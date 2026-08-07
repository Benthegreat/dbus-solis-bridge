from __future__ import annotations

import dbus

from .config import AppConfig
from .dbus_helpers import (
    format_amps,
    format_hz,
    format_volts,
    format_watts,
)
from .models import AcData
from .vedbus_loader import VeDbusService


GRID_SERVICE_NAME = "com.victronenergy.grid.solis"


class GridService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._bus = dbus.SystemBus(private=True)

        self.service = VeDbusService(
            GRID_SERVICE_NAME,
            bus=self._bus,
            register=False,
        )

        self._create_paths()
        self.service.register()

    def _add_path(
        self,
        path: str,
        value,
        formatter=None,
    ) -> None:
        self.service.add_path(
            path,
            value,
            writeable=False,
            gettextcallback=formatter,
        )

    def _create_paths(self) -> None:
        self._add_path("/Mgmt/ProcessName", "dbus_solis.py")
        self._add_path("/Mgmt/ProcessVersion", "0.3.0-dev")
        self._add_path("/Mgmt/Connection", "MQTT")

        self._add_path(
            "/DeviceInstance",
            self._config.devices.grid,
        )

        self._add_path("/ProductId", 0xFFFF)
        self._add_path("/ProductName", "Solis Virtual Grid Meter")
        self._add_path("/CustomName", "Solis Grid Meter")
        self._add_path("/FirmwareVersion", "0.3.0-dev")
        self._add_path("/HardwareVersion", "Virtual")
        self._add_path("/Serial", "SOLIS-VIRTUAL-GRID")

        self._add_path("/Connected", 0)
        self._add_path("/UpdateIndex", 0)
        self._add_path("/Bridge/LastUpdate", "never")

        # Position 0 = grid meter.
        self._add_path("/Position", 0)

        self._add_path("/Ac/Power", 0.0, format_watts)

        for phase in ("L1", "L2"):
            self._add_path(
                f"/Ac/{phase}/Voltage",
                0.0,
                format_volts,
            )
            self._add_path(
                f"/Ac/{phase}/Current",
                0.0,
                format_amps,
            )
            self._add_path(
                f"/Ac/{phase}/Power",
                0.0,
                format_watts,
            )
            self._add_path(
                f"/Ac/{phase}/Frequency",
                60.0,
                format_hz,
            )

    def set_connected(self, connected: bool) -> None:
        self.service["/Connected"] = int(connected)

    def update(
        self,
        data: AcData,
        connected: bool,
        last_update: str,
    ) -> None:
        self.service["/Connected"] = int(connected)
        self.service["/Ac/Power"] = data.total_power

        for name, phase in (
            ("L1", data.l1),
            ("L2", data.l2),
        ):
            base = f"/Ac/{name}"

            self.service[f"{base}/Voltage"] = phase.voltage
            self.service[f"{base}/Current"] = phase.current
            self.service[f"{base}/Power"] = phase.power
            self.service[f"{base}/Frequency"] = data.frequency

        self.service["/Bridge/LastUpdate"] = last_update

        self.service["/UpdateIndex"] = (
            int(self.service["/UpdateIndex"]) + 1
        ) % 256