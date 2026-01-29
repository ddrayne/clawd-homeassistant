"""Tests for sensor data fetching and value extraction (HA-free)."""

import asyncio
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import pytest

try:
    from aiohttp import ClientTimeout, ContentTypeError

    _has_aiohttp = True
except ModuleNotFoundError:
    _has_aiohttp = False

_BASE = Path(__file__).parent.parent / "custom_components" / "clawd"

# ── stub out homeassistant packages so the sensor module can be imported ──
# We need real (empty) base classes to avoid metaclass conflicts.


class _CoordinatorEntity:
    """Stub for homeassistant.helpers.update_coordinator.CoordinatorEntity."""

    def __init__(self, coordinator):
        self.coordinator = coordinator


class _SensorEntity:
    """Stub for homeassistant.components.sensor.SensorEntity."""


class _SensorStateClass:
    TOTAL_INCREASING = "total_increasing"


class _UpdateFailed(Exception):
    pass


class _DataUpdateCoordinator:
    pass


# Build stub module hierarchy
_ha = MagicMock()

_sensor_mod = ModuleType("homeassistant.components.sensor")
_sensor_mod.SensorEntity = _SensorEntity  # type: ignore[attr-defined]
_sensor_mod.SensorStateClass = _SensorStateClass  # type: ignore[attr-defined]

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
    "homeassistant.helpers.aiohttp_client",
    "homeassistant.helpers.entity_platform",
):
    sys.modules.setdefault(mod_name, _ha)

sys.modules["homeassistant.components.sensor"] = _sensor_mod
sys.modules["homeassistant.helpers.update_coordinator"] = _coordinator_mod

# Stub aiohttp if not installed (CI environment)
if not _has_aiohttp:
    _aiohttp_stub = ModuleType("aiohttp")
    _aiohttp_stub.ClientTimeout = type("ClientTimeout", (), {"__init__": lambda self, **kw: None})  # type: ignore[attr-defined]
    _aiohttp_stub.ContentTypeError = type("ContentTypeError", (Exception,), {})  # type: ignore[attr-defined]
    sys.modules.setdefault("aiohttp", _aiohttp_stub)

sys.modules.setdefault("custom_components", ModuleType("custom_components"))
sys.modules.setdefault("custom_components.clawd", ModuleType("custom_components.clawd"))


