# Coding Conventions

**Analysis Date:** 2026-01-25

## Naming Patterns

**Files:**
- Snake_case for module names: `gateway_client.py`, `config_flow.py`, `gateway.py`
- Special convention for entry point: `__init__.py` for package initialization
- Single responsibility per file: protocol layer, client layer, config layer kept separate

**Functions:**
- Snake_case for function names: `async_setup_entry()`, `send_agent_request()`, `strip_emojis()`
- Async functions prefixed with `async_`: `async_setup_entry()`, `async_unload_entry()`, `async_reload_entry()`, `async_step_user()`, `async_setup_entry()` for conversation platform
- Helper/private functions prefixed with underscore: `_async_handle_message()`, `_handle_agent_event()`, `_connection_loop()`, `_receive_loop()`, `_handshake()`

**Variables:**
- Snake_case for local variables: `user_message`, `response_text`, `agent_run`, `request_id`
- Constants in UPPER_SNAKE_CASE: `DOMAIN`, `DEFAULT_HOST`, `PROTOCOL_MIN_VERSION`, `CLIENT_ID`
- Protected attributes prefixed with underscore: `self._config_entry`, `self._gateway_client`, `self._full_text`, `self._websocket`
- Logger follows convention: `_LOGGER = logging.getLogger(__name__)`

**Types:**
- Type hints on function signatures: `async def send_agent_request(self, message: str, idempotency_key: str | None = None) -> str:`
- Union types use pipe syntax (Python 3.10+): `str | None`, `dict[str, Any]`, `asyncio.Future | None`
- Class attributes typed with type hints: `_attr_has_entity_name = True`, `_attr_name = "Clawd"`

**Classes:**
- PascalCase for class names: `ClawdError`, `GatewayConnectionError`, `AgentExecutionError`, `GatewayProtocol`, `ClawdGatewayClient`, `AgentRun`, `ClawdConversationEntity`
- Domain-specific naming for Home Assistant integration classes: `ClawdConfigFlow`, `ClawdOptionsFlowHandler`, `ClawdConversationEntity`

## Code Style

**Formatting:**
- No explicit formatter configured; follows PEP 8 conventions implicitly
- Line length not strictly enforced but modules kept readable (longest logical lines ~90 chars)
- Import organization follows PEP 8: standard library, third-party, local imports
- Docstrings use triple quotes with description format

**Linting:**
- Pylint is referenced via disable comments: `# pylint: disable=broad-except` used in exception handling
- Broad exception catches justified with disable comment to allow for resilient error handling in async/connection code
- No strict configuration file detected; relies on Home Assistant ecosystem conventions

## Import Organization

**Order:**
1. Standard library imports: `logging`, `asyncio`, `json`, `uuid`, `re`, `time`, `typing`
2. Third-party imports: `websockets`, `voluptuous`, `homeassistant` modules
3. Local imports: `.const`, `.exceptions`, `.gateway`, `.gateway_client`

**Path Aliases:**
- Relative imports used within package: `from .const import DOMAIN`, `from .exceptions import GatewayConnectionError`
- Absolute imports for external packages: `from homeassistant.config_entries import ConfigEntry`
- No import aliases observed; full paths maintained for clarity

**Example (from `config_flow.py`):**
```python
import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_HOST, CONF_PORT, CONF_TOKEN, CONF_TIMEOUT
from homeassistant.core import HomeAssistant, callback
from homeassistant.data_entry_flow import FlowResult

from .const import (
    CONF_SESSION_KEY,
    CONF_STRIP_EMOJIS,
    CONF_USE_SSL,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_SESSION_KEY,
    DEFAULT_STRIP_EMOJIS,
    DEFAULT_TIMEOUT,
    DEFAULT_USE_SSL,
    DOMAIN,
)
from .exceptions import (
    GatewayAuthenticationError,
    GatewayConnectionError,
    GatewayTimeoutError,
)
from .gateway_client import ClawdGatewayClient
```

## Error Handling

**Patterns:**
- Custom exception hierarchy with base class `ClawdError` in `exceptions.py`
- Specific exception types for different failure modes: `GatewayConnectionError`, `GatewayAuthenticationError`, `GatewayTimeoutError`, `AgentExecutionError`, `ProtocolError`
- Exception chaining with `from err` to preserve stack traces: `raise GatewayConnectionError("Connection closed") from err`
- Broad exception catches (`except Exception`) with `pylint: disable=broad-except` comment used strategically in resilient code paths (connection loops, message handling)

