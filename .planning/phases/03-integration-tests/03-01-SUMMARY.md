---
type: summary
phase: 03
plan: 01
subsystem: integration-tests
tags:
  - config-flow
  - conversation
  - error-handling
  - emoji-stripping
dependency-graph:
  requires:
    - "02-01: exception hierarchy tests"
    - "02-02: emoji stripping unit tests"
  provides:
    - "Integration tests for config flow"
    - "Integration tests for conversation entity"
  affects:
    - "03-02: Gateway client tests"
    - "04-xx: Gateway protocol tests"
tech-stack:
  added: []
  patterns:
    - "pytest.mark.skipif for HA framework conditional tests"
    - "Mock factory functions for test objects"
    - "Error message constant validation"
key-files:
  created:
    - tests/test_config_flow.py
    - tests/test_conversation.py
  modified: []
decisions:
  - key: "skip-tests-without-ha"
    choice: "Use pytest.mark.skipif for tests requiring HA framework"
    rationale: "Allows tests to run in Windows standalone mode while still testing full flow when HA available"
  - key: "error-message-validation"
    choice: "Test error message content for user-friendliness"
    rationale: "Ensures user-facing error messages don't expose technical details"
  - key: "mock-factory-pattern"
    choice: "Use factory functions for mock objects"
    rationale: "Cleaner test setup, reusable across test classes"
metrics:
  duration: "15 min"
  completed: "2026-01-25"
---

# Phase 03 Plan 01: Core Integration Tests Summary

**One-liner:** Config flow and conversation entity tests covering success/error paths with 32 tests (23 passing, 9 skipped without HA).

## What Was Built

### Config Flow Integration Tests (test_config_flow.py)

Created 15 focused tests for the config flow:

**TestConfigFlowErrorMapping (3 tests - always pass)**
- Verified GatewayAuthenticationError maps to "invalid_auth"
- Verified GatewayTimeoutError maps to "timeout"
- Verified GatewayConnectionError maps to "cannot_connect"

**TestValidateConnectionFunction (4 tests - skipped without HA)**
- Valid connection returns entry title
- Auth error propagates correctly
- Connection error propagates correctly
- Timeout error propagates correctly

**TestConfigFlowStepUser (5 tests - skipped without HA)**
- Initial step shows form
- Valid input creates entry
- Auth/connection/timeout errors show correct error keys

**TestUniqueIdHandling (3 tests - always pass)**
- Unique ID format is host:port
- Different ports produce different IDs
- Different hosts produce different IDs

### Conversation Entity Integration Tests (test_conversation.py)

Created 17 focused tests for the conversation entity:

**TestConversationEntityAvailability (2 tests)**
- Entity available when connected
- Entity unavailable when disconnected

**TestConversationSuccessPath (3 tests)**
- Send message returns response
- Response includes conversation ID
- Response includes agent ID

**TestConversationErrorHandling (3 tests)**
- Connection error returns helpful message
- Timeout error returns helpful message
- Agent error returns helpful message

**TestEmojiStrippingIntegration (3 tests)**
- Emoji stripped when enabled
- Emoji preserved when disabled
- Chat log always gets full response

**TestConversationInputValidation (2 tests)**
- User message extracted from input
- Language extracted from input

**TestErrorMessageConstants (4 tests)**
- Connection error message is helpful
- Timeout error message is helpful
- Agent error message is helpful
- Unexpected error message is helpful

## Test Statistics

| File | Lines | Tests | Passed | Skipped |
|------|-------|-------|--------|---------|
| test_config_flow.py | 390 | 15 | 6 | 9 |
| test_conversation.py | 361 | 17 | 17 | 0 |
| **Total** | **751** | **32** | **23** | **9** |

Full test suite: 180 passed, 10 skipped

## Technical Decisions

### Skip Tests Without HA Framework
Used `pytest.mark.skipif(not HAS_HA_FRAMEWORK)` to handle Windows Long Path issues:
- Tests requiring HA imports are skipped in standalone mode
- Tests using direct module loading always run
- Provides full coverage when HA framework available

### Mock Factory Functions
Created reusable mock factories:
- `make_valid_input()` - creates valid config input dict
- `make_mock_user_input()` - creates mock ConversationInput
- `make_mock_chat_log()` - creates mock ChatLog
- `make_mock_config_entry()` - creates mock config entry
- `make_mock_gateway_client()` - creates mock gateway client with configurable responses/errors

### Error Message Validation
Tests verify user-facing messages are:
- Non-technical (no "WebSocket", "ECONNREFUSED", etc.)
- Actionable ("check your configuration", "try again")
- Concise (under 60 characters where possible)

## Commits

| Commit | Description |
|--------|-------------|
| e8208d6 | test(03-01): add config flow integration tests |
| 673007c | test(03-01): add conversation entity integration tests |

## Deviations from Plan

None - plan executed exactly as written.

## Next Phase Readiness

**Ready for 03-02:** Gateway client tests
- Config flow tests establish error propagation patterns
- Conversation tests establish error handling patterns
- Mock factory pattern can be extended for gateway tests

**Dependencies satisfied:**
- Exception hierarchy verified (02-01)
- Emoji stripping verified (02-02)
- Error mapping verified (03-01)
