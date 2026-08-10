dbus-solis-bridge

Expose a Solis Hybrid inverter as native Victron GX D-Bus services using MQTT telemetry.

dbus-solis-bridge allows a Solis S6 Hybrid inverter to appear as native Victron devices on Cerbo GX / Venus OS.

Instead of polling Modbus directly from the Cerbo, telemetry is normalized by Home Assistant and published via MQTT. The bridge then creates native D-Bus services that integrate with:

GX Device List
VRM Portal
Remote Console
ESS
Venus OS logging
Energy Flow diagrams
Features
VE.Bus Inverter/Charger
Native com.victronenergy.vebus
Grid input
AC output
DC bus
Energy counters
VE.Bus state/mode
ESS compatible
Battery Monitor

Native com.victronenergy.battery

Publishes

SOC
SOH
Voltage
Current
Power
Temperature
Charge current limits
Discharge current limits

Supports BMS-derived values such as Lynk II.

Grid Meter

Native com.victronenergy.grid

Provides

L1/L2 voltages
L1/L2 currents
L1/L2 power
Grid frequency
Total import/export power
Lifetime import/export energy
Solar Charger

Native com.victronenergy.solarcharger

Supports

PV voltage
PV current
PV power
Yield today
Lifetime yield
MPPT state
AC Coupled PV Inverter

Native com.victronenergy.pvinverter

Supports

AC Coupled position
Per-phase voltage
Per-phase power
Total power
Daily energy
Lifetime energy

Compatible with Solis AC Coupled mode using the GEN/Smart Port.

MQTT Driven

The bridge consumes a single normalized MQTT payload.

Advantages

inverter independent
Home Assistant friendly
multiple data sources may be combined
easy debugging
Architecture
Solis Inverter
        │
        │ Modbus
        ▼
 Home Assistant
        │
 MQTT JSON
        ▼
dbus-solis-bridge
        │
 D-Bus Services
        ▼
 Venus OS
        │
        ▼
 VRM
Current Services

The bridge creates:

com.victronenergy.vebus.solis

com.victronenergy.battery.solis

com.victronenergy.grid.solis

com.victronenergy.solarcharger.solis

com.victronenergy.pvinverter.solis_ac
Installation

Copy the project to

/data/dbus-solis

Copy

config.example.json

to

config.json

Edit:

MQTT broker
credentials
device instances

Run

./install.sh
Persistent Startup (Venus OS)

Venus OS recreates /service during boot.

To ensure automatic startup after every reboot, add the following to:

/data/rc.local
#!/bin/sh

if [ ! -L /service/dbus-solis ]; then
    ln -s /data/dbus-solis/service /service/dbus-solis
fi

exit 0

Make executable:

chmod +x /data/rc.local

After this, the bridge starts automatically after every reboot.

MQTT Payload

The bridge expects one normalized JSON payload.

Top level objects:

battery

grid

vebus

mppt

ac_pv

A complete example is included in

tests/sample_payload.json
Sign Conventions

Battery

Value	Meaning
Positive	Charging
Negative	Discharging

VE.Bus DC

Value	Meaning
Positive	Rectifying (AC→DC)
Negative	Inverting (DC→AC)

Grid

Value	Meaning
Positive	Import
Negative	Export

PV Inverter

Value	Meaning
Positive	Producing
Negative	Idle / measurement noise
Development

Run locally

python dbus_solis.py

Compile

python -m compileall dbus_solis dbus_solis.py

Install

./install.sh
Tested Hardware
Cerbo GX
Venus OS Large
Solis S6 EH2P Hybrid
Solis Modbus Integration for Home Assistant
Lynk II BMS
Pytes batteries (via Lynk II)
MQTT (FlashMQ)
Roadmap
Completed
✅ VE.Bus
✅ Battery Service
✅ Grid Meter
✅ MPPT
✅ AC Coupled PV
✅ MQTT queue processing
✅ Watchdog
✅ Automatic reconnect
✅ Persistent autostart
✅ Energy counters
✅ Configurable device instances
Planned
Better diagnostics
MQTT schema versioning
Installation wizard
GitHub Actions unit tests
VRM validation on long-term operation
License

MIT License