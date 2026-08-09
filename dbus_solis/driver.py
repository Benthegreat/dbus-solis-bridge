from __future__ import annotations

import logging
import queue
import time

from gi.repository import GLib

from .battery import BatteryService
from .config import AppConfig
from .grid import GridService
from .models import DcData, SystemData, VebusData
from .mppt import MpptService
from .mqtt_client import MQTTClient
from .vebus import VebusService


class SolisDriver:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._log = logging.getLogger("dbus-solis")

        self._payload_queue: queue.Queue[SystemData] = queue.Queue(
            maxsize=5
        )

        self._last_update = 0.0

        self._vebus = VebusService(config)
        self._mppt = MpptService(config)
        self._battery = BatteryService(config)
        self._grid = GridService(config)

        self._mqtt = MQTTClient(
            config=config.mqtt,
            on_message=self._enqueue_message,
        )

    def start(self) -> None:
        self._mqtt.start()

        # Process MQTT data on the GLib / D-Bus thread.
        GLib.timeout_add(
            200,
            self._process_queue,
        )

        # Mark devices disconnected when telemetry goes stale.
        GLib.timeout_add_seconds(
            1,
            self._watchdog,
        )

        self._log.info("dbus-solis driver started")

    def stop(self) -> None:
        self._mqtt.stop()

        self._vebus.set_connected(False)
        self._mppt.set_connected(False)
        self._battery.set_connected(False)
        self._grid.set_connected(False)

        self._log.info("dbus-solis driver stopped")

    def _enqueue_message(
        self,
        data: SystemData,
    ) -> None:
        """
        Called from the MQTT background thread.

        Keep only recent telemetry if updates arrive faster than
        the GLib loop processes them.
        """

        while self._payload_queue.full():
            try:
                self._payload_queue.get_nowait()
            except queue.Empty:
                break

        try:
            self._payload_queue.put_nowait(data)
        except queue.Full:
            self._log.warning(
                "Dropped MQTT update because queue is full"
            )

    def _process_queue(self) -> bool:
        """
        Runs on the GLib main loop.

        Drain the queue and apply only the newest telemetry.
        """

        newest: SystemData | None = None

        while True:
            try:
                newest = self._payload_queue.get_nowait()
            except queue.Empty:
                break

        if newest is None:
            return True

        try:
            # MQTT is the normalized/canonical data source. Any Solis-specific
            # sign conversion should happen in the publisher (Home Assistant),
            # so all D-Bus services consume the same power-flow convention.
            self._vebus.update(
                data=VebusData(
                    state=newest.vebus.state,
                    mode=newest.vebus.mode,
                    vebus_error=newest.vebus.vebus_error,
                    soc=newest.battery.soc,
                    active_input=newest.vebus.active_input,
                    dc=DcData(
                        voltage=newest.battery.voltage,
                        current=newest.battery.current,
                        power=newest.battery.power,
                    ),
                    grid=newest.vebus.grid,
                    out=newest.vebus.out,
                    energy=newest.vebus.energy,
                ),
                connected=newest.connected,
                last_update=newest.timestamp,
            )

            self._mppt.update(
                data=newest.mppt,
                connected=newest.connected,
                last_update=newest.timestamp,
            )

            self._battery.update(
                soc=newest.battery.soc,
                soh=newest.battery.soh,
                voltage=newest.battery.voltage,
                current=newest.battery.current,
                power=newest.battery.power,
                temperature=newest.battery.temperature,
                max_charge_current=newest.battery.max_charge_current,
                max_discharge_current=newest.battery.max_discharge_current,
                connected=newest.connected,
                last_update=newest.timestamp,
            )

            self._grid.update(
                data=newest.grid,
                connected=newest.connected,
                last_update=newest.timestamp,
            )

            self._last_update = time.monotonic()

            self._log.debug(
                "Applied MQTT telemetry to D-Bus"
            )

        except Exception:
            self._log.exception(
                "Failed to apply MQTT telemetry to D-Bus"
            )

        return True

    def _watchdog(self) -> bool:
        if self._last_update == 0:
            stale = True
        else:
            age = time.monotonic() - self._last_update
            stale = age > self._config.stale_timeout

        if stale:
            self._vebus.set_connected(False)
            self._mppt.set_connected(False)
            self._battery.set_connected(False)
            self._grid.set_connected(False)

        return True