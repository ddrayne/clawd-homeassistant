# Codebase Concerns

**Analysis Date:** 2026-01-25

## Tech Debt

**Broad Exception Catching in Initialization:**
- Issue: `__init__.py` line 46 catches all exceptions during initial Gateway connection without logging specific error context
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\__init__.py`
- Impact: If Gateway connection fails, the error message is logged but the specific exception type is lost, making debugging difficult. Setup failures are non-deterministic in their visibility.
- Fix approach: Replace bare `except Exception as err:` with specific exception handling for `GatewayConnectionError`, `GatewayTimeoutError`, and `GatewayAuthenticationError` at line 46. Log the original exception type explicitly.

**Broad Exception Catching in Config Flow:**
- Issue: `config_flow.py` lines 98 and 171 catch all exceptions during connection validation with minimal logging
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\config_flow.py`
- Impact: Unknown errors during config validation map to generic "unknown" error code, hiding real problems (network timeouts, SSL errors, malformed responses). Users cannot distinguish between different failure modes.
- Fix approach: Add specific exception handling before the broad catch at lines 98 and 171. Examples: `except (ssl.SSLError, socket.gaierror, asyncio.TimeoutError)` before the final broad catch, with distinct error codes for each.

**Private Protocol Implementation Access:**
- Issue: `gateway_client.py` line 98 directly accesses private `_connected_event` attribute from `GatewayProtocol`
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway_client.py`
- Impact: Breaking change if `GatewayProtocol` refactors internal state management. Tight coupling between layers. No public API for waiting on connection establishment.
- Fix approach: Add public method `wait_for_connection()` to `GatewayProtocol` that wraps the internal event. Update `ClawdGatewayClient.connect()` to use the public method instead of accessing `_connected_event`.

**Incomplete Cleanup in Connection Loop:**
- Issue: `gateway.py` lines 177-183 handle authentication errors by breaking the reconnection loop, but `_pending_requests` is never explicitly cleared after fatal errors
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py`
- Impact: If auth fails repeatedly, each failed attempt leaves futures in `_pending_requests`. Although `disconnect()` cleans them up, this is only called explicitly by higher layers. A dangling connection attempt could leave failed futures indefinitely.
- Fix approach: Clear `_pending_requests` immediately after catching `GatewayAuthenticationError` or `ProtocolError` in lines 177-183, before breaking.

## Known Bugs

**Duplicate Handler Registration Not Prevented at Runtime:**
- Symptoms: If `on_event()` is called twice with the same handler function, the second call logs a warning but does not actually prevent duplicate registration if the handler object identity changes
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 372-388
- Trigger: Register a lambda or dynamically created handler twice; the check at line 377 uses `handler not in list`, which relies on object identity. If the same logical handler is wrapped differently, duplicates slip through.
- Workaround: Ensure handlers are stored as named functions or methods, not lambdas. Avoid re-registering handlers on reconnection without first unregistering.

**Agent Run Event Race Condition:**
- Symptoms: Events for a run_id can arrive after `AgentRun` is removed from `_agent_runs` dict, but this is logged as debug "unknown run". If the agent sends multiple completion events rapidly, the second completion is silently ignored.
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway_client.py` lines 218-222 and 194-195
- Trigger: Gateway sends `status="ok"` completion event, then immediately sends a second event before the cleanup at line 195 completes. The handler will not find the run in the dict.
- Workaround: The current code handles this gracefully by checking `if not agent_run:` and returning early. No actual data loss occurs. Monitor logs for frequency of "Agent event for unknown run" warnings.

## Security Considerations

**Gateway Token Exposure in Logs:**
- Risk: Token values could be accidentally logged if exception messages include the entire config dict or request payloads
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway_client.py` (token passed via params dict), `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` (line 415 logs requests)
- Current mitigation: Logs use `_LOGGER.debug()` for request details and avoid logging the full params dict. Token is not explicitly logged anywhere observed.
- Recommendations: (1) Add explicit sanitization in debug logging to mask token values if full request payloads are logged. (2) Document that debug logs may contain sensitive data and should not be shared. (3) Consider adding a redaction utility for common secrets (token, password fields).

**Non-SSL Remote Connections Warning Only:**
- Risk: Users can connect to remote Gateways without SSL, sending unencrypted traffic including auth tokens
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\config_flow.py` lines 81-88 and 153-160
- Current mitigation: Warnings logged at lines 86-88 and 158-160 when non-localhost remote connection is attempted without SSL. User must acknowledge this configuration.
- Recommendations: (1) Strongly consider making SSL required for non-localhost connections rather than just warning. (2) Document the security implications more prominently in README (currently mentioned but could be emphasized as critical). (3) Add validation to reject insecure remote configs if possible without breaking backward compatibility.

**Authentication Token Storage:**
- Risk: Although Home Assistant encrypts secrets at rest, the token is visible in plain text during configuration flow and in debug logs
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\config_flow.py` (token passed as user_input dict)
- Current mitigation: Home Assistant's config_entries automatically encrypts tokens with CONF_TOKEN key. Token is not logged in regular code paths.
- Recommendations: (1) Verify Home Assistant's encryption is enabled in deployment environment. (2) Add a note in documentation that tokens should be treated as passwords. (3) Consider adding rotation capability if Gateway supports token expiration.

