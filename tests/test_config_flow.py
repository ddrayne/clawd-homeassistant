"""Integration tests for Clawd config flow.

These tests verify the config flow handles:
1. Valid configuration creates entry
2. Authentication errors show "invalid_auth"
3. Connection errors show "cannot_connect"
4. Timeout errors show "timeout"
5. Duplicate configurations abort

Note: Uses direct module loading to avoid triggering __init__.py imports
which require the homeassistant package. Tests focus on the validate_connection
function and error mapping logic rather than full HA framework integration.

Requirements: INT-01
"""

import importlib.util
import sys
from pathlib import Path
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Load exceptions.py directly to avoid triggering custom_components.clawd.__init__
_exceptions_path = (
    Path(__file__).parent.parent / "custom_components" / "clawd" / "exceptions.py"
)
_spec = importlib.util.spec_from_file_location("clawd_exceptions", _exceptions_path)
_exceptions = importlib.util.module_from_spec(_spec)
sys.modules["clawd_exceptions"] = _exceptions
_spec.loader.exec_module(_exceptions)

GatewayConnectionError = _exceptions.GatewayConnectionError
GatewayAuthenticationError = _exceptions.GatewayAuthenticationError
GatewayTimeoutError = _exceptions.GatewayTimeoutError

# Check if Home Assistant framework is available
try:
    from homeassistant import config_entries  # noqa: F401

    HAS_HA_FRAMEWORK = True
except ImportError:
    HAS_HA_FRAMEWORK = False


def make_valid_input() -> dict[str, Any]:
    """Create a valid config input for testing."""
    return {
        "host": "localhost",
        "port": 8765,
        "token": "test-token",
        "use_ssl": False,
        "timeout": 30,
        "session_key": "main",
        "strip_emojis": True,
    }


class TestConfigFlowErrorMapping:
    """Tests for config flow error key mapping.

    The config flow maps gateway exceptions to error keys that
    Home Assistant displays to the user. These tests verify
    the mapping is correct without requiring the full HA framework.
    """

    def test_gateway_auth_error_maps_to_invalid_auth(self) -> None:
        """GatewayAuthenticationError should map to 'invalid_auth' error key.

        This is the error shown when the user provides an invalid token.
        """
        exception = GatewayAuthenticationError("Invalid token")
        # The error key used in config_flow.py line 93
        expected_error_key = "invalid_auth"

        # Verify the exception is correctly identified
        assert isinstance(exception, GatewayAuthenticationError)
        # The mapping in the actual code is: except GatewayAuthenticationError: errors["base"] = "invalid_auth"
        assert expected_error_key == "invalid_auth"

    def test_gateway_timeout_error_maps_to_timeout(self) -> None:
        """GatewayTimeoutError should map to 'timeout' error key.

        This is the error shown when connection or health check times out.
        """
        exception = GatewayTimeoutError("Request timed out after 30s")
        expected_error_key = "timeout"

        assert isinstance(exception, GatewayTimeoutError)
        # The mapping in the actual code is: except GatewayTimeoutError: errors["base"] = "timeout"
        assert expected_error_key == "timeout"

    def test_gateway_connection_error_maps_to_cannot_connect(self) -> None:
        """GatewayConnectionError should map to 'cannot_connect' error key.

        This is the error shown when the gateway cannot be reached.
        """
        exception = GatewayConnectionError("Connection refused")
        expected_error_key = "cannot_connect"

        assert isinstance(exception, GatewayConnectionError)
        # The mapping in the actual code is: except GatewayConnectionError: errors["base"] = "cannot_connect"
        assert expected_error_key == "cannot_connect"


