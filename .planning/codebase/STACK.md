# Technology Stack

**Analysis Date:** 2026-01-25

## Languages

**Primary:**
- Python 3 - Home Assistant integration component; all source code in `custom_components/clawd/`

## Runtime

**Environment:**
- Home Assistant 2024.1.0 or later - Required platform

**Package Manager:**
- pip - Home Assistant's native dependency manager
- Lockfile: Not detected (dependencies specified in `manifest.json`)

## Frameworks

**Core:**
- Home Assistant - Version 2024.1.0+ (Integration framework)
  - Purpose: Smart home automation platform hosting the Clawd integration
  - Used for conversation entity implementation, config flows, platform setup

**WebSocket:**
- websockets - Version 12.0+ (as specified in `manifest.json`)
  - Purpose: Async WebSocket client for Clawdbot Gateway communication
  - Used in `custom_components/clawd/gateway.py` for WebSocket protocol implementation

**Configuration:**
- voluptuous - Home Assistant built-in (not explicit in requirements)
  - Purpose: Configuration schema validation for config flows
  - Used in `custom_components/clawd/config_flow.py`

## Key Dependencies

**Critical:**
- websockets 12.0+ - WebSocket protocol implementation
  - Why it matters: Enables real-time bidirectional communication with Clawdbot Gateway
  - Used for persistent connections with ping/pong keepalive (30s intervals, 10s timeout)

**Infrastructure:**
- Home Assistant core - Provides conversation entity platform, config entries, logging
  - Used in `custom_components/clawd/__init__.py`, `conversation.py`, `config_flow.py`

## Configuration

**Environment:**
- Home Assistant UI-based configuration flow - Primary setup method
  - No environment variables required for core operation
  - Gateway token can be configured via web UI (encrypted at rest by Home Assistant)
  - Alternative: Manual YAML configuration supported through Home Assistant config entries

**Build:**
- `manifest.json` - Integration metadata and dependency specification
  - Location: `custom_components/clawd/manifest.json`
  - Specifies: domain, version, requirements, IoT class, documentation URL

**Configuration Files:**
- `custom_components/clawd/manifest.json` - Integration manifest with dependencies
- `custom_components/clawd/strings.json` - i18n strings for UI forms and errors

## Home Assistant Integration Details

**Domain:**
- clawd - Integration domain identifier
- Entry point: `custom_components/clawd/__init__.py`

**Platforms:**
- conversation - Conversation entity for voice assistant integration
  - Implementation: `custom_components/clawd/conversation.py`

**Configuration:**
- Host: Gateway hostname or IP (default: 127.0.0.1)
- Port: Gateway port (default: 18789)
- Token: Optional authentication token for remote connections
- Use SSL: Boolean flag for WSS (secure WebSocket) connections
- Timeout: Agent response timeout in seconds (default: 30, range: 5-300)
- Session Key: Clawdbot session identifier (default: "main")
- Strip Emojis: Boolean flag to remove emojis from TTS output (default: true)

**IoT Class:**
- local_push - Integration communicates with local Clawdbot Gateway

## Platform Requirements

**Development:**
- Python 3.7+ (Home Assistant's requirement)
- Home Assistant development environment or test instance
- Clawdbot installation with Gateway running

**Production:**
- Home Assistant installation (2024.1.0 or later)
- Clawdbot running with Gateway enabled on accessible host/port
- Network connectivity between Home Assistant and Gateway
- SSL/TLS recommended for remote connections

---

*Stack analysis: 2026-01-25*
