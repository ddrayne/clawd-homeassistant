# Testing Patterns

**Analysis Date:** 2026-01-25

## Test Framework

**Runner:**
- No test framework detected in codebase
- No pytest, unittest, or other test runner configuration files present
- No test files found in repository (`*_test.py`, `test_*.py`, `*_spec.py` patterns absent)

**Assertion Library:**
- Not applicable (no testing framework configured)

**Run Commands:**
```bash
# No automated tests configured
# Home Assistant integrations typically tested via:
# - Manual UI testing in Home Assistant instance
# - Type checking with mypy/pyright (not configured)
# - Linting with pylint (referenced in disable comments only)
```

## Test File Organization

**Location:**
- No test directory structure present
- Production code located in `custom_components/clawd/`
- No parallel test directory (`tests/`, `test/`) created

**Naming:**
- Not applicable (no test files present)

**Structure:**
- Not applicable (no test infrastructure)

## Test Coverage Status

**Current State:**
- **No automated tests** in the codebase
- Testing relies on manual verification and Home Assistant integration testing

**Integration Testing Approach:**
- Manual testing through Home Assistant UI
- Gateway connection validation in `config_flow.py` via `validate_connection()` function (used during config setup)
- Health check endpoint tested during configuration: `await client.health()`

## Manual Testing Patterns Observed

**Connection Validation (in `config_flow.py`):**
```python
async def validate_connection(
    hass: HomeAssistant, data: dict[str, Any]
) -> dict[str, Any]:
    """Validate the Gateway connection."""
    client = ClawdGatewayClient(
        host=data[CONF_HOST],
        port=data[CONF_PORT],
        token=data.get(CONF_TOKEN),
        use_ssl=data.get(CONF_USE_SSL, DEFAULT_USE_SSL),
        timeout=data.get(CONF_TIMEOUT, DEFAULT_TIMEOUT),
        session_key=data.get(CONF_SESSION_KEY, DEFAULT_SESSION_KEY),
    )

    try:
        # Try to connect
        await client.connect()

        # Test with a health check
        await client.health()

        # Return validated data
        return {"title": f"Clawd Gateway ({data[CONF_HOST]})"}

    finally:
        await client.disconnect()
```

This validation runs when user submits configuration, catching connection/auth issues before saving config.

## Mocking

**Framework:**
- Not applicable (no test framework)

**Patterns:**
- No mocking infrastructure present
- Codebase uses real connections to Gateway for testing (manual)
- WebSocket handling in `gateway.py` allows testing with real Gateway instance

**Testing Strategy:**
- **Integration-focused**: Real WebSocket connection required for testing
- **Dependency injection via constructor**: `ClawdGatewayClient` accepts `GatewayProtocol` via constructor, allowing test Gateway implementations to be injected
- **Event handler registration**: `GatewayProtocol.on_event()` allows handler registration for testing event flows

## What Could Be Mocked

**For Future Test Suite:**

**Mock candidates (if testing framework added):**
- `websockets.connect()` to simulate various connection scenarios
- Gateway responses in `_handle_message()` for event processing paths
- Home Assistant conversation entity methods for response handling

**What should NOT be mocked:**
- Core protocol logic in `_connection_loop()` - requires real state transitions
- Event buffering in `AgentRun` class - timing-dependent behavior
- Error conditions and retry logic - needs realistic timeout simulation

## Async Testing Considerations

**No existing test patterns**, but codebase is heavily async:

**Async patterns that would need testing:**
- `async def connect()` - connection lifecycle
- `async def send_agent_request()` - request/response correlation
- `asyncio.wait_for()` - timeout handling
- `asyncio.Event` - event signaling between coroutines
- `_connection_loop()` - reconnection logic

**Testing approach would use:**
- `pytest` with `pytest-asyncio` plugin for async test support
- `asyncio.wait_for()` with timeout for testing slow operations
- Mock async context managers for WebSocket alternatives

## Test Infrastructure Gaps

**Critical missing:**
- [ ] No unit test suite (all testing manual)
- [ ] No test runner configured
- [ ] No fixtures for test data
- [ ] No mocking framework
- [ ] No CI/CD test automation
- [ ] No coverage tracking

**Configuration needed to add tests:**
- `pytest.ini` or `pyproject.toml` with pytest config
- `conftest.py` for shared fixtures
- `tests/` directory with test modules
- Mock Gateway implementation or fixtures
- CI workflow (GitHub Actions, etc.) to run tests

## Testing Recommendations

**Phase 1: Unit Tests (Highest Priority)**
- `tests/test_gateway.py`: Test `GatewayProtocol` message handling, handshake, reconnection logic
- `tests/test_gateway_client.py`: Test `AgentRun` buffering, `send_agent_request()` response correlation
- `tests/test_conversation.py`: Test emoji stripping, message handling, error responses
- Focus on error paths: timeouts, disconnections, malformed responses

**Phase 2: Integration Tests**
- Test full request/response flow with mock Gateway server
- Test connection lifecycle (connect, disconnect, reconnect)
- Test event handler registration and dispatch

**Phase 3: Config Flow Tests**
- Test configuration validation path in `config_flow.py`
- Test error handling for invalid credentials, timeouts
- Test Home Assistant integration setup/teardown

---

*Testing analysis: 2026-01-25*
