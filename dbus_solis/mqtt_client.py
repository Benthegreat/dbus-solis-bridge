from __future__ import annotations

import json
import logging
import socket
import ssl
import threading
import time
from collections.abc import Callable
from typing import Any

from .config import MQTTConfig
from .models import SystemData


MessageCallback = Callable[[SystemData], None]


class MQTTClient:
    """
    Minimal MQTT 3.1.1 client using only the Python standard library.

    This avoids depending on paho-mqtt being installed on Venus OS.
    """

    def __init__(
        self,
        config: MQTTConfig,
        on_message: MessageCallback,
    ) -> None:
        self._config = config
        self._on_message = on_message
        self._log = logging.getLogger("dbus-solis.mqtt")

        self._stop_event = threading.Event()
        self._thread: threading.Thread | None = None
        self._socket: socket.socket | None = None
        self._packet_id = 1

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._run,
            name="dbus-solis-mqtt",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stop_event.set()

        if self._socket is not None:
            try:
                self._socket.close()
            except OSError:
                pass

        if self._thread is not None:
            self._thread.join(timeout=2)

    @staticmethod
    def _pack_utf8(value: str) -> bytes:
        encoded = value.encode("utf-8")
        return len(encoded).to_bytes(2, "big") + encoded

    @staticmethod
    def _encode_remaining_length(length: int) -> bytes:
        encoded = bytearray()

        while True:
            digit = length % 128
            length //= 128

            if length > 0:
                digit |= 0x80

            encoded.append(digit)

            if length == 0:
                return bytes(encoded)

    @staticmethod
    def _read_exact(
        sock: socket.socket,
        count: int,
    ) -> bytes:
        data = bytearray()

        while len(data) < count:
            chunk = sock.recv(count - len(data))

            if not chunk:
                raise ConnectionError("MQTT connection closed")

            data.extend(chunk)

        return bytes(data)

    def _read_packet(
        self,
        sock: socket.socket,
    ) -> tuple[int, bytes]:
        first_byte = self._read_exact(sock, 1)[0]

        multiplier = 1
        remaining_length = 0

        while True:
            digit = self._read_exact(sock, 1)[0]
            remaining_length += (digit & 127) * multiplier

            if not digit & 128:
                break

            multiplier *= 128

            if multiplier > 128 * 128 * 128:
                raise ValueError("Invalid MQTT remaining length")

        body = self._read_exact(sock, remaining_length)
        return first_byte, body

    def _build_connect_packet(self) -> bytes:
        variable_header = self._pack_utf8("MQTT")
        variable_header += bytes([4])

        connect_flags = 0x02
        payload = self._pack_utf8(self._config.client_id)

        if self._config.username:
            connect_flags |= 0x80
            payload += self._pack_utf8(self._config.username)

        if self._config.password:
            connect_flags |= 0x40
            payload += self._pack_utf8(self._config.password)

        variable_header += bytes([connect_flags])
        variable_header += self._config.keepalive.to_bytes(
            2,
            "big",
        )

        remaining = variable_header + payload

        return (
            bytes([0x10])
            + self._encode_remaining_length(len(remaining))
            + remaining
        )

    def _build_subscribe_packet(self) -> bytes:
        packet_id = self._packet_id
        self._packet_id += 1

        if self._packet_id > 65535:
            self._packet_id = 1

        payload = self._pack_utf8(self._config.topic)
        payload += bytes([0])

        body = packet_id.to_bytes(2, "big") + payload

        return (
            bytes([0x82])
            + self._encode_remaining_length(len(body))
            + body
        )

    def _open_socket(self) -> socket.socket:
        sock = socket.create_connection(
            (
                self._config.host,
                self._config.port,
            ),
            timeout=10,
        )

        sock.settimeout(5)

        if self._config.tls:
            context = ssl.create_default_context()

            if self._config.tls_insecure:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE

            sock = context.wrap_socket(
                sock,
                server_hostname=self._config.host,
            )

        return sock

    def _handle_publish(self, body: bytes) -> None:
        if len(body) < 2:
            raise ValueError("Malformed MQTT PUBLISH packet")

        topic_length = int.from_bytes(body[:2], "big")
        payload_start = 2 + topic_length

        if len(body) < payload_start:
            raise ValueError("Malformed MQTT topic length")

        raw_payload = body[payload_start:]
        parsed: Any = json.loads(
            raw_payload.decode("utf-8")
        )

        system_data = SystemData.from_dict(parsed)
        self._on_message(system_data)

    def _run_session(self) -> None:
        sock = self._open_socket()
        self._socket = sock

        self._log.info(
            "Connecting to MQTT broker %s:%s",
            self._config.host,
            self._config.port,
        )

        sock.sendall(self._build_connect_packet())

        packet_type, body = self._read_packet(sock)

        if packet_type >> 4 != 2:
            raise ConnectionError(
                "Expected MQTT CONNACK packet"
            )

        if len(body) < 2:
            raise ConnectionError(
                "Malformed MQTT CONNACK packet"
            )

        return_code = body[1]

        if return_code != 0:
            raise ConnectionError(
                f"MQTT connection rejected, code={return_code}"
            )

        sock.sendall(self._build_subscribe_packet())

        self._log.info(
            "Subscribed to MQTT topic %s",
            self._config.topic,
        )

        # MQTT keepalive is based on client transmit activity, not receive
        # activity. Incoming telemetry does not satisfy the broker keepalive.
        last_tx = time.monotonic()
        ping_sent_at: float | None = None

        while not self._stop_event.is_set():
            try:
                packet_type, body = self._read_packet(sock)
                packet_kind = packet_type >> 4

                if packet_kind == 3:
                    self._handle_publish(body)

                elif packet_kind == 13:
                    # PINGRESP
                    ping_sent_at = None

            except socket.timeout:
                # A timeout is only an opportunity to run the keepalive check.
                # Frequent incoming publishes may prevent socket.timeout from
                # occurring, so the same check also runs after every packet.
                pass

            now = time.monotonic()

            if (
                ping_sent_at is not None
                and now - ping_sent_at >= self._config.keepalive
            ):
                raise TimeoutError("MQTT PINGRESP timeout")

            if (
                ping_sent_at is None
                and now - last_tx >= self._config.keepalive / 2
            ):
                sock.sendall(b"\xC0\x00")
                last_tx = now
                ping_sent_at = now

    def _run(self) -> None:
        reconnect_delay = 1

        while not self._stop_event.is_set():
            try:
                self._run_session()
                reconnect_delay = 1

            except Exception as exc:
                if not self._stop_event.is_set():
                    self._log.warning(
                        "MQTT connection failed: %s",
                        exc,
                    )

                    self._stop_event.wait(
                        reconnect_delay
                    )

                    reconnect_delay = min(
                        reconnect_delay * 2,
                        30,
                    )

            finally:
                if self._socket is not None:
                    try:
                        self._socket.close()
                    except OSError:
                        pass

                    self._socket = None