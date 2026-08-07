#!/bin/sh
set -eu

APP_DIR="/data/dbus-solis"
SERVICE_LINK="/service/dbus-solis"

echo "Installing dbus-solis..."

if [ ! -f "$APP_DIR/dbus_solis.py" ]; then
    echo "Error: $APP_DIR/dbus_solis.py not found."
    echo "Copy the repository to $APP_DIR before running this installer."
    exit 1
fi

if [ ! -f "$APP_DIR/config.json" ]; then
    if [ -f "$APP_DIR/config.example.json" ]; then
        cp "$APP_DIR/config.example.json" "$APP_DIR/config.json"
        echo "Created config.json from config.example.json."
        echo "Edit $APP_DIR/config.json, then run ./install.sh again."
        exit 2
    fi

    echo "Error: No config.json or config.example.json found."
    exit 1
fi

echo "Validating config.json..."
python3 -m json.tool "$APP_DIR/config.json" >/dev/null

echo "Fixing line endings and permissions..."
sed -i 's/\r$//' "$APP_DIR/dbus_solis.py"
sed -i 's/\r$//' "$APP_DIR/service/run"
sed -i 's/\r$//' "$APP_DIR/install.sh"
sed -i 's/\r$//' "$APP_DIR/uninstall.sh"

chmod 755 "$APP_DIR/dbus_solis.py"
chmod 755 "$APP_DIR/service/run"
chmod 755 "$APP_DIR/install.sh"
chmod 755 "$APP_DIR/uninstall.sh"

if [ -e "$SERVICE_LINK" ] || [ -L "$SERVICE_LINK" ]; then
    echo "Removing existing service link..."
    svc -d "$SERVICE_LINK" 2>/dev/null || true
    rm -rf "$SERVICE_LINK"
fi

echo "Creating service link..."
ln -s "$APP_DIR/service" "$SERVICE_LINK"

echo "Starting dbus-solis..."
svc -u "$SERVICE_LINK"

sleep 3

if pgrep -f "$APP_DIR/dbus_solis.py" >/dev/null; then
    echo
    echo "dbus-solis is running."
    echo
    echo "Check D-Bus services with:"
    echo "  dbus -y | grep solis"
    echo
    echo "Check live values with:"
    echo "  dbus -y com.victronenergy.vebus.solis /Connected GetValue"
    echo "  dbus -y com.victronenergy.solarcharger.solis /Connected GetValue"
else
    echo
    echo "Error: dbus-solis did not start."
    echo
    echo "Run manually for diagnostics:"
    echo "  /usr/bin/python3 -u $APP_DIR/dbus_solis.py"
    exit 1
fi