#!/usr/bin/env python3

from __future__ import annotations

import logging
import sys

from dbus.mainloop.glib import DBusGMainLoop
from gi.repository import GLib

from dbus_solis.config import load_config
from dbus_solis.driver import SolisDriver


def main() -> int:
    try:
        config = load_config()
    except (FileNotFoundError, ValueError, KeyError) as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 2

    logging.basicConfig(
        level=getattr(logging, config.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    log = logging.getLogger("dbus-solis")

    DBusGMainLoop(set_as_default=True)

    try:
        driver = SolisDriver(config)
    except Exception:
        log.exception("Unable to initialize driver")
        return 1

    driver.start()
    log.info("dbus-solis started")

    loop = GLib.MainLoop()

    try:
        loop.run()
    except KeyboardInterrupt:
        log.info("Stopping dbus-solis")
    finally:
        driver.stop()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())