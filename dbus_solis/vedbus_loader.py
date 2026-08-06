from __future__ import annotations

import os
import sys


VELIB_PATHS = (
    "/opt/victronenergy/dbus-systemcalc-py/ext/velib_python",
    "/opt/victronenergy/velib_python",
    "/data/dbus-solis/ext/velib_python",
)


for candidate in VELIB_PATHS:
    if os.path.exists(os.path.join(candidate, "vedbus.py")):
        sys.path.insert(0, candidate)
        break
else:
    raise RuntimeError(
        "Could not locate vedbus.py. "
        "Expected Victron velib_python on Venus OS."
    )


from vedbus import VeDbusService  # type: ignore  # noqa: E402


__all__ = ["VeDbusService"]