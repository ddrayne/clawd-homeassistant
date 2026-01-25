# Phase 1: Test Infrastructure Foundation - Context

**Gathered:** 2026-01-25
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish pytest configuration, core fixtures, and cleanup patterns that prevent async pitfalls. This phase creates the foundation that all subsequent test phases build on. No actual tests of application code — just the infrastructure to write tests.

</domain>

<decisions>
## Implementation Decisions

### Claude's Discretion

User deferred all implementation decisions to Claude. Standard Home Assistant testing conventions and pytest best practices should guide:

- **Pytest configuration** — pyproject.toml or pytest.ini, plugin selection, coverage settings
- **Fixture organization** — conftest.py structure, naming conventions, scope choices
- **Mock hass object** — Minimal stub vs behavior-accurate mock, what methods to implement
- **Mock config entries** — Factory pattern vs fixture instances
- **WebSocket mock fixtures** — Level of realism for connect/disconnect simulation
- **Async cleanup patterns** — Fixture-level teardown vs explicit cleanup, event loop handling

**Constraints from requirements:**
- INFRA-01: Single CLI command to run tests with coverage report
- INFRA-02: Mock hass object as reusable fixture
- INFRA-03: Mock config entries without manual setup per test
- INFRA-04: WebSocket mock fixtures for basic connect/disconnect
- INFRA-05: Proper async resource cleanup (no "Event loop is closed" errors)

</decisions>

<specifics>
## Specific Ideas

No specific requirements — open to standard approaches.

Follow Home Assistant custom component testing patterns where applicable.

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope.

</deferred>

---

*Phase: 01-test-infrastructure-foundation*
*Context gathered: 2026-01-25*
