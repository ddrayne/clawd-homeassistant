# Architecture

**Analysis Date:** 2026-01-25

## Pattern Overview

**Overall:** Layered event-driven gateway client integration

**Key Characteristics:**
- Integration layer provides Home Assistant conversation entity interface
- Client layer manages high-level agent request/response semantics
- Protocol layer handles low-level WebSocket communication with automatic reconnection
- Event-driven buffering model for asynchronous agent execution
- Async/await pattern throughout for non-blocking I/O

## Layers

**Home Assistant Integration Layer:**
- Purpose: Expose Clawdbot agent as a conversation entity within Home Assistant
- Location: `custom_components/clawd/__init__.py`, `custom_components/clawd/conversation.py`
- Contains: Configuration entry setup/teardown, conversation entity implementation, error handling
- Depends on: ClawdGatewayClient for agent communication
- Used by: Home Assistant's conversation platform and voice assistant pipeline

**Configuration & User Interface Layer:**
- Purpose: Handle user setup, configuration validation, and settings management
- Location: `custom_components/clawd/config_flow.py`
- Contains: Configuration flow steps, options flow, connection validation
- Depends on: ClawdGatewayClient for connection testing, voluptuous for form validation
- Used by: Home Assistant config entries system

**Client Layer (High-Level API):**
- Purpose: Provide semantic request/response API for agent interactions
- Location: `custom_components/clawd/gateway_client.py`
- Contains: ClawdGatewayClient class, AgentRun event buffering tracker
- Depends on: GatewayProtocol for WebSocket communication
- Used by: Conversation entity and config flow for agent requests

**Protocol Layer (Low-Level WebSocket):**
- Purpose: Manage WebSocket connection, handshake, authentication, message framing
- Location: `custom_components/clawd/gateway.py`
- Contains: GatewayProtocol class, connection loop, handshake logic, event dispatcher
- Depends on: websockets library for WebSocket communication
- Used by: ClawdGatewayClient for underlying transport

**Constants & Configuration:**
- Purpose: Define default values, configuration keys, protocol constants
- Location: `custom_components/clawd/const.py`
- Contains: Domain name, configuration defaults, protocol version bounds, client identification
- Depends on: None
- Used by: All other modules for consistent configuration keys

**Exception Hierarchy:**
- Purpose: Provide typed exception handling throughout the stack
- Location: `custom_components/clawd/exceptions.py`
- Contains: Base ClawdError and specialized exceptions for connection, auth, timeout, protocol, agent execution
- Depends on: None
- Used by: All layers for error handling and distinction

## Data Flow

**Conversation Request Flow:**

1. User sends message via Home Assistant voice/text interface
2. `ClawdConversationEntity._async_handle_message()` receives ConversationInput
3. Calls `ClawdGatewayClient.send_agent_request(user_message)`
4. Client sends agent request via `GatewayProtocol.send_request(method="agent", params={...})`
5. Protocol sends JSON request over WebSocket and waits for acknowledgment response
6. Response contains runId identifying the agent execution
7. Client creates `AgentRun` tracker for this runId and registers it
8. Protocol's receive loop processes incoming events and dispatches them
9. Agent events are buffered in `AgentRun.add_output()` (handles cumulative text updates)
10. When agent completes (status="ok" or phase="end"), `AgentRun.set_complete()` sets event
11. Client awaits completion with configured timeout, then returns buffered response
12. Conversation entity receives response, optionally strips emojis, creates intent response
13. Response is returned to Home Assistant and converted to speech

**State Management:**

- `hass.data[DOMAIN][entry_id]` stores the ClawdGatewayClient instance (singleton per configured Gateway)
- `ClawdGatewayClient._agent_runs` dict tracks in-flight agent executions by runId
- `GatewayProtocol._pending_requests` dict tracks in-flight protocol requests by request_id
- `GatewayProtocol._connected_event` coordinates connection readiness for callers
- Agent runs auto-cleanup when complete or on timeout

## Key Abstractions

**ClawdConversationEntity:**
- Purpose: Implement Home Assistant's conversation entity protocol
- Examples: `custom_components/clawd/conversation.py` lines 52-157
- Pattern: Extends conversation.ConversationEntity, handles ConversationInput/ConversationResult marshalling, emoji stripping for TTS

