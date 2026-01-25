"""Unit tests for Clawd integration constants.

These tests serve as executable documentation for const.py.
If a constant value changes, the test failure alerts developers
to update dependent code throughout the codebase.

Note: Uses direct module loading to avoid triggering __init__.py imports
which require the homeassistant package.
"""

import importlib.util
import sys
from pathlib import Path

import pytest

# Load const.py directly to avoid triggering custom_components.clawd.__init__
# which imports homeassistant
_const_path = Path(__file__).parent.parent / "custom_components" / "clawd" / "const.py"
_spec = importlib.util.spec_from_file_location("clawd_const", _const_path)
_const = importlib.util.module_from_spec(_spec)
sys.modules["clawd_const"] = _const
_spec.loader.exec_module(_const)

# Import all constants from the loaded module
DOMAIN = _const.DOMAIN
DEFAULT_HOST = _const.DEFAULT_HOST
DEFAULT_PORT = _const.DEFAULT_PORT
DEFAULT_USE_SSL = _const.DEFAULT_USE_SSL
DEFAULT_TIMEOUT = _const.DEFAULT_TIMEOUT
DEFAULT_SESSION_KEY = _const.DEFAULT_SESSION_KEY
DEFAULT_STRIP_EMOJIS = _const.DEFAULT_STRIP_EMOJIS
CONF_HOST = _const.CONF_HOST
CONF_PORT = _const.CONF_PORT
CONF_TOKEN = _const.CONF_TOKEN
CONF_USE_SSL = _const.CONF_USE_SSL
CONF_TIMEOUT = _const.CONF_TIMEOUT
CONF_SESSION_KEY = _const.CONF_SESSION_KEY
CONF_STRIP_EMOJIS = _const.CONF_STRIP_EMOJIS
STATE_CONNECTED = _const.STATE_CONNECTED
STATE_DISCONNECTED = _const.STATE_DISCONNECTED
STATE_CONNECTING = _const.STATE_CONNECTING
STATE_ERROR = _const.STATE_ERROR
PROTOCOL_MIN_VERSION = _const.PROTOCOL_MIN_VERSION
PROTOCOL_MAX_VERSION = _const.PROTOCOL_MAX_VERSION
CLIENT_ID = _const.CLIENT_ID
CLIENT_DISPLAY_NAME = _const.CLIENT_DISPLAY_NAME
CLIENT_VERSION = _const.CLIENT_VERSION
CLIENT_PLATFORM = _const.CLIENT_PLATFORM
CLIENT_MODE = _const.CLIENT_MODE


class TestDomain:
    """Tests for the DOMAIN constant.

    The domain is critical - it must never change as it's used
    throughout Home Assistant for identification and configuration.
    """

    def test_domain_is_clawd(self):
        """Domain must be 'clawd' - this is the integration identifier."""
        assert DOMAIN == "clawd"

    def test_domain_is_lowercase(self):
        """Domain should be lowercase per Home Assistant conventions."""
        assert DOMAIN == DOMAIN.lower()

    def test_domain_is_alphanumeric(self):
        """Domain should only contain alphanumeric characters."""
        assert DOMAIN.isalnum()


class TestDefaultConfiguration:
    """Tests for DEFAULT_* configuration constants.

    These document the out-of-box defaults for the integration.
    Changing these affects new installations.
    """

    def test_default_host_is_localhost(self):
        """Default host should be localhost for local development."""
        assert DEFAULT_HOST == "127.0.0.1"

    def test_default_host_is_valid_ip(self):
        """Default host should be a valid IP address format."""
        parts = DEFAULT_HOST.split(".")
        assert len(parts) == 4
        assert all(0 <= int(p) <= 255 for p in parts)

    def test_default_port_value(self):
        """Default port is 18789 (Clawdbot Gateway default)."""
        assert DEFAULT_PORT == 18789

    def test_default_port_in_valid_range(self):
        """Default port should be in valid port range (1-65535)."""
        assert 1 <= DEFAULT_PORT <= 65535

    def test_default_port_above_privileged(self):
        """Default port should be above privileged ports (>1024)."""
        assert DEFAULT_PORT > 1024

    def test_default_use_ssl_is_false(self):
        """SSL is disabled by default for local connections."""
        assert DEFAULT_USE_SSL is False

    def test_default_timeout_value(self):
        """Default timeout is 30 seconds."""
        assert DEFAULT_TIMEOUT == 30

    def test_default_timeout_is_reasonable(self):
        """Default timeout should be between 5 and 120 seconds."""
        assert 5 <= DEFAULT_TIMEOUT <= 120

    def test_default_session_key_value(self):
        """Default session key is 'main' for direct-chat sessions."""
        assert DEFAULT_SESSION_KEY == "main"

    def test_default_session_key_is_nonempty(self):
        """Session key should not be empty."""
        assert len(DEFAULT_SESSION_KEY) > 0

    def test_default_strip_emojis_is_true(self):
        """Strip emojis by default for TTS compatibility."""
        assert DEFAULT_STRIP_EMOJIS is True


