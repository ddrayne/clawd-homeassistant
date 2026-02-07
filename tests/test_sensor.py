"""Tests for WS-backed diagnostic sensors (HA-free)."""

import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import MagicMock

import pytest

_BASE = Path(__file__).parent.parent / "custom_components" / "clawd"

# ── stub homeassistant modules ──


class _CoordinatorEntity:
    def __init__(self, coordinator):
        self.coordinator = coordinator


class _SensorEntity:
    pass


class _SensorStateClass:
    TOTAL_INCREASING = "total_increasing"
    MEASUREMENT = "measurement"


class _EntityCategory:
    DIAGNOSTIC = "diagnostic"


class _UpdateFailed(Exception):
    pass


class _DataUpdateCoordinator:
    pass


_ha = MagicMock()

_sensor_mod = ModuleType("homeassistant.components.sensor")
_sensor_mod.SensorEntity = _SensorEntity  # type: ignore[attr-defined]
_sensor_mod.SensorStateClass = _SensorStateClass  # type: ignore[attr-defined]

_const_mod = ModuleType("homeassistant.const")
_const_mod.EntityCategory = _EntityCategory  # type: ignore[attr-defined]

_coordinator_mod = ModuleType("homeassistant.helpers.update_coordinator")
_coordinator_mod.CoordinatorEntity = _CoordinatorEntity  # type: ignore[attr-defined]
_coordinator_mod.DataUpdateCoordinator = _DataUpdateCoordinator  # type: ignore[attr-defined]
_coordinator_mod.UpdateFailed = _UpdateFailed  # type: ignore[attr-defined]

for mod_name in (
    "homeassistant",
    "homeassistant.components",
    "homeassistant.config_entries",
    "homeassistant.core",
    "homeassistant.helpers",
    "homeassistant.helpers.entity_platform",
):
    sys.modules.setdefault(mod_name, _ha)

sys.modules["homeassistant.components.sensor"] = _sensor_mod
sys.modules["homeassistant.const"] = _const_mod
sys.modules["homeassistant.helpers.update_coordinator"] = _coordinator_mod