## Performance Bottlenecks

**Synchronous Emoji Pattern Matching on Every Response:**
- Problem: `conversation.py` line 38 applies regex substitution to every response before TTS, even if emojis are disabled
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\conversation.py` lines 23-38
- Cause: `strip_emojis()` is always called when `CONF_STRIP_EMOJIS` is true, applying regex to the full response text
- Improvement path: For very long responses (1000+ chars), regex compilation is O(n). The `EMOJI_PATTERN` is compiled at module load time (good), but the substitution still scans the entire string. For typical responses (<500 chars) this is negligible. If users report delays with very long responses, consider: (1) Implementing incremental emoji stripping only on new chunks if streaming is added later, (2) Caching compiled regex to module level (already done, so no improvement here).

**Agent Run State Not Garbage Collected on Errors:**
- Problem: If an agent request times out (line 185-191 in `gateway_client.py`), the `AgentRun` object is removed from `_agent_runs` in the finally block, but if the event handler thread is slow, it may still hold a reference
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway_client.py` lines 158-195
- Cause: Race between cleanup (line 195) and handler (lines 209-260). If many requests timeout in rapid succession, memory could accumulate.
- Improvement path: The finally block ensures cleanup regardless of exception. Memory leak risk is low because: (1) timeouts are expected to be rare, (2) `AgentRun` objects are small (one string buffer + asyncio.Event), (3) cleanup happens immediately. Monitor for "Agent event for unknown run" log spam as an indicator of excessive timeouts.

**WebSocket Connection Loop Blocks on Ping Timeouts:**
- Problem: `gateway.py` line 115-119 uses websockets library's auto-ping with 30-second interval and 10-second timeout. If ping times out, reconnection takes 5 seconds (line 189) plus connection time
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 112-189
- Cause: Network latency on poor connections could trigger unnecessary reconnections
- Improvement path: The current defaults (ping=30s, timeout=10s) are reasonable for local networks. If users report frequent disconnections on unstable networks: (1) add configurable ping/timeout parameters, (2) implement exponential backoff for reconnection retries instead of fixed 5s sleep.

## Fragile Areas

**Event Handler Dispatch Exception Handling:**
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 358-370
- Why fragile: Event handlers are user-provided callables (registered at line 372-388). If a handler raises an exception, the current code catches it and logs, but continues dispatching to other handlers. If the agent event handler throws, the event is partially processed.
- Safe modification: Add a wrapper that pre-validates handlers are callable. Test that handler exceptions don't prevent other handlers from running (current behavior is correct but not obvious). Document that handlers should not raise exceptions.
- Test coverage: No explicit tests visible for handler exception cases. Need unit tests for: (1) handler that raises, (2) async handler that raises, (3) multiple handlers with one failing.

**Handshake Message Ordering Assumption:**
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 228-249
- Why fragile: The handshake assumes events can arrive during handshake (line 235-240 skips events) but the response will eventually arrive. If the Gateway sends events in a specific order, an event before the response could be lost.
- Safe modification: Use a higher-level protocol state machine that explicitly handles "awaiting handshake response" state. Currently the loop is reasonable but fragile to Gateway protocol changes.
- Test coverage: No visible tests for handshake scenarios. Need tests for: (1) handshake timeout, (2) handshake with intervening events, (3) handshake failure with error response.

**Connection State Race Between Layers:**
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 49, 123-124, 138, 144-145, and `gateway_client.py` line 98-99
- Why fragile: `_connected` flag is set at line 123 immediately after handshake, but receive_task might not be running yet. Brief window where `connected` property returns true but receive loop hasn't started.
- Safe modification: Ensure `_connected` is only set AFTER receive_task is confirmed running. Use asyncio barriers or move receive_task start before setting `_connected = True`.
- Test coverage: No visible tests for rapid connect/send sequences. Need integration tests for: (1) immediate send after connect returns, (2) concurrent connect+disconnect.

**JSON Parsing No Size Limits:**
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 281-289
- Why fragile: `json.loads()` on line 283 has no size restrictions. A malicious or broken Gateway could send multi-megabyte JSON payloads causing memory exhaustion.
- Safe modification: Add maximum message size check before `json.loads()`. Example: `if len(message_text) > 10_000_000: raise ProtocolError("Message too large")`.
- Test coverage: No visible tests for oversized payloads. Need to test malformed/oversized message handling.

## Scaling Limits

**Single Pending Request Dict Not Bounded:**
- Current capacity: `_pending_requests` dict grows with concurrent requests (line 410 adds, line 433 removes)
- Limit: If 1000+ concurrent requests are sent to Gateway without responses, dict grows unbounded. In-memory dict size becomes issue.
- Scaling path: (1) Add max pending requests limit (soft warning at 100+, reject at 1000), (2) implement request queue with backpressure, (3) add metrics logging of dict size for debugging.

