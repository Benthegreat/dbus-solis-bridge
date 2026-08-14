# Troubleshooting

---

# No D-Bus Services

Check

```bash
pgrep -af dbus_solis.py
```

Then

```bash
dbus -y | grep solis
```

---

# MQTT Not Connecting

Verify

- broker IP
- username
- password
- topic

Check

```bash
mosquitto_sub
```

---

# Services Disconnect After 10 Seconds

The watchdog has not received MQTT data.

Verify Home Assistant automation is publishing.

---

# Install Works But Doesn't Start After Reboot

Verify

```
/data/rc.local
```

contains

```sh
ln -s /data/dbus-solis/service /service/dbus-solis
```

---

# JSON Errors

Validate

```bash
python3 -m json.tool config.json
```

---

# Wrong Battery Direction

Battery should be

Positive

Charging

Negative

Discharging

Reverse sign in Home Assistant if necessary.

---

# Wrong Grid Direction

Grid should be

Positive

Import

Negative

Export

---

# Bridge Crashes

Run manually

```bash
python3 dbus_solis.py
```

The traceback usually identifies the issue.

---

# Debug Logging

Edit

```
config.json
```

```json
"log_level":"DEBUG"
```

Restart the bridge.
