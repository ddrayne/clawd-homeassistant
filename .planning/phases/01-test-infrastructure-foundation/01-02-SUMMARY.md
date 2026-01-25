---
phase: 01-test-infrastructure-foundation
plan: 02
subsystem: testing
tags: [pytest, fixtures, async, websocket, mock, home-assistant]

# Dependency graph
requires:
  - phase: 01-01
    provides: pytest configuration with asyncio_mode=auto and tests/__init__.py
provides:
  - Core test fixtures for all subsequent test phases
  - auto_enable_custom_integrations for HA discovery
  - mock_config_entry factory for Clawd domain
  - mock_websocket with AsyncMock for send/recv/close
  - mock_websocket_connect patching gateway module
  - async_cleanup pattern for event loop safety
affects: [01-03, phase-2, phase-3, phase-4, phase-5, phase-6, phase-7]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - AsyncMock for WebSocket method mocking
    - Generator-typed fixture for patch yielding
    - Async fixture for cleanup pattern

key-files:
  created:
    - tests/conftest.py
  modified: []

key-decisions:
  - "Factory pattern for mock_config_entry (returns new instance each call)"
  - "Patch target is gateway module, not websockets directly"
  - "Async generator pattern for mock connect (matches websockets library behavior)"

patterns-established:
  - "INFRA-01: auto_enable_custom_integrations (autouse) enables HA discovery"
  - "INFRA-02: mock_websocket provides AsyncMock with async context manager support"
  - "INFRA-03: mock_websocket_connect yields (mock_connect, mock_websocket) tuple"
  - "INFRA-04: async_cleanup fixture for event loop cleanup"

# Metrics
duration: 1min
completed: 2026-01-25
---

# Phase 01 Plan 02: Core Test Fixtures Summary

**5 pytest fixtures in conftest.py: auto_enable_custom_integrations, mock_config_entry, mock_websocket, mock_websocket_connect, and async_cleanup**

## Performance

- **Duration:** 1 min
- **Started:** 2026-01-25T16:31:22Z
- **Completed:** 2026-01-25T16:32:27Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- Created conftest.py with all core fixtures for Clawd integration testing
- Established WebSocket mocking pattern that patches the correct gateway module path
- Implemented async_cleanup fixture to prevent "Event loop is closed" errors

## Task Commits

Each task was committed atomically:

1. **Task 1: Create conftest.py with all core fixtures** - `552f460` (feat)
2. **Task 2: Add async cleanup helper fixture** - `cb4e7ca` (feat)

## Files Created/Modified
- `tests/conftest.py` - Core test fixtures for Clawd integration (72 lines)

## Decisions Made
- **Factory pattern for mock_config_entry**: Returns new MockConfigEntry instance each call (function scope by default)
- **Patch target is gateway module**: Using `custom_components.clawd.gateway.websockets.connect` ensures the patch hits where websockets is actually imported
- **Async generator for connect mock**: Matches the websockets library's async iterator pattern for reconnection support

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- All 5 fixtures are defined and ready for use
- Plan 03 will validate fixtures by running actual pytest
- Fixtures provide complete foundation for all subsequent test phases

---
*Phase: 01-test-infrastructure-foundation*
*Completed: 2026-01-25*
