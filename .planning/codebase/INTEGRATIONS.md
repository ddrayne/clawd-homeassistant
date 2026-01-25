# External Integrations

**Analysis Date:** 2026-01-25

## APIs & External Services

**Clawdbot Gateway:**
- Service: Clawdbot Gateway WebSocket API
  - What it's used for: Remote execution of agent queries with full Clawdbot capabilities (Gmail, Calendar, GitHub, Spotify, Obsidian, file access, web browsing, custom skills)
  - SDK/Client: Custom WebSocket protocol implementation in `custom_components/clawd/gateway.py`
  - Auth: Token-based authentication via optional Gateway token
  - Connection: WebSocket (ws:// or wss://) at configurable host:port (default: ws://127.0.0.1:18789)
  - Protocol Version: 3 (client supports min: 3, max: 3) - defined in `custom_components/clawd/const.py`

**Home Assistant Conversation Integration:**
- Service: Home Assistant's built-in Assist conversation platform
  - What it's used for: Receives voice commands and text input from Home Assistant voice assistant
  - SDK/Client: Home Assistant `conversation.ConversationEntity` abstract class
  - Implementation: `custom_components/clawd/conversation.py::ClawdConversationEntity`
  - Connection: Local in-process through Home Assistant's conversation platform

## Data Storage

**Databases:**
- None - This is a stateless integration
  - No persistent data storage beyond Home Assistant's config entries (encrypted)
  - Chat history managed by Home Assistant's ChatLog entity in memory

**File Storage:**
- None - Local file storage not used
  - Delegated to Clawdbot for file operations via agent requests

**Caching:**
- None - No explicit caching layer
  - Gateway connections maintained in memory in `custom_components/clawd/__init__.py::hass.data[DOMAIN]`
  - Agent run tracking cached temporarily during request in `custom_components/clawd/gateway_client.py::ClawdGatewayClient._agent_runs`

## Authentication & Identity

**Auth Provider:**
- Token-based custom authentication to Clawdbot Gateway
  - Implementation: `custom_components/clawd/gateway.py::GatewayProtocol._handshake()`
  - Client identification: Hardcoded client metadata
    - Client ID: "gateway-client"
    - Display Name: "Home Assistant Clawd"
    - Version: "1.0.0"
    - Platform: "python"
    - Mode: "backend"
  - Token storage: Home Assistant encrypts tokens at rest via config entries
  - Validation: Config flow in `custom_components/clawd/config_flow.py` performs health check on Gateway

**Security:**
- Warnings: Non-SSL remote connections logged as warnings in config flow
- SSL/TLS: Configurable via `use_ssl` flag; WSS (wss://) protocol used when enabled
- SSH Tunnels: Documented alternative for secure remote access

## Monitoring & Observability

**Error Tracking:**
- None - No external error tracking service
  - Errors logged locally via Python logging module
  - Custom exception hierarchy in `custom_components/clawd/exceptions.py`:
    - `ClawdError` - Base exception
    - `GatewayConnectionError` - Connection failures
    - `GatewayAuthenticationError` - Auth failures
    - `GatewayTimeoutError` - Request timeouts
    - `AgentExecutionError` - Agent execution failures
    - `ProtocolError` - Protocol violations

**Logs:**
- Python logging to Home Assistant logs
  - Logger: `_LOGGER = logging.getLogger(__name__)` in each module
  - Levels: DEBUG (protocol details), INFO (connections), WARNING (issues), ERROR (failures)
  - Key logging points:
    - Connection lifecycle in `gateway.py`
    - Agent request/response in `gateway_client.py`
    - Message handling in `conversation.py`

## CI/CD & Deployment

**Hosting:**
- Home Assistant installation (self-hosted or managed instance)
  - Deployment method: HACS integration or manual custom components directory
  - No cloud services required

**CI Pipeline:**
- Not detected - No CI/CD configuration files found

**Package Distribution:**
- HACS (Home Assistant Community Store) - Recommended distribution channel
  - Repository: https://github.com/ddrayne/clawd-homeassistant
  - Metadata: `hacs.json` specifies integration name and Home Assistant version requirement

## Environment Configuration

**Required env vars:**
- None for Home Assistant integration
- Alternative (Clawdbot side): `CLAWDBOT_GATEWAY_TOKEN` environment variable on Gateway host
  - Retrieved via `clawdbot doctor --generate-gateway-token` or `echo $CLAWDBOT_GATEWAY_TOKEN`

**Configuration via UI:**
- Gateway Host - Default: 127.0.0.1
- Gateway Port - Default: 18789 (range: 1-65535)
- Gateway Token - Optional for remote connections
- Use SSL - Default: false (recommended true for remote)
- Agent Timeout - Default: 30 seconds (range: 5-300)
- Session Key - Default: "main"
- Strip Emojis - Default: true

**Secrets location:**
- Home Assistant encrypted config entries storage
  - Token not stored in plain text files
  - Accessible via Home Assistant UI only

## Webhooks & Callbacks

**Incoming:**
- None - No incoming webhooks
  - Gateway initiates WebSocket connection, Home Assistant responds to requests
  - Bidirectional event-driven communication via WebSocket

**Outgoing:**
- None - No outgoing webhooks
  - All communication is request-response through WebSocket
  - Gateway events handled via registered event handlers in `custom_components/clawd/gateway.py::on_event()`

## Gateway Protocol Details

**Message Types:**
- Request (req): Client sends request, waits for response
  - Structure: `{"type": "req", "id": <uuid>, "method": <method>, "params": <dict>}`
  - Methods: "connect", "agent", "health", "status"

- Response (res): Gateway responds to request
  - Structure: `{"type": "res", "id": <uuid>, "ok": <bool>, "error": <str>, "payload": <dict>}`

- Event (event): Gateway pushes events to client
  - Structure: `{"type": "event", "event": <name>, "payload": <dict>}`
  - Event types: "agent" (agent execution events)

**Agent Request Flow:**
1. Client sends agent request with message, sessionKey, idempotencyKey
2. Gateway acknowledges with runId
3. Gateway sends agent events with intermediate output and status updates
4. Client buffers output and watches for completion status
5. Client returns complete response text or summary

**Idempotency:**
- Agent requests include idempotency key (UUID v4) for safe retries
- Generated by `custom_components/clawd/gateway_client.py::send_agent_request()` if not provided

---

*Integration audit: 2026-01-25*
