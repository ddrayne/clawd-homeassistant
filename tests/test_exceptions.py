"""Minimal tests for exception hierarchy."""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load exceptions.py directly to avoid triggering custom_components.openclaw.__init__
# which imports homeassistant
_exceptions_path = (
    Path(__file__).parent.parent / "custom_components" / "openclaw" / "exceptions.py"
)
_spec = importlib.util.spec_from_file_location("openclaw_exceptions", _exceptions_path)
_exceptions = importlib.util.module_from_spec(_spec)
sys.modules["openclaw_exceptions"] = _exceptions
_spec.loader.exec_module(_exceptions)

# Import all exceptions from the loaded module
OpenClawError = _exceptions.OpenClawError
GatewayConnectionError = _exceptions.GatewayConnectionError
GatewayAuthenticationError = _exceptions.GatewayAuthenticationError
DevicePairingRequiredError = _exceptions.DevicePairingRequiredError
GatewayTimeoutError = _exceptions.GatewayTimeoutError
AgentExecutionError = _exceptions.AgentExecutionError
ProtocolError = _exceptions.ProtocolError

# Subclasses only (excludes base OpenClawError).
SUBCLASS_EXCEPTIONS = [
    GatewayConnectionError,
    GatewayAuthenticationError,
    DevicePairingRequiredError,
    GatewayTimeoutError,
    AgentExecutionError,
    ProtocolError,
]


class TestExceptionHierarchy:
    @pytest.mark.parametrize(
        "exception_class",
        SUBCLASS_EXCEPTIONS,
        ids=[e.__name__ for e in SUBCLASS_EXCEPTIONS],
    )
    def test_inherits_from_openclaw_error(self, exception_class) -> None:
        assert issubclass(exception_class, OpenClawError)

    def test_device_pairing_is_auth_error(self) -> None:
        """DevicePairingRequiredError is a subclass of GatewayAuthenticationError."""
        assert issubclass(DevicePairingRequiredError, GatewayAuthenticationError)
        err = DevicePairingRequiredError("pairing required")
        assert isinstance(err, GatewayAuthenticationError)
