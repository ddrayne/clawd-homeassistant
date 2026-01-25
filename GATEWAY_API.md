# Clawdbot Gateway API Documentation

This document provides comprehensive documentation of the Clawdbot Gateway API for developers building integrations.

## Table of Contents

- [Overview](#overview)
- [Authentication](#authentication)
- [WebSocket Protocol](#websocket-protocol)
- [REST Endpoints](#rest-endpoints)
- [Agent Execution](#agent-execution)
- [Sessions](#sessions)
- [Cron & Scheduling](#cron--scheduling)
- [Message Routing](#message-routing)
- [Browser Control](#browser-control)
- [Nodes](#nodes)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)

## Overview

The Clawdbot Gateway provides a unified API for interacting with your AI agent. It exposes both REST and WebSocket endpoints for real-time communication.

**Default Configuration:**
- Protocol: `ws://` (non-SSL) or `wss://` (SSL)
- Port: `18789`
- Bind: `localhost` (default), `lan` (local network), or `0.0.0.0` (all interfaces)

**Base URLs:**
```
http://localhost:18789      # HTTP (REST)
ws://localhost:18789        # WebSocket
```

For remote connections with SSL:
```
https://gateway.example.com:18789   # HTTPS
wss://gateway.example.com:18789     # Secure WebSocket
```

## Authentication

### Token-Based Auth

The Gateway supports bearer token authentication for non-localhost connections.

**Header:**
```
Authorization: Bearer YOUR_GATEWAY_TOKEN
```

**Generating a Token:**
```bash
# Generate new token
clawdbot doctor --generate-gateway-token

# Retrieve existing token from environment
echo $CLAWDBOT_GATEWAY_TOKEN
```

**Starting Gateway with LAN Binding:**
```bash
# Allow connections from local network
clawdbot gateway --bind lan

# Allow from all interfaces (use with caution)
clawdbot gateway --bind 0.0.0.0
```

**Security Notes:**
- Localhost connections (127.0.0.1) may not require authentication depending on config
- Always use SSL/TLS for remote connections
- Token provides full access to your agent - keep it secret
- Consider using SSH tunnels as an alternative to exposing the gateway

## WebSocket Protocol

The primary method for real-time agent communication.

### Connection

**Endpoint:** `/gateway/ws/agent`

**Connection URL:**
```
ws://localhost:18789/gateway/ws/agent?sessionKey=main
```

**Query Parameters:**
- `sessionKey` (optional): Target session (default: `main`)

**Example (JavaScript):**
```javascript
const ws = new WebSocket('ws://localhost:18789/gateway/ws/agent?sessionKey=main', {
  headers: {
    'Authorization': 'Bearer YOUR_TOKEN'
  }
});
```

**Example (Python):**
```python
import websockets
import json

async def connect_gateway():
    uri = "ws://localhost:18789/gateway/ws/agent?sessionKey=main"
    headers = {"Authorization": "Bearer YOUR_TOKEN"}
    
    async with websockets.connect(uri, extra_headers=headers) as ws:
        # Send message
        await ws.send(json.dumps({
            "type": "message",
            "text": "Hello, Clawd!"
        }))
        
        # Receive response
        response = await ws.recv()
        data = json.loads(response)
        print(data)
```

### Message Format

**Client → Gateway:**
```json
{
  "type": "message",
  "text": "Your query here",
  "options": {
    "model": "anthropic/claude-opus-4-5",
    "thinking": "high",
    "timeoutMs": 30000
  }
}
```

**Fields:**
- `type`: Always `"message"` for queries
- `text`: The user input/query
- `options` (optional):
  - `model`: Override default model
  - `thinking`: Reasoning mode (`"off"`, `"low"`, `"medium"`, `"high"`)
  - `timeoutMs`: Request timeout in milliseconds

**Gateway → Client (Streaming):**

Responses are streamed as JSON objects. Each message has a `type` field.

**Token Stream:**
```json
{
  "type": "token",
  "content": "Hello! ",
  "index": 0
}
```

**Complete Response:**
```json
{
  "type": "response",
  "content": "Hello! How can I help you today?",
  "usage": {
    "inputTokens": 150,
    "outputTokens": 45,
    "cacheReadTokens": 0,
    "cacheWriteTokens": 0
  },
  "model": "anthropic/claude-sonnet-4-5",
  "sessionKey": "main"
}
```

**Error:**
```json
{
  "type": "error",
  "error": "Timeout waiting for agent response",
  "code": "TIMEOUT"
}
```

### Message Types

| Type | Direction | Description |
|------|-----------|-------------|
| `message` | Client → Gateway | User query |
| `token` | Gateway → Client | Streaming response token |
| `response` | Gateway → Client | Complete response |
| `error` | Gateway → Client | Error occurred |
| `ping` | Both | Keepalive ping |
| `pong` | Both | Keepalive pong |

### Keepalive

Send periodic pings to maintain connection:

```json
{
  "type": "ping"
}
```

Gateway responds with:
```json
{
  "type": "pong"
}
```

Recommended interval: 30-60 seconds

## REST Endpoints

### Health Check

**GET** `/health`

Check if Gateway is running.

**Response:**
```json
{
  "status": "ok",
  "version": "2026.1.21-2",
  "uptime": 3600
}
```

### Status

**GET** `/status`

Get detailed Gateway status.

**Response:**
```json
{
  "ok": true,
  "gateway": {
    "version": "2026.1.21-2",
    "mode": "local",
    "bind": "lan",
    "port": 18789
  },
  "agents": {
    "main": {
      "status": "ready",
      "model": "anthropic/claude-sonnet-4-5"
    }
  },
  "channels": ["telegram", "whatsapp", "discord"]
}
```

### Configuration

**GET** `/config`

Retrieve Gateway configuration (requires auth).

**Response:**
```json
{
  "ok": true,
  "config": {
    "gateway": {
      "mode": "local",
      "bind": "lan"
    },
    "agents": {...},
    "channels": {...}
  }
}
```

## Agent Execution

### Send Message (HTTP)

**POST** `/agent/message`

Send a single message to the agent and wait for complete response.

**Request Body:**
```json
{
  "text": "What's the weather like today?",
  "sessionKey": "main",
  "options": {
    "model": "anthropic/claude-sonnet-4-5",
    "thinking": "low",
    "timeoutMs": 30000
  }
}
```

**Response:**
```json
{
  "ok": true,
  "response": "The weather today is sunny with a high of 72°F...",
  "usage": {
    "inputTokens": 120,
    "outputTokens": 85
  },
  "sessionKey": "main",
  "duration": 8234
}
```

**Error Response:**
```json
{
  "ok": false,
  "error": "Timeout waiting for agent response",
  "code": "TIMEOUT"
}
```

## Sessions

### List Sessions

**GET** `/sessions`

List all active sessions.

**Query Parameters:**
- `limit` (optional): Max sessions to return
- `activeMinutes` (optional): Only sessions active in last N minutes

**Response:**
```json
{
  "ok": true,
  "sessions": [
    {
      "sessionKey": "main",
      "agentId": "main",
      "lastActive": "2026-01-25T20:30:00Z",
      "messageCount": 145
    },
    {
      "sessionKey": "voice-assistant",
      "agentId": "main",
      "lastActive": "2026-01-25T20:25:00Z",
      "messageCount": 23
    }
  ]
}
```

### Get Session History

**GET** `/sessions/{sessionKey}/history`

Retrieve conversation history for a session.

**Query Parameters:**
- `limit` (optional): Number of messages (default: 50)
- `includeTools` (optional): Include tool calls (default: false)

**Response:**
```json
{
  "ok": true,
  "sessionKey": "main",
  "messages": [
    {
      "role": "user",
      "content": "What's the weather?",
      "timestamp": "2026-01-25T20:30:00Z"
    },
    {
      "role": "assistant",
      "content": "The weather is sunny...",
      "timestamp": "2026-01-25T20:30:08Z"
    }
  ]
}
```

### Send to Session

**POST** `/sessions/{sessionKey}/send`

Send a message to a specific session.

**Request Body:**
```json
{
  "message": "Check my calendar for today",
  "timeoutSeconds": 30
}
```

**Response:**
```json
{
  "ok": true,
  "response": "You have 3 meetings today..."
}
```

### Spawn Sub-Agent

**POST** `/sessions/spawn`

Spawn a background agent task.

**Request Body:**
```json
{
  "task": "Research Edinburgh restaurants and email me the results",
  "agentId": "main",
  "cleanup": "delete",
  "label": "restaurant-research",
  "timeoutSeconds": 300
}
```

**Options:**
- `task`: Task description
- `agentId` (optional): Target agent
- `cleanup`: `"delete"` or `"keep"` session after completion
- `label` (optional): Human-readable label
- `timeoutSeconds` (optional): Max execution time

**Response:**
```json
{
  "ok": true,
  "sessionKey": "spawn-abc123",
  "label": "restaurant-research",
  "status": "running"
}
```

**Checking Status:**
```
GET /sessions/spawn-abc123/status
```

### Session Status

**GET** `/sessions/{sessionKey}/status`

Get usage statistics for a session.

**Response:**
```json
{
  "ok": true,
  "sessionKey": "main",
  "usage": {
    "totalTokens": 125430,
    "estimatedCost": 0.42,
    "messageCount": 145
  },
  "model": "anthropic/claude-sonnet-4-5"
}
```

## Cron & Scheduling

### List Cron Jobs

**GET** `/cron/list`

List all scheduled cron jobs.

**Response:**
```json
{
  "ok": true,
  "jobs": [
    {
      "jobId": "reminder-123",
      "schedule": "*/30 * * * *",
      "text": "Check email for urgent messages",
      "enabled": true,
      "nextRun": "2026-01-25T21:00:00Z"
    }
  ]
}
```

### Add Cron Job

**POST** `/cron/add`

Schedule a new cron job.

**Request Body:**
```json
{
  "schedule": "0 9 * * *",
  "text": "Daily morning briefing: weather, calendar, top news",
  "contextMessages": 3
}
```

**Options:**
- `schedule`: Cron expression (or `"@hourly"`, `"@daily"`, etc.)
- `text`: Task to execute
- `contextMessages` (optional): Include last N messages as context (0-10)

**Response:**
```json
{
  "ok": true,
  "jobId": "cron-xyz789",
  "nextRun": "2026-01-26T09:00:00Z"
}
```

### Remove Cron Job

**DELETE** `/cron/{jobId}`

Delete a scheduled job.

**Response:**
```json
{
  "ok": true,
  "removed": "cron-xyz789"
}
```

### Run Cron Job

**POST** `/cron/{jobId}/run`

Manually trigger a cron job.

**Request Body:**
```json
{
  "mode": "now"
}
```

**Response:**
```json
{
  "ok": true,
  "executed": true,
  "response": "..."
}
```

## Message Routing

### Send Message (Channel)

**POST** `/message/send`

Send a message through a configured channel (Telegram, WhatsApp, Discord, etc.).

**Request Body:**
```json
{
  "channel": "telegram",
  "target": "7527535418",
  "message": "Hello from the Gateway!",
  "asVoice": false
}
```

**Options:**
- `channel`: Channel name (`telegram`, `whatsapp`, `discord`, `signal`)
- `target`: User ID or phone number
- `message`: Message text
- `asVoice` (optional): Send as voice message
- `filePath` (optional): Attachment path
- `replyTo` (optional): Message ID to reply to

**Response:**
```json
{
  "ok": true,
  "messageId": "1234",
  "chatId": "7527535418"
}
```

## Browser Control

### Open URL

**POST** `/browser/open`

Open a URL in controlled browser.

**Request Body:**
```json
{
  "targetUrl": "https://example.com",
  "profile": "clawd"
}
```

### Take Screenshot

**POST** `/browser/screenshot`

Capture browser screenshot.

**Request Body:**
```json
{
  "targetId": "tab-123",
  "fullPage": true
}
```

**Response:**
```json
{
  "ok": true,
  "screenshot": "data:image/png;base64,..."
}
```

### Browser Action

**POST** `/browser/act`

Perform browser action (click, type, etc.).

**Request Body:**
```json
{
  "request": {
    "kind": "click",
    "ref": "button-123",
    "targetId": "tab-123"
  }
}
```

## Nodes

### List Nodes

**GET** `/nodes/status`

List paired nodes (iOS/Android devices).

**Response:**
```json
{
  "ok": true,
  "nodes": [
    {
      "id": "iphone-xyz",
      "name": "Dan's iPhone",
      "platform": "ios",
      "online": true,
      "lastSeen": "2026-01-25T20:30:00Z"
    }
  ]
}
```

### Send Notification

**POST** `/nodes/notify`

Send notification to a node.

**Request Body:**
```json
{
  "node": "iphone-xyz",
  "title": "Reminder",
  "body": "Check the oven!",
  "priority": "timeSensitive"
}
```

### Capture Photo

**POST** `/nodes/camera_snap`

Take a photo with node camera.

**Request Body:**
```json
{
  "node": "iphone-xyz",
  "facing": "back",
  "quality": 0.8
}
```

## Error Handling

### Error Response Format

All errors follow this structure:

```json
{
  "ok": false,
  "error": "Human-readable error message",
  "code": "ERROR_CODE",
  "details": {}
}
```

### Common Error Codes

| Code | Description |
|------|-------------|
| `AUTH_REQUIRED` | Authentication token required |
| `INVALID_TOKEN` | Invalid authentication token |
| `TIMEOUT` | Request timed out |
| `AGENT_ERROR` | Agent execution error |
| `SESSION_NOT_FOUND` | Session does not exist |
| `INVALID_REQUEST` | Malformed request |
| `RATE_LIMITED` | Too many requests |

### HTTP Status Codes

| Status | Meaning |
|--------|---------|
| 200 | Success |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 429 | Rate Limited |
| 500 | Internal Server Error |
| 503 | Service Unavailable |

## Rate Limiting

The Gateway implements rate limiting to prevent abuse:

**Default Limits:**
- 60 requests per minute per IP
- 10 concurrent WebSocket connections per IP

**Rate Limit Headers:**
```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1706213400
```

**429 Response:**
```json
{
  "ok": false,
  "error": "Rate limit exceeded",
  "code": "RATE_LIMITED",
  "retryAfter": 30
}
```

## Best Practices

### Connection Management

1. **WebSocket Keepalive:** Send ping every 30-60s
2. **Reconnection:** Implement exponential backoff
3. **Connection Pooling:** Reuse connections when possible
4. **Timeout Handling:** Set appropriate timeouts for query complexity

### Performance

1. **Streaming:** Use WebSocket streaming for faster perceived response time
2. **Parallel Requests:** Gateway supports concurrent requests
3. **Model Selection:** Use faster models for simple queries
4. **Caching:** Cache identical requests locally when appropriate

### Security

1. **SSL/TLS:** Always use for remote connections
2. **Token Storage:** Store tokens securely (encrypted at rest)
3. **Network Security:** Use firewalls, SSH tunnels, or VPNs
4. **Least Privilege:** Only expose necessary endpoints

### Error Recovery

1. **Retry Logic:** Implement retry with exponential backoff
2. **Graceful Degradation:** Handle errors gracefully
3. **Timeout Strategy:** Different timeouts for different query types
4. **Logging:** Log errors for debugging

## Examples

### Complete WebSocket Example (Python)

```python
import asyncio
import websockets
import json

async def chat_with_clawd():
    uri = "ws://localhost:18789/gateway/ws/agent?sessionKey=main"
    
    async with websockets.connect(uri) as ws:
        # Send query
        await ws.send(json.dumps({
            "type": "message",
            "text": "What's the weather like today?"
        }))
        
        # Stream response
        full_response = ""
        async for message in ws:
            data = json.loads(message)
            
            if data["type"] == "token":
                # Streaming token
                print(data["content"], end="", flush=True)
                full_response += data["content"]
            
            elif data["type"] == "response":
                # Complete response
                print(f"\n\nComplete response: {data['content']}")
                print(f"Tokens used: {data['usage']['outputTokens']}")
                break
            
            elif data["type"] == "error":
                print(f"Error: {data['error']}")
                break

asyncio.run(chat_with_clawd())
```

### HTTP Request Example (curl)

```bash
# Health check
curl http://localhost:18789/health

# Send message
curl -X POST http://localhost:18789/agent/message \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "text": "What is 2+2?",
    "sessionKey": "main"
  }'

# List sessions
curl http://localhost:18789/sessions \
  -H "Authorization: Bearer YOUR_TOKEN"

# Schedule reminder
curl -X POST http://localhost:18789/cron/add \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d '{
    "schedule": "0 9 * * *",
    "text": "Morning briefing"
  }'
```

## Changelog

### Version 2026.1.21
- Initial Gateway API documentation
- WebSocket streaming support
- Session management endpoints
- Cron scheduling API
- Browser control endpoints
- Node management API

## Support

- **Clawdbot Docs:** https://docs.clawd.bot/
- **GitHub Issues:** https://github.com/ddrayne/clawd-homeassistant/issues
- **Discord:** https://discord.com/invite/clawd

---

*Last Updated: 2026-01-25*