**Agent Runs Dict No Eviction Policy:**
- Current capacity: `_agent_runs` dict stores one AgentRun per in-flight request
- Limit: If agents take 30+ seconds and many concurrent requests arrive, dict grows. Orphaned entries from cancelled requests never auto-evict.
- Scaling path: (1) Add cleanup timer that removes runs older than 2x timeout value, (2) track orphaned entries and warn if accumulation is detected, (3) add metrics for peak dict size.

**WebSocket Message Queue In Memory:**
- Current capacity: websockets library buffers received messages. No backpressure implemented.
- Limit: If receive_loop is slow and many events arrive, the internal websockets buffer could grow large
- Scaling path: Add flow control - measure event dispatch latency and warn if taking >100ms. Consider async queue with bounded size between recv and handler.

## Dependencies at Risk

**websockets >= 12.0 (Hard Requirement):**
- Risk: websockets 12.0+ has breaking changes from 11.x. If an older version is installed, code will fail.
- Impact: Home Assistant users must have websockets 12.0+ installed. Older environments (HA versions <2024.1) may have older websockets.
- Migration plan: The manifest.json specifies `websockets>=12.0`, which is correct. However, document that Home Assistant 2024.1+ is required specifically for websockets 12.0 compatibility.

**Home Assistant 2024.1.0+ (Hard Requirement):**
- Risk: Integration uses modern HA APIs (config_entries, async patterns). Earlier versions of HA lack required features.
- Impact: Installation on HA <2024.1 will fail or behave unexpectedly.
- Migration plan: Enforce minimum version in manifest (currently not explicitly set). Add version check in __init__.py or document clearly.

## Missing Critical Features

**No Request Timeout Configuration:**
- Problem: Individual request timeouts are hardcoded in gateway_client.py: initial ack at 10s (line 145), health/status at 5s (lines 263, 267). Agent wait timeout uses CONF_TIMEOUT but connect has fixed 5s (line 98).
- Blocks: Users cannot increase initial handshake timeout for slow networks. Health checks timeout quickly and cannot be retried.
- Impact: On slow/unreliable networks, even valid connections fail during setup or health checks.

**No Persistent Retry Logic for Failed Requests:**
- Problem: If a request times out or fails, no retry is attempted at the application level. Users must reconfigure the integration.
- Blocks: Transient network issues or brief Gateway unavailability causes permanent setup failure.
- Impact: Users cannot recover from temporary network glitches without manual intervention.

**No Rate Limiting Between Requests:**
- Problem: Multiple concurrent conversation requests immediately send to Gateway without any throttling or queue ordering.
- Blocks: Burst traffic could overwhelm the Gateway or exhaust connection resources.
- Impact: High-frequency requests (e.g., voice assistant with short timeouts) could cause degradation.

## Test Coverage Gaps

**Handshake Failure Scenarios:**
- What's not tested: Timeout during handshake, authentication failure during handshake, protocol version mismatch, Gateway sending malformed response
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 191-273
- Risk: Handshake logic is complex with state management. Silent failures are possible if edge cases exist (e.g., timeout during response wait is caught, but what if JSON is malformed?).
- Priority: High - handshake failures should fail fast with clear errors

**Message Handler Exception Propagation:**
- What's not tested: Event handler exceptions, async vs sync handler exceptions, handler that raises during dispatch
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway.py` lines 358-370
- Risk: Handler exceptions are caught and logged but the semantics of "continue dispatching other handlers" may not match user expectations. No way to know if a handler failed.
- Priority: Medium - affects reliability but not core functionality

**Agent Run Cleanup on Exception:**
- What's not tested: Timeout scenarios, error responses, missing run_id in events
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\gateway_client.py` lines 158-207
- Risk: The finally block cleans up, but what if cleanup itself fails? What if multiple completion events arrive?
- Priority: Medium - currently handles gracefully but should be tested explicitly

**Config Validation Security:**
- What's not tested: SSL/TLS connection validation, certificate chain verification, token sensitivity in error messages
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\config_flow.py` lines 35-60
- Risk: SSL errors might expose path information or certificate details in error messages.
- Priority: Medium-High - affects security posture

**Conversation Entity Emoji Stripping:**
- What's not tested: Emoji pattern matches, edge cases (skin tone modifiers, zero-width joiners), stripping toggle
- Files: `C:\Users\danie\Documents\Code\clawd-homeassistant\custom_components\clawd\conversation.py` lines 23-38
- Risk: Emoji pattern may not match all emoji variations (especially newer Unicode versions). TTS could receive unexpected output.
- Priority: Low - functionality is not critical, graceful degradation if pattern incomplete

**Concurrent Message Handling:**
- What's not tested: Multiple concurrent agent requests, request while handshaking, disconnect during request
- Files: Multiple files - gateway.py connection loop, gateway_client.py request handling
- Risk: Race conditions possible in concurrent scenarios. No stress testing visible.
- Priority: High - affects reliability in realistic usage

---

*Concerns audit: 2026-01-25*
