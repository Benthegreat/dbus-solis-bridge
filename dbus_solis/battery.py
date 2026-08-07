from __future__ import annotations

import dbus

from .config import AppConfig
from .dbus_helpers import (
    format_amps,
    format_percent,
    format_volts,
    format_watts,
)
from .vedbus_loader import VeDbusService


BATTERY_SERVICE_NAME = "com.victronenergy.battery.solis"


class BatteryService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._bus = dbus.SystemBus(private=True)

        self.service = VeDbusService(
            BATTERY_SERVICE_NAME,
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
        self._add_path("/Mgmt/ProcessVersion", "0.2.0-dev")
        self._add_path("/Mgmt/Connection", "MQTT")

        self._add_path(
            "/DeviceInstance",
            self._config.devices.battery,
        )
        self._add_path("/ProductId", 0xFFFF)
        self._add_path("/ProductName", "Solis Virtual Battery")
        self._add_path("/CustomName", "Solis Battery")
        self._add_path("/FirmwareVersion", "0.2.0-dev")
        self._add_path("/HardwareVersion", "Virtual")
        self._add_path("/Serial", "SOLIS-VIRTUAL-BATTERY")

        self._add_path("/Connected", 0)
        self._add_path("/UpdateIndex", 0)
        self._add_path("/Bridge/LastUpdate", "never")

        self._add_path("/Soc", 0.0, format_percent)
        self._add_path("/Soh", 0.0, format_percent)

        self._add_path("/Dc/0/Voltage", 0.0, format_volts)
        self._add_path("/Dc/0/Current", 0.0, format_amps)
        self._add_path("/Dc/0/Power", 0.0, format_watts)

        self._add_path("/Dc/0/Temperature", 0.0)

        self._add_path("/Info/MaxChargeCurrent", 0.0, format_amps)
        self._add_path("/Info/MaxDischargeCurrent", 0.0, format_amps)

        for alarm in (
            "LowVoltage",
            "HighVoltage",
            "LowSoc",
            "HighChargeCurrent",
            "HighDischargeCurrent",
            "HighTemperature",
            "LowTemperature",
        ):
            self._add_path(f"/Alarms/{alarm}", 0)

    def set_connected(self, connected: bool) -> None:
        self.service["/Connected"] = int(connected)

    def update(
        self,
        *,
        soc: float,
        soh: float,
        voltage: float,
        current: float,
        power: float,
        temperature: float,
        max_charge_current: float,
        max_discharge_current: float,
        connected: bool,
        last_update: str,
    ) -> None:
        self.service["/Connected"] = int(connected)
        self.service["/Soc"] = soc
        self.service["/Soh"] = soh

        self.service["/Dc/0/Voltage"] = voltage
        self.service["/Dc/0/Current"] = current
        self.service["/Dc/0/Power"] = power
        self.service["/Dc/0/Temperature"] = temperature

        self.service["/Info/MaxChargeCurrent"] = max_charge_current
        self.service["/Info/MaxDischargeCurrent"] = max_discharge_current

        self.service["/Bridge/LastUpdate"] = last_update

        self.service["/UpdateIndex"] = (
            int(self.service["/UpdateIndex"]) + 1
        ) % 256