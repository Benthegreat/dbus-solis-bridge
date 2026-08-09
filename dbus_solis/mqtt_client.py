from __future__ import annotations

import json
import logging
from collections.abc import Callable
from typing import Any

import paho.mqtt.client as mqtt

from .config import MQTTConfig
from .models import SystemData


MessageCallback = Callable[[SystemData], None]


class MQTTClient:
    """
    MQTT subscriber backed by Eclipse Paho.

    Paho handles:
    - MQTT keepalive / PINGREQ / PINGRESP
    - reconnects
    - packet framing
    - SUBACK handling
    - network-loop management
    """

    def __init__(
        self,
        config: MQTTConfig,
        on_message: MessageCallback,
    ) -> None:
        self._config = config
        self._on_message_callback = on_message
        self._log = logging.getLogger("dbus-solis.mqtt")

        client_kwargs = {
            "client_id": self._config.client_id,
            "protocol": mqtt.MQTTv311,
        }

        # Paho 2.x requires selecting the callback API version.
        # This fallback also keeps the code usable with Paho 1.x.
        if hasattr(mqtt, "CallbackAPIVersion"):
            client_kwargs["callback_api_version"] = (
                mqtt.CallbackAPIVersion.VERSION1
            )

        self._client = mqtt.Client(**client_kwargs)

        if self._config.username:
            self._client.username_pw_set(
                username=self._config.username,
                password=self._config.password or None,
            )

        if self._config.tls:
            self._client.tls_set()

            if self._config.tls_insecure:
                self._client.tls_insecure_set(True)

        self._client.reconnect_delay_set(
            min_delay=1,
            max_delay=30,
        )

        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message

        if hasattr(self._client, "on_connect_fail"):
            self._client.on_connect_fail = self._on_connect_fail

        self._started = False

    def start(self) -> None:
        if self._started:
            return

        self._log.info(
            "Connecting to MQTT broker %s:%s",
            self._config.host,
            self._config.port,
        )

        self._client.connect_async(
            host=self._config.host,
            port=self._config.port,
            keepalive=self._config.keepalive,
        )

        self._client.loop_start()
        self._started = True

    def stop(self) -> None:
        if not self._started:
            return

        try:
            self._client.disconnect()
        finally:
            self._client.loop_stop()
            self._started = False

    def _on_connect(
        self,
        client,
        userdata,
        flags,
        rc,
    ) -> None:
        result = int(rc)

        if result != 0:
            self._log.warning(
                "MQTT connection rejected: rc=%s",
                rc,
            )
            return

        result, mid = client.subscribe(
            self._config.topic,
            qos=0,
        )

        if result != mqtt.MQTT_ERR_SUCCESS:
            self._log.error(
                "Unable to subscribe to MQTT topic %s: rc=%s",
                self._config.topic,
                result,
            )
            return

        self._log.info(
            "Subscribed to MQTT topic %s",
            self._config.topic,
        )

    def _on_disconnect(
        self,
        client,
        userdata,
        rc,
    ) -> None:
        if int(rc) == 0:
            self._log.info("MQTT disconnected")
        else:
            self._log.warning(
                "MQTT connection lost: rc=%s; reconnecting",
                rc,
            )

    def _on_connect_fail(
        self,
        client,
        userdata,
    ) -> None:
        self._log.warning(
            "MQTT connection attempt failed"
        )

    def _on_message(
        self,
        client,
        userdata,
        message,
    ) -> None:
        if message.topic != self._config.topic:
            return

        try:
            decoded = message.payload.decode("utf-8")

            parsed: Any = json.loads(decoded)

            system_data = SystemData.from_dict(parsed)

        except (
            UnicodeDecodeError,
            json.JSONDecodeError,
            ValueError,
            TypeError,
        ) as exc:
            self._log.warning(
                "Rejected MQTT payload: %s",
                exc,
            )
            return

        try:
            self._on_message_callback(system_data)

        except Exception:
            self._log.exception(
                "Unhandled exception processing MQTT telemetry"
            )