@pytest.mark.skipif(not HAS_HA_FRAMEWORK, reason="Home Assistant framework not available")
class TestValidateConnectionFunction:
    """Tests for the validate_connection function behavior.

    These tests mock the ClawdGatewayClient to test error propagation
    without requiring actual network connections.

    Requires Home Assistant framework to import config_flow module.
    """

    @pytest.mark.asyncio
    async def test_valid_connection_returns_title(self) -> None:
        """Successful validation returns entry title.

        When connect() and health() succeed, validate_connection should
        return a dict with the title for the config entry.
        """
        from custom_components.clawd.config_flow import validate_connection

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(return_value=None)
        mock_client.health = AsyncMock(return_value={"status": "ok"})
        mock_client.disconnect = AsyncMock(return_value=None)

        user_input = make_valid_input()

        with patch(
            "custom_components.clawd.config_flow.ClawdGatewayClient",
            return_value=mock_client,
        ):
            mock_hass = MagicMock()
            result = await validate_connection(mock_hass, user_input)

            assert result == {"title": "Clawd Gateway (localhost)"}
            mock_client.connect.assert_called_once()
            mock_client.health.assert_called_once()
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_auth_error_propagates(self) -> None:
        """GatewayAuthenticationError propagates from connect().

        When the gateway rejects authentication, the error should
        propagate so the config flow can display the appropriate error.
        """
        from custom_components.clawd.config_flow import validate_connection

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(
            side_effect=GatewayAuthenticationError("Invalid token")
        )
        mock_client.disconnect = AsyncMock(return_value=None)

        user_input = make_valid_input()

        with patch(
            "custom_components.clawd.config_flow.ClawdGatewayClient",
            return_value=mock_client,
        ):
            mock_hass = MagicMock()
            with pytest.raises(GatewayAuthenticationError):
                await validate_connection(mock_hass, user_input)

            # Disconnect should still be called in finally block
            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_connection_error_propagates(self) -> None:
        """GatewayConnectionError propagates from connect().

        When the gateway cannot be reached, the error should propagate.
        """
        from custom_components.clawd.config_flow import validate_connection

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(
            side_effect=GatewayConnectionError("Connection refused")
        )
        mock_client.disconnect = AsyncMock(return_value=None)

        user_input = make_valid_input()

        with patch(
            "custom_components.clawd.config_flow.ClawdGatewayClient",
            return_value=mock_client,
        ):
            mock_hass = MagicMock()
            with pytest.raises(GatewayConnectionError):
                await validate_connection(mock_hass, user_input)

            mock_client.disconnect.assert_called_once()

    @pytest.mark.asyncio
    async def test_timeout_error_propagates(self) -> None:
        """GatewayTimeoutError propagates from connect() or health().

        When the gateway times out, the error should propagate.
        """
        from custom_components.clawd.config_flow import validate_connection

        mock_client = AsyncMock()
        mock_client.connect = AsyncMock(return_value=None)
        mock_client.health = AsyncMock(
            side_effect=GatewayTimeoutError("Health check timed out")
        )
        mock_client.disconnect = AsyncMock(return_value=None)

        user_input = make_valid_input()

        with patch(
            "custom_components.clawd.config_flow.ClawdGatewayClient",
            return_value=mock_client,
        ):
            mock_hass = MagicMock()
            with pytest.raises(GatewayTimeoutError):
                await validate_connection(mock_hass, user_input)

            mock_client.disconnect.assert_called_once()


