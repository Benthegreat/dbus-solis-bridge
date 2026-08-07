# dbus-solis-bridge

A lightweight MQTT-to-D-Bus bridge that allows a Solis hybrid inverter to appear as native Victron devices on Venus OS.

Current virtual services:

- com.victronenergy.vebus.solis
- com.victronenergy.solarcharger.solis

This project bridges telemetry from Home Assistant (or any compatible MQTT publisher) into the Victron D-Bus, allowing the Cerbo GX and VRM to display Solis inverter data.

## Features

- Native VE.Bus service
- Native Solar Charger service
- Automatic MQTT reconnect
- Split-phase support
- No external MQTT libraries
- Open source

## Status

Current release:

**v0.1.0-alpha**

Tested on:

- Cerbo GX
- Venus OS Large
- Solis S6-EH2P

## Quick Start

```bash
cp config.example.json config.json
nano config.json
./install.sh