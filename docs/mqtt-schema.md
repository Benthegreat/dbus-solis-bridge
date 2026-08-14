# MQTT Schema

The bridge consumes a single JSON payload.

Topic:

```
solis/venus/update
```

---

# Root Objects

```text
battery
grid
vebus
mppt
ac_pv
```

---

# battery

```json
{
    "soc":94,
    "soh":100,
    "voltage":53.1,
    "current":-120,
    "power":-6350,
    "temperature":22,
    "max_charge_current":920,
    "max_discharge_current":920
}
```

---

# grid

```json
{
    "frequency":60,
    "total_power":120,
    "energy_from_grid":4200,
    "energy_to_grid":12800,
    "l1":{},
    "l2":{}
}
```

---

# vebus

Contains

- state
- mode
- DC bus
- AC input
- AC output
- energy counters

---

# mppt

Contains

- MPPT state
- PV voltage
- PV current
- PV power
- yield

---

# ac_pv

```json
{
    "connected":true,
    "position":1,
    "l1":{},
    "l2":{},
    "power":5200,
    "energy_today":21.3,
    "energy_total":4511
}
```

---

# Sign Conventions

## Battery

Positive

- charging

Negative

- discharging

---

## VE.Bus DC

Positive

- AC → DC
- Rectifying

Negative

- DC → AC
- Inverting

---

## Grid

Positive

- Import

Negative

- Export

---

## PV

Positive

- Producing

Negative

- Idle / measurement noise

---

# Timing

Recommended publish interval

```
2 seconds
```

Maximum recommended

```
1 second
```
