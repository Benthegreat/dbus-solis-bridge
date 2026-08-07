from __future__ import annotations

import dbus

from .config import AppConfig
from .constants import MPPT_SERVICE_NAME, PRODUCT_ID_VIRTUAL
from .dbus_helpers import (
    format_amps,
    format_kwh,
    format_volts,
    format_watts,
)
from .models import MpptData
from .vedbus_loader import VeDbusService


class MpptService:
    def __init__(self, config: AppConfig) -> None:
        self._config = config
        self._bus = dbus.SystemBus(private=True)

        self.service = VeDbusService(
            MPPT_SERVICE_NAME,
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
            config.devices.mppt,
        )
        self._add_path(
            "/ProductId",
            PRODUCT_ID_VIRTUAL,
        )
        self._add_path(
            "/ProductName",
            "Solis Virtual External MPPT",
        )
        self._add_path(
            "/CustomName",
            "Solis External MPPT",
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
            "SOLIS-VIRTUAL-MPPT",
        )

        self._add_path("/Connected", 0)
        self._add_path("/UpdateIndex", 0)

        self._add_path("/State", 0)
        self._add_path("/ErrorCode", 0)
        self._add_path("/Mode", 1)

        self._add_path(
            "/Pv/V",
            0.0,
            format_volts,
        )
        self._add_path(
            "/Pv/I",
            0.0,
            format_amps,
        )

        self._add_path(
            "/Yield/Power",
            0.0,
            format_watts,
        )
        self._add_path(
            "/Yield/System",
            0.0,
            format_kwh,
        )
        self._add_path(
            "/Yield/User",
            0.0,
            format_kwh,
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
        self._add_path(
            "/Bridge/LastUpdate",
            "never",
        )

    def set_connected(self, connected: bool) -> None:
        self.service["/Connected"] = int(connected)

    def update(
        self,
        data: MpptData,
        connected: bool,
        last_update: str,
        
    ) -> None:
        self.service["/Connected"] = int(connected)

        self.service["/State"] = data.state
        self.service["/ErrorCode"] = data.error_code
        self.service["/Mode"] = data.mode
        self.service["/Pv/V"] = data.pv.voltage
        self.service["/Pv/I"] = data.pv.current
        self.service["/Bridge/LastUpdate"] = last_update
        self.service["/Yield/Power"] = (
            data.yield_data.power
        )
        self.service["/Yield/System"] = (
            data.yield_data.system
        )
        self.service["/Yield/User"] = (
            data.yield_data.system
        )

        self.service["/Dc/0/Voltage"] = (
            data.dc.voltage
        )
        self.service["/Dc/0/Current"] = (
            data.dc.current
        )
        self.service["/Dc/0/Power"] = (
            data.dc.power
        )

        self.service["/UpdateIndex"] = (
            int(self.service["/UpdateIndex"]) + 1
        ) % 256