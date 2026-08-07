from __future__ import annotations

import dbus

from .config import AppConfig
from .constants import (
    ACTIVE_INPUT_GRID,
    PRODUCT_ID_VIRTUAL,
    STATE_EXTERNAL_CONTROL,
    VEBUS_SERVICE_NAME,
)
from .dbus_helpers import (
    format_amps,
    format_hz,
    format_percent,
    format_volts,
    format_watts,
)
from .models import VebusData
from .vedbus_loader import VeDbusService


class VebusService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._bus = dbus.SystemBus(private=True)

        self.service = VeDbusService(
            VEBUS_SERVICE_NAME,
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
        config = self._config

        self._add_path("/Mgmt/ProcessName", "dbus_solis.py")
        self._add_path("/Mgmt/ProcessVersion", "0.1.0")
        self._add_path("/Mgmt/Connection", "MQTT")

        self._add_path(
            "/DeviceInstance",
            config.devices.vebus,
        )
        self._add_path(
            "/ProductId",
            PRODUCT_ID_VIRTUAL,
        )
        self._add_path(
            "/ProductName",
            "Solis S6-EH2P Virtual Dual Inverter",
        )
        self._add_path(
            "/CustomName",
            "Solis Dual Inverter",
        )
        self._add_path(
            "/FirmwareVersion",
            "0.1.0",
        )
        self._add_path(
            "/HardwareVersion",
            "Virtual",
        )
        self._add_path(
            "/Serial",
            "SOLIS-VIRTUAL-VEBUS",
        )

        self._add_path("/Connected", 0)
        self._add_path("/UpdateIndex", 0)

        self._add_path("/State", STATE_EXTERNAL_CONTROL)
        self._add_path("/Mode", 3)
        self._add_path("/VebusError", 0)
        self._add_path("/Soc", 0.0, format_percent)

        self._add_path("/Ac/NumberOfPhases", 2)
        self._add_path("/Ac/NumberOfAcInputs", 1)

        self._add_path(
            "/Ac/ActiveIn/ActiveInput",
            ACTIVE_INPUT_GRID,
        )
        self._add_path(
            "/Ac/ActiveIn/CurrentLimit",
            100.0,
            format_amps,
        )
        self._add_path(
            "/Ac/ActiveIn/Connected",
            0,
        )

        self._add_path(
            "/Ac/ActiveIn/P",
            0.0,
            format_watts,
        )
        self._add_path(
            "/Ac/Out/P",
            0.0,
            format_watts,
        )

        for phase in ("L1", "L2"):
            self._add_path(
                f"/Ac/ActiveIn/{phase}/V",
                0.0,
                format_volts,
            )
            self._add_path(
                f"/Ac/ActiveIn/{phase}/I",
                0.0,
                format_amps,
            )
            self._add_path(
                f"/Ac/ActiveIn/{phase}/P",
                0.0,
                format_watts,
            )
            self._add_path(
                f"/Ac/ActiveIn/{phase}/F",
                60.0,
                format_hz,
            )

            self._add_path(
                f"/Ac/Out/{phase}/V",
                0.0,
                format_volts,
            )
            self._add_path(
                f"/Ac/Out/{phase}/I",
                0.0,
                format_amps,
            )
            self._add_path(
                f"/Ac/Out/{phase}/P",
                0.0,
                format_watts,
            )
            self._add_path(
                f"/Ac/Out/{phase}/F",
                60.0,
                format_hz,
            )

        self._add_path(
            "/Dc/0/Voltage",
            0.0,
            format_volts,
        )
        self._add_path(
            "/Dc/0/Current",
            0.0,
            format_amps,
        )
        self._add_path(
            "/Dc/0/Power",
            0.0,
            format_watts,
        )

        for alarm in (
            "GridLost",
            "HighDcVoltage",
            "LowBattery",
            "LowDcVoltage",
            "Overload",
            "HighTemperature",
            "OverTemperature",
            "Ripple",
            "TemperatureSensor",
            "PhaseRotation",
        ):
            self._add_path(
                f"/Alarms/{alarm}",
                0,
            )

    def set_connected(self, connected: bool) -> None:
        self.service["/Connected"] = int(connected)
        self._add_path( "/Bridge/LastUpdate", "never",)

    def update(
        self,
        data: VebusData,
        connected: bool,
    ) -> None:
        self.service["/Connected"] = int(connected)

        self.service["/State"] = data.state
        self.service["/Mode"] = data.mode
        self.service["/VebusError"] = data.vebus_error
        self.service["/Soc"] = data.soc

        self.service["/Dc/0/Voltage"] = data.dc.voltage
        self.service["/Dc/0/Current"] = data.dc.current
        self.service["/Dc/0/Power"] = data.dc.power

        self.service["/Ac/ActiveIn/ActiveInput"] = (
            data.active_input
        )
        
        grid_connected = (
            data.active_input != 240
            and (
                data.grid.l1.voltage > 50
                or data.grid.l2.voltage > 50
            )
        )

        self.service["/Ac/ActiveIn/Connected"] = int(
            grid_connected
        )
        self.service["/Alarms/GridLost"] = int(
             0 if grid_connected else 2

        )

        self.service["/Ac/ActiveIn/P"] = (
            data.grid.total_power
        )
        self.service["/Ac/Out/P"] = (
            data.out.total_power
        )

        self._update_ac_group(
            base="/Ac/ActiveIn",
            frequency=data.grid.frequency,
            l1=data.grid.l1,
            l2=data.grid.l2,
        )

        self._update_ac_group(
            base="/Ac/Out",
            frequency=data.out.frequency,
            l1=data.out.l1,
            l2=data.out.l2,
        )

        self.service["/UpdateIndex"] = (
            int(self.service["/UpdateIndex"]) + 1
        ) % 256
        self._add_path( "/Bridge/LastUpdate", "never",)

    def _update_ac_group(
        self,
        base: str,
        frequency: float,
        l1,
        l2,
    ) -> None:
        for phase_name, phase_data in (
            ("L1", l1),
            ("L2", l2),
        ):
            phase_base = f"{base}/{phase_name}"

            self.service[f"{phase_base}/V"] = (
                phase_data.voltage
            )
            self.service[f"{phase_base}/I"] = (
                phase_data.current
            )
            self.service[f"{phase_base}/P"] = (
                phase_data.power
            )
            self.service[f"{phase_base}/F"] = (
                frequency
            )