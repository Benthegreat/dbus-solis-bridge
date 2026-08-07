import json
from pathlib import Path

from dbus_solis.models import SystemData


def main():
    payload = Path("tests/sample_payload.json")

    data = json.loads(payload.read_text())

    system = SystemData.from_dict(data)

    print("Connection:", system.connected)

    print("SOC:", system.vebus.soc)

    print("Battery Voltage:", system.vebus.dc.voltage)

    print("Grid Power:", system.vebus.grid.total_power)

    print("Load Power:", system.vebus.out.total_power)

    print("PV Voltage:", system.mppt.pv.voltage)

    print("PV Yield:", system.mppt.yield_data.system)
    print("Battery SOH:", system.battery.soh)
    print("Battery Temp:", system.battery.temperature)
    print(
        "Battery Max Charge Current:",
        system.battery.max_charge_current,
    )

if __name__ == "__main__":
    main()