sys.modules.setdefault("custom_components", ModuleType("custom_components"))
sys.modules.setdefault("custom_components.clawd", ModuleType("custom_components.clawd"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_const = _load_module("custom_components.clawd.const", _BASE / "const.py")
_exceptions = _load_module("custom_components.clawd.exceptions", _BASE / "exceptions.py")
_gateway = _load_module("custom_components.clawd.gateway", _BASE / "gateway.py")
_gateway_client = _load_module(
    "custom_components.clawd.gateway_client", _BASE / "gateway_client.py"
)
_sensor = _load_module("custom_components.clawd.sensor", _BASE / "sensor.py")

ClawdUptimeSensor = _sensor.ClawdUptimeSensor
ClawdConnectedClientsSensor = _sensor.ClawdConnectedClientsSensor
ClawdHealthSensor = _sensor.ClawdHealthSensor
ClawdGatewayClient = _gateway_client.ClawdGatewayClient


def _make_coordinator(data=None):
    coordinator = MagicMock()
    coordinator.data = data
    return coordinator


def _make_client(**overrides):
    client = ClawdGatewayClient("localhost", 1, None)
    if "presence" in overrides:
        client._gateway._presence = overrides["presence"]
    if "snapshot" in overrides:
        client._gateway._connect_snapshot = overrides["snapshot"]
    return client


# ── Uptime Sensor ──


class TestClawdUptimeSensor:
    def test_native_value_from_coordinator(self) -> None:
        client = _make_client()
        coordinator = _make_coordinator({"uptimeMs": 60000})
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        assert sensor.native_value == 60.0

    def test_native_value_fallback_to_snapshot(self) -> None:
        client = _make_client(snapshot={"snapshot": {"uptimeMs": 30000}})
        coordinator = _make_coordinator(None)
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        assert sensor.native_value == 30.0

    def test_native_value_none_when_no_data(self) -> None:
        client = _make_client()
        coordinator = _make_coordinator(None)
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        assert sensor.native_value is None

    def test_native_value_coordinator_takes_precedence(self) -> None:
        client = _make_client(snapshot={"snapshot": {"uptimeMs": 10000}})
        coordinator = _make_coordinator({"uptimeMs": 90000})
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        assert sensor.native_value == 90.0

    def test_extra_state_attributes(self) -> None:
        client = _make_client()
        coordinator = _make_coordinator({"stateVersion": 5, "sessions": 3})
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        attrs = sensor.extra_state_attributes
        assert attrs["state_version"] == 5
        assert attrs["sessions"] == 3

    def test_extra_state_attributes_empty(self) -> None:
        client = _make_client()
        coordinator = _make_coordinator(None)
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        attrs = sensor.extra_state_attributes
        assert attrs["state_version"] is None
        assert attrs["sessions"] is None

    def test_unique_id(self) -> None:
        client = _make_client()
        coordinator = _make_coordinator(None)
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        assert sensor._attr_unique_id == "test_entry_gateway_uptime"

    def test_device_info(self) -> None:
        client = _make_client()
        coordinator = _make_coordinator(None)
        sensor = ClawdUptimeSensor(coordinator, "test_entry", client)
        info = sensor.device_info
        assert ("clawd", "test_entry") in info["identifiers"]


# ── Connected Clients Sensor ──


class TestClawdConnectedClientsSensor:
    def test_native_value_from_list(self) -> None:
        client = _make_client(presence={"clients": ["a", "b", "c"]})
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        assert sensor.native_value == 3

    def test_native_value_from_int(self) -> None:
        client = _make_client(presence={"clients": 5})
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        assert sensor.native_value == 5

    def test_native_value_none_when_no_presence(self) -> None:
        client = _make_client()
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        assert sensor.native_value is None

    def test_native_value_none_when_clients_missing(self) -> None:
        client = _make_client(presence={"other": "data"})
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        assert sensor.native_value is None

    def test_extra_state_attributes_with_list(self) -> None:
        client = _make_client(presence={"clients": ["ha", "web"]})
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        attrs = sensor.extra_state_attributes
        assert attrs["client_list"] == ["ha", "web"]

    def test_extra_state_attributes_no_list(self) -> None:
        client = _make_client(presence={"clients": 2})
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        attrs = sensor.extra_state_attributes
        assert "client_list" not in attrs

    def test_extra_state_attributes_empty(self) -> None:
        client = _make_client()
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        attrs = sensor.extra_state_attributes
        assert attrs == {}

    def test_unique_id(self) -> None:
        client = _make_client()
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        assert sensor._attr_unique_id == "test_entry_connected_clients"

    def test_device_info(self) -> None:
        client = _make_client()
        sensor = ClawdConnectedClientsSensor("test_entry", client)
        info = sensor.device_info
        assert ("clawd", "test_entry") in info["identifiers"]


# ── Health Sensor ──


class TestClawdHealthSensor:
    def test_native_value(self) -> None:
        coordinator = _make_coordinator({"status": "ok"})
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        assert sensor.native_value == "ok"

    def test_native_value_none_when_no_data(self) -> None:
        coordinator = _make_coordinator(None)
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        assert sensor.native_value is None

    def test_native_value_none_when_status_missing(self) -> None:
        coordinator = _make_coordinator({"version": "1.0"})
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        assert sensor.native_value is None

    def test_extra_state_attributes(self) -> None:
        coordinator = _make_coordinator({
            "status": "ok",
            "version": "2.1.0",
            "uptimeMs": 50000,
            "memoryUsage": 128,
            "cpuUsage": 0.5,
        })
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        attrs = sensor.extra_state_attributes
        assert attrs["version"] == "2.1.0"
        assert attrs["uptimeMs"] == 50000
        assert attrs["memoryUsage"] == 128
        assert attrs["cpuUsage"] == 0.5

    def test_extra_state_attributes_omits_missing(self) -> None:
        coordinator = _make_coordinator({"status": "ok"})
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        attrs = sensor.extra_state_attributes
        assert attrs == {}

    def test_extra_state_attributes_empty_data(self) -> None:
        coordinator = _make_coordinator(None)
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        attrs = sensor.extra_state_attributes
        assert attrs == {}

    def test_unique_id(self) -> None:
        coordinator = _make_coordinator(None)
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        assert sensor._attr_unique_id == "test_entry_gateway_health"

    def test_device_info(self) -> None:
        coordinator = _make_coordinator(None)
        sensor = ClawdHealthSensor(coordinator, "test_entry")
        info = sensor.device_info
        assert ("clawd", "test_entry") in info["identifiers"]
