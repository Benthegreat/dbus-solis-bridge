from __future__ import annotations

import logging
import threading
import time

from gi.repository import GLib

from .config import AppConfig
from .models import SystemData
from .mppt import MpptService
from .mqtt_client import MQTTClient
from .vebus import VebusService


class SolisDriver:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._log = logging.getLogger("dbus-solis")
        self._lock = threading.Lock()
        self._last_update = 0.0

        self._vebus = VebusService(config)
        self._mppt = MpptService(config)

        self._mqtt = MQTTClient(
            config=config.mqtt,
            on_message=self._handle_message,
        )

    def start(self) -> None:
        self._mqtt.start()

        GLib.timeout_add_seconds(
            1,
            self._watchdog,
        )

        self._log.info("dbus-solis driver started")

    def stop(self) -> None:
        self._mqtt.stop()

        with self._lock:
            self._vebus.set_connected(False)
            self._mppt.set_connected(False)

        self._log.info("dbus-solis driver stopped")

    def _handle_message(
        self,
        data: SystemData,
    ) -> None:
        with self._lock:
            self._vebus.update(
                data=data.vebus,
                connected=data.connected,
            )

            self._mppt.update(
                data=data.mppt,
                connected=data.connected,
            )

            self._last_update = time.monotonic()

        self._log.debug("Updated D-Bus services from MQTT")

    def _watchdog(self) -> bool:
        with self._lock:
            if self._last_update == 0:
                stale = True
            else:
                age = time.monotonic() - self._last_update
                stale = (
                    age
                    > self._config.stale_timeout
                )

            if stale:
                self._vebus.set_connected(False)
                self._mppt.set_connected(False)

        return True
        