class TestConfigurationKeys:
    """Tests for CONF_* configuration key constants.

    These keys are used in config flow and options flow.
    They must remain stable for existing configurations to load.
    """

    def test_conf_host_key(self):
        """Host configuration key."""
        assert CONF_HOST == "host"

    def test_conf_port_key(self):
        """Port configuration key."""
        assert CONF_PORT == "port"

    def test_conf_token_key(self):
        """Token configuration key."""
        assert CONF_TOKEN == "token"

    def test_conf_use_ssl_key(self):
        """SSL configuration key."""
        assert CONF_USE_SSL == "use_ssl"

    def test_conf_timeout_key(self):
        """Timeout configuration key."""
        assert CONF_TIMEOUT == "timeout"

    def test_conf_session_key_key(self):
        """Session key configuration key."""
        assert CONF_SESSION_KEY == "session_key"

    def test_conf_strip_emojis_key(self):
        """Strip emojis configuration key."""
        assert CONF_STRIP_EMOJIS == "strip_emojis"

    def test_all_conf_keys_are_snake_case(self):
        """All configuration keys should use snake_case."""
        conf_keys = [
            CONF_HOST,
            CONF_PORT,
            CONF_TOKEN,
            CONF_USE_SSL,
            CONF_TIMEOUT,
            CONF_SESSION_KEY,
            CONF_STRIP_EMOJIS,
        ]
        for key in conf_keys:
            # snake_case: lowercase letters, numbers, and underscores only
            assert key == key.lower()
            assert all(c.isalnum() or c == "_" for c in key)


class TestConnectionStates:
    """Tests for STATE_* connection state constants.

    These states are used for connection status reporting.
    """

    def test_state_connected_value(self):
        """Connected state value."""
        assert STATE_CONNECTED == "connected"

    def test_state_disconnected_value(self):
        """Disconnected state value."""
        assert STATE_DISCONNECTED == "disconnected"

    def test_state_connecting_value(self):
        """Connecting state value."""
        assert STATE_CONNECTING == "connecting"

    def test_state_error_value(self):
        """Error state value."""
        assert STATE_ERROR == "error"

    def test_all_states_are_distinct(self):
        """All connection states must be distinct values."""
        states = [
            STATE_CONNECTED,
            STATE_DISCONNECTED,
            STATE_CONNECTING,
            STATE_ERROR,
        ]
        assert len(states) == len(set(states))


class TestProtocolVersion:
    """Tests for protocol version constants.

    These control Gateway protocol compatibility.
    """

    def test_protocol_min_version_value(self):
        """Minimum supported protocol version is 3."""
        assert PROTOCOL_MIN_VERSION == 3

    def test_protocol_max_version_value(self):
        """Maximum supported protocol version is 3."""
        assert PROTOCOL_MAX_VERSION == 3

    def test_protocol_version_relationship(self):
        """Minimum version must be <= maximum version."""
        assert PROTOCOL_MIN_VERSION <= PROTOCOL_MAX_VERSION

    def test_protocol_versions_are_positive(self):
        """Protocol versions must be positive integers."""
        assert PROTOCOL_MIN_VERSION > 0
        assert PROTOCOL_MAX_VERSION > 0


class TestClientIdentification:
    """Tests for CLIENT_* identification constants.

    These identify this integration to the Gateway server.
    """

    def test_client_id_value(self):
        """Client ID for Gateway handshake."""
        assert CLIENT_ID == "gateway-client"

    def test_client_display_name_value(self):
        """Human-readable client name."""
        assert CLIENT_DISPLAY_NAME == "Home Assistant Clawd"

    def test_client_version_value(self):
        """Client version string."""
        assert CLIENT_VERSION == "1.0.0"

    def test_client_version_is_semver_format(self):
        """Client version should follow semver format (x.y.z)."""
        parts = CLIENT_VERSION.split(".")
        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_client_platform_value(self):
        """Platform identifier."""
        assert CLIENT_PLATFORM == "python"

    def test_client_mode_value(self):
        """Client mode for backend operation."""
        assert CLIENT_MODE == "backend"


class TestConstantsIntegrity:
    """Meta-tests for constants module integrity."""

    def test_all_constants_are_immutable_types(self):
        """All constants should be immutable types (str, int, bool)."""
        constants = [
            DOMAIN,
            DEFAULT_HOST,
            DEFAULT_PORT,
            DEFAULT_USE_SSL,
            DEFAULT_TIMEOUT,
            DEFAULT_SESSION_KEY,
            DEFAULT_STRIP_EMOJIS,
            CONF_HOST,
            CONF_PORT,
            CONF_TOKEN,
            CONF_USE_SSL,
            CONF_TIMEOUT,
            CONF_SESSION_KEY,
            CONF_STRIP_EMOJIS,
            STATE_CONNECTED,
            STATE_DISCONNECTED,
            STATE_CONNECTING,
            STATE_ERROR,
            PROTOCOL_MIN_VERSION,
            PROTOCOL_MAX_VERSION,
            CLIENT_ID,
            CLIENT_DISPLAY_NAME,
            CLIENT_VERSION,
            CLIENT_PLATFORM,
            CLIENT_MODE,
        ]
        for const in constants:
            assert isinstance(const, (str, int, bool))
