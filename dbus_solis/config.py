from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path


DEFAULT_CONFIG = "/data/dbus-solis/config.json"


@dataclass(frozen=True)
class MQTTConfig:
    host: str
    port: int
    topic: str
    username: str
    password: str
    client_id: str
    keepalive: int
    tls: bool
    tls_insecure: bool


@dataclass(frozen=True)
class DeviceInstances:
    vebus: int
    mppt: int
    battery: int


@dataclass(frozen=True)
class AppConfig:
    mqtt: MQTTConfig
    devices: DeviceInstances
    stale_timeout: int
    log_level: str


def load_config(path: str = DEFAULT_CONFIG) -> AppConfig:
    config_file = Path(path)

    if not config_file.exists():
        raise FileNotFoundError(
            f"{config_file} does not exist. "
            "Copy config.example.json to config.json first."
        )

    with config_file.open("r", encoding="utf-8") as f:
        raw = json.load(f)

    mqtt = raw["mqtt"]

    host = mqtt["host"].strip()

    if host.startswith("http://") or host.startswith("https://"):
        raise ValueError(
            "MQTT host must not include http:// or https://"
        )

    return AppConfig(
        mqtt=MQTTConfig(
            host=host,
            port=int(mqtt.get("port", 1883)),
            topic=mqtt["topic"],
            username=mqtt.get("username", ""),
            password=mqtt.get("password", ""),
            client_id=mqtt.get(
                "client_id",
                "venus-dbus-solis"
            ),
            keepalive=int(mqtt.get("keepalive", 30)),
            tls=bool(mqtt.get("tls", False)),
            tls_insecure=bool(mqtt.get("tls_insecure", False)),
        ),
        devices=DeviceInstances(
            vebus=int(raw["device_instances"]["vebus"]),
            mppt=int(raw["device_instances"]["mppt"]),
            battery=int(
                raw["device_instances"].get("battery", 262)
            ),
        ),
        stale_timeout=int(
            raw.get("stale_timeout_seconds", 10)
        ),
        log_level=raw.get("log_level", "INFO").upper(),
    )