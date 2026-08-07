#!/bin/sh
set -eu

APP_DIR="/data/dbus-solis"
SERVICE_LINK="/service/dbus-solis"

echo "Uninstalling dbus-solis..."

if [ -e "$SERVICE_LINK" ] || [ -L "$SERVICE_LINK" ]; then
    svc -d "$SERVICE_LINK" 2>/dev/null || true
    rm -rf "$SERVICE_LINK"
    echo "Removed service link."
else
    echo "Service link not present."
fi

echo
echo "Driver files were NOT deleted."
echo "Configuration was preserved at:"
echo "  $APP_DIR/config.json"
echo
echo "To remove the project completely:"
echo "  rm -rf $APP_DIR"