**Example (from `gateway.py`):**
```python
except asyncio.TimeoutError as err:
    raise GatewayConnectionError(
        "Handshake timeout"
    ) from err

except json.JSONDecodeError as err:
    raise ProtocolError(
        "Invalid JSON in handshake response"
    ) from err

except Exception as err:  # pylint: disable=broad-except
    _LOGGER.error(
        "Unexpected error in connection: %s",
        err,
        exc_info=True,
    )
```

## Logging

**Framework:** Python standard library `logging`

**Patterns:**
- Logger created per module: `_LOGGER = logging.getLogger(__name__)`
- Log levels used strategically:
  - `_LOGGER.debug()` for detailed event tracking: "Added 10 new chars to run-123 (total: 250)"
  - `_LOGGER.info()` for lifecycle events: "Setting up Clawd integration", "Connected to Gateway successfully"
  - `_LOGGER.warning()` for recoverable issues: "Non-cumulative text update", "Connection timeout"
  - `_LOGGER.error()` for failures: "Failed to connect to Gateway: %s"
  - `_LOGGER.exception()` for unexpected errors with traceback: `_LOGGER.exception("Unexpected error in message handling")`

**Example (from `gateway_client.py`):**
```python
_LOGGER.debug(
    "Added %d new chars to %s (total: %d)",
    len(new_text),
    self.run_id,
    len(self._full_text),
)
```

## Comments

**When to Comment:**
- Regex patterns explained for clarity: `# Emoji pattern for removal from TTS`
- Protocol handling decisions documented: `# Gateway sends cumulative text, not incremental`
- Non-obvious workarounds explained: `# This is cumulative text, extract only new portion`
- Event processing logic clarified: `# Event for unknown run, might be from previous session`
- Business rules documented: `# Old-style completion` vs `# New-style completion via phase`

**JSDoc/TSDoc:**
- Not applicable (Python project); uses Python docstrings instead
- Docstrings follow Google-style format with Args, Returns, Raises sections
- Example from `gateway_client.py`:
```python
async def send_agent_request(
    self, message: str, idempotency_key: str | None = None
) -> str:
    """
    Send agent request and return complete response.

    Handles event buffering automatically.

    Args:
        message: User message to send to agent
        idempotency_key: Optional idempotency key for safe retries

    Returns:
        Complete response from agent

    Raises:
        GatewayTimeoutError: If request times out
        AgentExecutionError: If agent execution fails
    """
```

## Function Design

**Size:**
- Typical functions 10-50 lines of code
- Larger functions (100+ lines) used for complex state machines like `_connection_loop()` (80 lines) and `_receive_loop()` (45 lines)
- Public methods kept concise by delegating to private helper methods: `connect()` delegates to `_connection_loop()`

**Parameters:**
- Type hints on all parameters
- Sensible defaults used: `use_ssl: bool = False`, `timeout: int = 30`, `idempotency_key: str | None = None`
- Multiple related parameters grouped in config dictionaries for setup: `data: dict[str, Any]`

**Return Values:**
- Explicit return types declared: `-> bool`, `-> str`, `-> dict[str, Any]`, `-> None`
- Async functions return awaitable values: `async def connect(self) -> None:`, `async def send_agent_request(...) -> str:`
- Raises clauses in docstrings document exceptions: `Raises: GatewayTimeoutError`

**Example (from `gateway_client.py`):**
```python
def add_output(self, output: str) -> None:
    """Add output to buffer. Gateway sends cumulative text, extract only new chars."""
    if not output:
        return

    if output.startswith(self._full_text):
        new_text = output[len(self._full_text) :]
        if new_text:
            self._full_text = output
            _LOGGER.debug(...)
    else:
        _LOGGER.warning(...)
        self._full_text = output
```

## Module Design

**Exports:**
- No explicit `__all__` declarations; all public classes and functions are module-level accessible
- Modules organized by responsibility: protocol layer, client layer, conversation layer, config layer

**Barrel Files:**
- No barrel files (`__init__.py` with re-exports) used; package `__init__.py` contains integration setup logic only
- Direct imports preferred: `from .gateway_client import ClawdGatewayClient`

**Organization:**
- `const.py`: Configuration constants and defaults
- `exceptions.py`: Exception class hierarchy
- `gateway.py`: Low-level WebSocket protocol implementation (`GatewayProtocol`)
- `gateway_client.py`: High-level API client (`ClawdGatewayClient`, `AgentRun`)
- `conversation.py`: Home Assistant conversation entity integration
- `config_flow.py`: Home Assistant configuration UI
- `__init__.py`: Integration setup/teardown lifecycle

---

*Convention analysis: 2026-01-25*