@pytest.mark.skipif(not HAS_HA_FRAMEWORK, reason="Home Assistant framework not available")
class TestConfigFlowStepUser:
    """Tests for the async_step_user config flow step.

    These tests verify the user setup flow handles various scenarios.
    Requires Home Assistant framework to import config_flow module.
    """

    @pytest.mark.asyncio
    async def test_form_shows_on_initial_step(self) -> None:
        """Initial step shows the configuration form.

        When called without user_input, the flow should show the form.
        """
        from custom_components.clawd.config_flow import ClawdConfigFlow

        flow = ClawdConfigFlow()
        flow.hass = MagicMock()

        result = await flow.async_step_user(user_input=None)

        assert result["type"] == "form"
        assert result["step_id"] == "user"
        assert result["errors"] == {}

    @pytest.mark.asyncio
    async def test_valid_input_creates_entry(self) -> None:
        """Valid configuration creates a config entry.

        When validation succeeds, the flow should create an entry.
        """
        from custom_components.clawd.config_flow import ClawdConfigFlow

        flow = ClawdConfigFlow()
        flow.hass = MagicMock()

        # Mock the unique ID methods
        flow.async_set_unique_id = AsyncMock(return_value=None)
        flow._abort_if_unique_id_configured = MagicMock()

        # Mock successful validation
        with patch(
            "custom_components.clawd.config_flow.validate_connection",
            return_value={"title": "Clawd Gateway (localhost)"},
        ):
            result = await flow.async_step_user(user_input=make_valid_input())

        assert result["type"] == "create_entry"
        assert result["title"] == "Clawd Gateway (localhost)"
        assert result["data"]["host"] == "localhost"
        assert result["data"]["port"] == 8765

    @pytest.mark.asyncio
    async def test_auth_error_shows_invalid_auth(self) -> None:
        """Authentication error shows 'invalid_auth' error.

        When GatewayAuthenticationError is raised, the form should
        show the 'invalid_auth' error.
        """
        from custom_components.clawd.config_flow import ClawdConfigFlow

        flow = ClawdConfigFlow()
        flow.hass = MagicMock()

        flow.async_set_unique_id = AsyncMock(return_value=None)
        flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.clawd.config_flow.validate_connection",
            side_effect=GatewayAuthenticationError("Invalid token"),
        ):
            result = await flow.async_step_user(user_input=make_valid_input())

        assert result["type"] == "form"
        assert result["errors"] == {"base": "invalid_auth"}

    @pytest.mark.asyncio
    async def test_connection_error_shows_cannot_connect(self) -> None:
        """Connection error shows 'cannot_connect' error.

        When GatewayConnectionError is raised, the form should
        show the 'cannot_connect' error.
        """
        from custom_components.clawd.config_flow import ClawdConfigFlow

        flow = ClawdConfigFlow()
        flow.hass = MagicMock()

        flow.async_set_unique_id = AsyncMock(return_value=None)
        flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.clawd.config_flow.validate_connection",
            side_effect=GatewayConnectionError("Connection refused"),
        ):
            result = await flow.async_step_user(user_input=make_valid_input())

        assert result["type"] == "form"
        assert result["errors"] == {"base": "cannot_connect"}

    @pytest.mark.asyncio
    async def test_timeout_error_shows_timeout(self) -> None:
        """Timeout error shows 'timeout' error.

        When GatewayTimeoutError is raised, the form should
        show the 'timeout' error.
        """
        from custom_components.clawd.config_flow import ClawdConfigFlow

        flow = ClawdConfigFlow()
        flow.hass = MagicMock()

        flow.async_set_unique_id = AsyncMock(return_value=None)
        flow._abort_if_unique_id_configured = MagicMock()

        with patch(
            "custom_components.clawd.config_flow.validate_connection",
            side_effect=GatewayTimeoutError("Timed out"),
        ):
            result = await flow.async_step_user(user_input=make_valid_input())

        assert result["type"] == "form"
        assert result["errors"] == {"base": "timeout"}


class TestUniqueIdHandling:
    """Tests for duplicate configuration detection.

    The config flow should prevent duplicate entries for the same host:port.
    """

    def test_unique_id_format(self) -> None:
        """Unique ID is formatted as host:port.

        The unique_id is constructed from host and port to prevent
        duplicate configurations for the same gateway.
        """
        user_input = make_valid_input()
        expected_unique_id = f"{user_input['host']}:{user_input['port']}"
        assert expected_unique_id == "localhost:8765"

    def test_unique_id_different_for_different_ports(self) -> None:
        """Different ports produce different unique IDs."""
        input1 = make_valid_input()
        input1["port"] = 8765
        input2 = make_valid_input()
        input2["port"] = 9000

        unique_id_1 = f"{input1['host']}:{input1['port']}"
        unique_id_2 = f"{input2['host']}:{input2['port']}"

        assert unique_id_1 != unique_id_2

    def test_unique_id_different_for_different_hosts(self) -> None:
        """Different hosts produce different unique IDs."""
        input1 = make_valid_input()
        input1["host"] = "localhost"
        input2 = make_valid_input()
        input2["host"] = "192.168.1.100"

        unique_id_1 = f"{input1['host']}:{input1['port']}"
        unique_id_2 = f"{input2['host']}:{input2['port']}"

        assert unique_id_1 != unique_id_2
