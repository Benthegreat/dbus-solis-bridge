from __future__ import annotations

from typing import Any


def format_watts(_path: str, value: Any) -> str:
    try:
        return f"{float(value):.0f} W"
    except (TypeError, ValueError):
        return "---"


def format_volts(_path: str, value: Any) -> str:
    try:
        return f"{float(value):.1f} V"
    except (TypeError, ValueError):
        return "---"


def format_amps(_path: str, value: Any) -> str:
    try:
        return f"{float(value):.1f} A"
    except (TypeError, ValueError):
        return "---"


def format_hz(_path: str, value: Any) -> str:
    try:
        return f"{float(value):.2f} Hz"
    except (TypeError, ValueError):
        return "---"


def format_percent(_path: str, value: Any) -> str:
    try:
        return f"{float(value):.1f} %"
    except (TypeError, ValueError):
        return "---"


def format_kwh(_path: str, value: Any) -> str:
    try:
        return f"{float(value):.2f} kWh"
    except (TypeError, ValueError):
        return "---"