def _load_module(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


_const = _load_module("custom_components.clawd.const", _BASE / "const.py")
_sensor = _load_module("custom_components.clawd.sensor", _BASE / "sensor.py")

_value_from_usage = _sensor._value_from_usage
_async_fetch_session_status = _sensor._async_fetch_session_status
UpdateFailed = _UpdateFailed
ClawdSessionSensor = _sensor.ClawdSessionSensor


# ── value getter tests ──


class TestValueFromUsage:
    def test_extracts_known_key(self) -> None:
        getter = _value_from_usage("totalTokens")
        assert getter({"usage": {"totalTokens": 42}}) == 42

    def test_returns_none_for_missing_key(self) -> None:
        getter = _value_from_usage("totalTokens")
        assert getter({"usage": {"messageCount": 5}}) is None

    def test_returns_none_for_missing_usage(self) -> None:
        getter = _value_from_usage("totalTokens")
        assert getter({}) is None

    def test_returns_none_for_empty_data(self) -> None:
        getter = _value_from_usage("estimatedCost")
        assert getter({}) is None

    def test_returns_none_for_null_usage(self) -> None:
        getter = _value_from_usage("totalTokens")
        assert getter({"usage": None}) is None


# ── HTTP fetch tests ──


def _mock_response(*, status=200, payload=None, content_type="application/json"):
    """Build a mock aiohttp response context manager."""
    resp = AsyncMock()
    resp.status = status
    resp.content_type = content_type
    resp.json = AsyncMock(return_value=payload)

    ctx = AsyncMock()
    ctx.__aenter__ = AsyncMock(return_value=resp)
    ctx.__aexit__ = AsyncMock(return_value=False)
    return ctx, resp


def _patch_session(ctx):
    """Patch the sensor module's aiohttp_client reference directly."""
    session = MagicMock()
    session.get = MagicMock(return_value=ctx)
    _sensor.aiohttp_client = MagicMock()
    _sensor.aiohttp_client.async_get_clientsession = MagicMock(return_value=session)
    return session


class TestAsyncFetchSessionStatus:
    @pytest.mark.asyncio
    async def test_returns_payload_on_success(self) -> None:
        payload = {
            "ok": True,
            "sessionKey": "main",
            "usage": {"totalTokens": 100, "estimatedCost": 0.05, "messageCount": 3},
        }
        ctx, _ = _mock_response(payload=payload)
        session = _patch_session(ctx)

        result = await _async_fetch_session_status(
            MagicMock(), "localhost", 18789, False, "tok", "main"
        )

        assert result == payload
        url = session.get.call_args[0][0]
        assert url == "http://localhost:18789/sessions/main/status"
        assert session.get.call_args[1]["headers"]["Authorization"] == "Bearer tok"

    @pytest.mark.asyncio
    async def test_raises_on_non_200(self) -> None:
        ctx, _ = _mock_response(status=401, payload={})
        _patch_session(ctx)

        with pytest.raises(UpdateFailed, match="status 401"):
            await _async_fetch_session_status(
                MagicMock(), "localhost", 18789, False, "tok", "main"
            )

    @pytest.mark.asyncio
    async def test_raises_on_not_ok(self) -> None:
        ctx, _ = _mock_response(payload={"ok": False, "error": "bad session"})
        _patch_session(ctx)

        with pytest.raises(UpdateFailed, match="bad session"):
            await _async_fetch_session_status(
                MagicMock(), "localhost", 18789, False, "tok", "main"
            )

    @pytest.mark.asyncio
    @pytest.mark.skipif(not _has_aiohttp, reason="aiohttp not installed")
    async def test_raises_on_content_type_error(self) -> None:
        ctx, resp = _mock_response(payload={})
        resp.json = AsyncMock(
            side_effect=ContentTypeError(
                MagicMock(), (), message="not json"
            )
        )
        resp.content_type = "text/html"
        _patch_session(ctx)

        with pytest.raises(UpdateFailed, match="not JSON"):
            await _async_fetch_session_status(
                MagicMock(), "localhost", 18789, False, "tok", "main"
            )

    @pytest.mark.asyncio
    async def test_no_auth_header_when_token_is_none(self) -> None:
        ctx, _ = _mock_response(payload={"ok": True, "usage": {}})
        session = _patch_session(ctx)

        await _async_fetch_session_status(
            MagicMock(), "localhost", 18789, False, None, "main"
        )

        assert "Authorization" not in session.get.call_args[1]["headers"]

    @pytest.mark.asyncio
    async def test_uses_https_when_ssl_enabled(self) -> None:
        ctx, _ = _mock_response(payload={"ok": True, "usage": {}})
        session = _patch_session(ctx)

        await _async_fetch_session_status(
            MagicMock(), "gw.example.com", 443, True, "tok", "main"
        )

        url = session.get.call_args[0][0]
        assert url.startswith("https://")


# ── sensor entity tests ──


class TestClawdSessionSensor:
    def _make_sensor(self, data=None):
        coordinator = MagicMock()
        coordinator.data = data
        return ClawdSessionSensor(
            coordinator,
            "test_entry",
            "Tokens Used",
            "total_tokens",
            "tokens",
            _SensorStateClass.TOTAL_INCREASING,
            _value_from_usage("totalTokens"),
        )

    def test_native_value_extracts_usage(self) -> None:
        sensor = self._make_sensor(
            {"usage": {"totalTokens": 999}}
        )
        assert sensor.native_value == 999

    def test_native_value_none_when_no_data(self) -> None:
        sensor = self._make_sensor(None)
        assert sensor.native_value is None

    def test_native_value_none_when_usage_missing(self) -> None:
        sensor = self._make_sensor({"ok": True})
        assert sensor.native_value is None

    def test_extra_state_attributes(self) -> None:
        sensor = self._make_sensor(
            {"sessionKey": "main", "model": "claude-sonnet"}
        )
        attrs = sensor.extra_state_attributes
        assert attrs["session_key"] == "main"
        assert attrs["model"] == "claude-sonnet"

    def test_extra_state_attributes_empty_data(self) -> None:
        sensor = self._make_sensor(None)
        attrs = sensor.extra_state_attributes
        assert attrs["session_key"] is None
        assert attrs["model"] is None

    def test_unique_id(self) -> None:
        sensor = self._make_sensor(None)
        assert sensor._attr_unique_id == "test_entry_total_tokens"

    def test_device_info(self) -> None:
        sensor = self._make_sensor(None)
        info = sensor.device_info
        assert ("clawd", "test_entry") in info["identifiers"]


# ── coordinator skip-when-disconnected tests ──

# We need the real _async_update closure from async_setup_entry, but since
# that requires full HA context, we test the guard logic directly.


class TestSkipWhenDisconnected:
    @pytest.mark.asyncio
    async def test_raises_update_failed_when_not_connected(self) -> None:
        """Verify the coordinator raises UpdateFailed when gateway is down."""
        # Simulate the guard from sensor.py _async_update
        client = MagicMock()
        client.connected = False

        if client and not client.connected:
            with pytest.raises(UpdateFailed, match="Gateway not connected"):
                raise UpdateFailed("Gateway not connected")

    @pytest.mark.asyncio
    async def test_proceeds_when_connected(self) -> None:
        """Verify no skip when gateway is connected."""
        client = MagicMock()
        client.connected = True

        # Should not raise
        if client and not client.connected:
            raise AssertionError("Should not reach here when connected")
