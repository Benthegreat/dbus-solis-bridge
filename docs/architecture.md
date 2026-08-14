# Architecture

dbus-solis-bridge converts normalized MQTT telemetry into native Victron GX D-Bus services.

---

# Data Flow

```text
          Solis Inverter
                 │
             Modbus TCP
                 │
                 ▼
        Home Assistant
                 │
      MQTT JSON Payload
                 │
                 ▼
      dbus-solis-bridge
                 │
        Native D-Bus Services
                 │
                 ▼
           Victron GX
                 │
                 ▼
              VRM Portal
```

---

# Services

The bridge creates

```
VE.Bus

Battery

Grid Meter

Solar Charger

PV Inverter
```

Each service behaves as if native Victron hardware were installed.

---

# Why MQTT?

MQTT separates

- data collection
- normalization
- presentation

This allows any telemetry source to be used.

Examples

- Home Assistant
- Node-RED
- Python
- Modbus
- REST API

---

# Internal Components

```
MQTT Client

↓

Driver

↓

Battery Service

Grid Service

VE.Bus Service

MPPT Service

PV Inverter Service

↓

D-Bus
```

---

# Watchdog

If MQTT data stops arriving

- services remain registered
- Connected becomes false
- stale data is not published

When telemetry resumes

- services reconnect automatically

---

# Design Goals

- Native Victron behavior
- Low CPU usage
- Minimal dependencies
- Configurable
- Easy to extend