**ClawdGatewayClient:**
- Purpose: High-level request/response API hiding event buffering complexity
- Examples: `custom_components/clawd/gateway_client.py` lines 70-270
- Pattern: Simple send_agent_request() interface that abstracts event buffering and completion tracking, manages AgentRun lifecycle

**AgentRun:**
- Purpose: Track execution of a single agent request and buffer its output events
- Examples: `custom_components/clawd/gateway_client.py` lines 18-68
- Pattern: Accumulates cumulative text updates, exposes completion event for wait_for semantics, handles both old-style (status) and new-style (phase) completion signals

**GatewayProtocol:**
- Purpose: WebSocket protocol implementation with automatic reconnection
- Examples: `custom_components/clawd/gateway.py` lines 31-434
- Pattern: Connection loop with exponential backoff retry (5s), event-based handshake, request/response correlation via UUID, event handler registry

**Emoji Stripping:**
- Purpose: Clean TTS output by removing emoji characters
- Examples: `custom_components/clawd/conversation.py` lines 22-38
- Pattern: Regex-based Unicode range matching, applied conditionally based on config flag

## Entry Points

**Integration Setup:**
- Location: `custom_components/clawd/__init__.py` async_setup_entry()
- Triggers: Home Assistant config entry creation (from config flow)
- Responsibilities: Create ClawdGatewayClient instance, establish connection, store in hass.data, forward setup to conversation platform

**Integration Teardown:**
- Location: `custom_components/clawd/__init__.py` async_unload_entry()
- Triggers: Home Assistant unload event, config entry removal
- Responsibilities: Disconnect client, clean up hass.data, unload conversation platform

**Conversation Message Handler:**
- Location: `custom_components/clawd/conversation.py` ClawdConversationEntity._async_handle_message()
- Triggers: User message from Home Assistant voice/chat interface
- Responsibilities: Extract message text, call gateway client, handle errors, format response for TTS/display

**Configuration Entry Point:**
- Location: `custom_components/clawd/config_flow.py` ClawdConfigFlow.async_step_user()
- Triggers: User adds integration via UI
- Responsibilities: Collect host/port/token/options, validate connection, prevent duplicates, warn on insecure remote connections

## Error Handling

**Strategy:** Layered exception handling with distinction between recoverable and fatal errors

**Patterns:**

- **Connection Errors** (GatewayConnectionError): Logged and reported to user, trigger automatic reconnection in protocol layer
- **Authentication Errors** (GatewayAuthenticationError): Logged, fatal - no retry, user must reconfigure token
- **Timeout Errors** (GatewayTimeoutError): Logged as warning, user-facing message suggests increasing timeout or checking Gateway
- **Agent Execution Errors** (AgentExecutionError): Logged, indicates agent failed, user-facing message suggests retry
- **Protocol Errors** (ProtocolError): Logged, fatal - indicates version mismatch or protocol violation, no retry
- **Broad Exception Handling**: Conversation handler has catch-all for unexpected errors to prevent voice assistant crash

Error propagation: Config flow validates connections before accepting config, conversation handler catches all exceptions and converts to user-facing error responses.

## Cross-Cutting Concerns

**Logging:** Standard Python logging module with loggers per module (`_LOGGER = logging.getLogger(__name__)`). Levels: DEBUG for message details, INFO for lifecycle events, WARNING for recoverable issues, ERROR for failures.

**Validation:** Config flow uses voluptuous library for form validation (host string, port 1-65535 int, timeout 5-300 int). Connection validation in config_flow.validate_connection() tests actual Gateway connection before accepting config.

**Authentication:** Token stored in Home Assistant config entry (encrypted at rest), included in WebSocket handshake auth params if provided. Token required for remote connections, optional for localhost.

**Connection Management:** GatewayProtocol._connection_loop() maintains persistent connection with automatic reconnection on failure (5s backoff). Handshake validates protocol version compatibility (min/max version matching). Ping/pong every 30s to detect stale connections.

**Message Correlation:** Protocol uses UUID-based request IDs to match responses with pending requests. Agent requests tracked by runId in AgentRun dict for event buffering.

**TTS Optimization:** Emoji regex strips common emoji Unicode ranges before text-to-speech to avoid awkward pronunciations. Original text preserved in chat history for display.
