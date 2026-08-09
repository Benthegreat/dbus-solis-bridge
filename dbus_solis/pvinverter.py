from __future__ import annotations

import dbus

from .config import AppConfig
from .dbus_helpers import format_watts
from .models import AcPvData
from .vedbus_loader import VeDbusService


PVINVERTER_SERVICE_NAME = "com.victronenergy.pvinverter.solis_ac"


class PvInverterService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._bus = dbus.SystemBus(private=True)

        self.service = VeDbusService(
            PVINVERTER_SERVICE_NAME,
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

        # Temporary unique instance until we add it to config.py.
        self._add_path(
            "/DeviceInstance",
            self._config.devices.pvinverter,
        )

        self._add_path("/ProductId", 0xFFFF)
        self._add_path(
            "/ProductName",
            "Solis AC-Coupled PV",
        )
        self._add_path(
            "/CustomName",
            "Solis AC Coupled Solar",
        )
        self._add_path("/FirmwareVersion", "0.3.0-dev")
        self._add_path("/HardwareVersion", "Virtual")
        self._add_path("/Serial", "SOLIS-AC-PV")

        self._add_path("/Connected", 0)
        self._add_path("/UpdateIndex", 0)
        self._add_path("/Bridge/LastUpdate", "never")

        # Victron:
        # 0 = AC input 1
        # 1 = AC output
        # 2 = AC input 2
        self._add_path("/Position", 0)

        self._add_path("/StatusCode", 7)
        self._add_path("/ErrorCode", 0)

        self._add_path("/Ac/Power", 0.0, format_watts)
        self._add_path("/Ac/L1/Voltage", 0.0)
        self._add_path("/Ac/L2/Voltage", 0.0)

        self._add_path("/Ac/L1/Power", 0.0, format_watts)
        self._add_path("/Ac/L2/Power", 0.0, format_watts)
        # Total produced AC energy.
        self._add_path("/Ac/Energy/Forward", 0.0)

        # Useful generation counters for debugging/UI.
        self._add_path("/Yield/Power", 0.0, format_watts)
        self._add_path("/Yield/User", 0.0)
        self._add_path("/Yield/System", 0.0)

    def set_connected(self, connected: bool) -> None:
        self.service["/Connected"] = int(connected)

    def update(
        self,
        data: AcPvData,
        connected: bool,
        last_update: str,
    ) -> None:
        is_connected = connected and data.connected

        self.service["/Connected"] = int(is_connected)
        self.service["/Position"] = data.position

        self.service["/Ac/L1/Voltage"] = data.l1_voltage
        self.service["/Ac/L2/Voltage"] = data.l2_voltage

        self.service["/Ac/L1/Power"] = data.l1_power
        self.service["/Ac/L2/Power"] = data.l2_power
        total_power = data.l1_power + data.l2_power
        self.service["/Ac/Power"] = total_power
        self.service["/Ac/Energy/Forward"] = data.energy_total

        self.service["/Yield/Power"] = total_power
        self.service["/Yield/User"] = data.energy_today
        self.service["/Yield/System"] = data.energy_total

        self.service["/StatusCode"] = (
            7 if is_connected else 8
        )

        self.service["/Bridge/LastUpdate"] = last_update

        self.service["/UpdateIndex"] = (
            int(self.service["/UpdateIndex"]) + 1
        ) % 256