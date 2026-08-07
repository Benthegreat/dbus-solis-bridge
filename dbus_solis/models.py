from __future__ import annotations

from dataclasses import dataclass
from typing import Any


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


@dataclass(frozen=True)
class PhaseData:
    voltage: float
    current: float
    power: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PhaseData":
        return cls(
            voltage=_to_float(data.get("voltage")),
            current=_to_float(data.get("current")),
            power=_to_float(data.get("power")),
        )


@dataclass(frozen=True)
class DcData:
    voltage: float
    current: float
    power: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "DcData":
        return cls(
            voltage=_to_float(data.get("voltage")),
            current=_to_float(data.get("current")),
            power=_to_float(data.get("power")),
        )


@dataclass(frozen=True)
class AcData:
    frequency: float
    total_power: float
    l1: PhaseData
    l2: PhaseData

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "AcData":
        l1 = PhaseData.from_dict(data.get("l1", {}))
        l2 = PhaseData.from_dict(data.get("l2", {}))

        return cls(
            frequency=_to_float(data.get("frequency"), 60.0),
            total_power=_to_float(
                data.get("total_power"),
                l1.power + l2.power,
            ),
            l1=l1,
            l2=l2,
        )


@dataclass(frozen=True)
class VebusData:
    state: int
    mode: int
    vebus_error: int
    soc: float
    active_input: int
    dc: DcData
    grid: AcData
    out: AcData

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "VebusData":
        return cls(
            state=_to_int(data.get("state"), 252),
            mode=_to_int(data.get("mode"), 3),
            vebus_error=_to_int(data.get("vebus_error")),
            soc=_to_float(data.get("soc")),
            active_input=_to_int(data.get("active_input")),
            dc=DcData.from_dict(data.get("dc", {})),
            grid=AcData.from_dict(data.get("grid", {})),
            out=AcData.from_dict(data.get("out", {})),
        )


@dataclass(frozen=True)
class PvData:
    voltage: float
    current: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "PvData":
        return cls(
            voltage=_to_float(data.get("voltage")),
            current=_to_float(data.get("current")),
        )


@dataclass(frozen=True)
class YieldData:
    power: float
    system: float

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "YieldData":
        return cls(
            power=_to_float(data.get("power")),
            system=_to_float(data.get("system")),
        )


@dataclass(frozen=True)
class MpptData:
    state: int
    error_code: int
    mode: int
    pv: PvData
    yield_data: YieldData
    dc: DcData

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "MpptData":
        return cls(
            state=_to_int(data.get("state")),
            error_code=_to_int(data.get("error_code")),
            mode=_to_int(data.get("mode"), 1),
            pv=PvData.from_dict(data.get("pv", {})),
            yield_data=YieldData.from_dict(data.get("yield", {})),
            dc=DcData.from_dict(data.get("dc", {})),
        )


@dataclass(frozen=True)
class SystemData:
    timestamp: str
    connected: bool
    vebus: VebusData
    mppt: MpptData

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "SystemData":
        if not isinstance(data, dict):
            raise ValueError("MQTT payload must be a JSON object")

        return cls(
            timestamp=str(data.get("timestamp", "")),
            connected=bool(data.get("connected", True)),
            vebus=VebusData.from_dict(data.get("vebus", {})),
            mppt=MpptData.from_dict(data.get("mppt", {})),
        )