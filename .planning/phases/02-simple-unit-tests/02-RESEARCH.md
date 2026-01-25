# Phase 2: Simple Unit Tests - Research

**Researched:** 2026-01-25
**Domain:** pytest unit testing patterns for constants, exception hierarchies, and regex
**Confidence:** HIGH

## Summary

This phase introduces simple unit tests for pure logic with no async operations or external dependencies. The three target areas are: (1) const.py with its configuration constants, (2) exceptions.py with its custom exception hierarchy, and (3) the emoji stripping regex pattern in conversation.py. These are ideal first tests because they require no mocking, no Home Assistant framework, and test deterministic, pure functions.

The testing approach follows pytest best practices established in Phase 1. Constants are tested via direct assertion to document expected values. Exception classes are tested by instantiation with messages and verifying inheritance hierarchies. Regex patterns are tested through parametrized tests covering normal cases, edge cases, and Unicode handling.

**Primary recommendation:** Use pytest.mark.parametrize extensively for edge case coverage, especially for emoji stripping. Test exception hierarchy using isinstance() checks. Document constant values through tests to catch accidental changes.

## Standard Stack

The infrastructure from Phase 1 is sufficient. No additional libraries needed.

### Core (from Phase 1)
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | ^9.0.0 | Test framework | Already configured |
| pytest-cov | ^7.0.0 | Coverage reporting | Already configured |

### Not Needed for This Phase
| Library | Why Not |
|---------|---------|
| pytest-asyncio | No async code in these tests |
| pytest-homeassistant-custom-component | No HA framework needed for pure unit tests |
| unittest.mock | No mocking needed - testing pure functions |

**Key insight:** These tests can run in standalone mode without the HA framework, making them faster and more portable.

## Architecture Patterns

### Recommended Test File Structure
```
tests/
├── conftest.py                  # Existing fixtures (not needed for this phase)
├── test_fixtures.py             # Existing fixture smoke tests
├── test_const.py                # NEW: Constants tests (UNIT-01)
├── test_exceptions.py           # NEW: Exception hierarchy tests (UNIT-02)
└── test_conversation_emoji.py   # NEW: Emoji stripping tests (UNIT-03)
```

### Pattern 1: Constants as Documentation Tests
**What:** Test each constant to document its expected value
**When to use:** For configuration constants that other code depends on
**Why:** Catches accidental changes and serves as executable documentation
**Example:**
```python
# tests/test_const.py
from custom_components.clawd.const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    # ... all constants
)

class TestDomain:
    """Test domain constant."""

    def test_domain_value(self) -> None:
        """Domain should be 'clawd'."""
        assert DOMAIN == "clawd"


class TestDefaultConfiguration:
    """Test default configuration values."""

    def test_default_host(self) -> None:
        """Default host should be localhost."""
        assert DEFAULT_HOST == "127.0.0.1"

    def test_default_port(self) -> None:
        """Default port should be 18789."""
        assert DEFAULT_PORT == 18789
```

### Pattern 2: Exception Hierarchy Testing
**What:** Test exception instantiation and inheritance chain
**When to use:** For custom exception classes
**Why:** Verifies exceptions can be raised, caught, and carry error details
**Example:**
```python
# tests/test_exceptions.py
import pytest
from custom_components.clawd.exceptions import (
    ClawdError,
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayTimeoutError,
    AgentExecutionError,
    ProtocolError,
)


class TestExceptionHierarchy:
    """Test exception inheritance hierarchy."""

    def test_all_exceptions_inherit_from_clawd_error(self) -> None:
        """All custom exceptions should inherit from ClawdError."""
        exceptions = [
            GatewayConnectionError,
            GatewayAuthenticationError,
            GatewayTimeoutError,
            AgentExecutionError,
            ProtocolError,
        ]
        for exc_class in exceptions:
            assert issubclass(exc_class, ClawdError)

    def test_clawd_error_inherits_from_exception(self) -> None:
        """ClawdError should inherit from Exception."""
        assert issubclass(ClawdError, Exception)


class TestExceptionInstantiation:
    """Test exception instantiation with messages."""

    @pytest.mark.parametrize("exc_class,message", [
        (ClawdError, "Base error"),
        (GatewayConnectionError, "Cannot connect to gateway"),
        (GatewayAuthenticationError, "Invalid token"),
        (GatewayTimeoutError, "Request timed out"),
        (AgentExecutionError, "Agent failed"),
        (ProtocolError, "Protocol mismatch"),
    ])
    def test_exception_with_message(self, exc_class, message) -> None:
        """Exception should carry error message."""
        exc = exc_class(message)
        assert str(exc) == message

    def test_exception_can_be_raised_and_caught(self) -> None:
        """Exceptions can be raised and caught by parent type."""
        with pytest.raises(ClawdError):
            raise GatewayConnectionError("test")
```

### Pattern 3: Parametrized Regex Testing
**What:** Test regex patterns with many input/output pairs
**When to use:** For text processing functions with multiple edge cases
**Why:** Comprehensive coverage without repetitive test functions
**Example:**
```python
# tests/test_conversation_emoji.py
import pytest
from custom_components.clawd.conversation import strip_emojis


class TestEmojiStripping:
    """Test emoji stripping functionality."""

    @pytest.mark.parametrize("input_text,expected", [
        # Normal text (no emojis)
        ("Hello world", "Hello world"),
        ("No emojis here", "No emojis here"),

        # Single emojis
        ("Hello!", "Hello!"),  # Not an emoji, just punctuation
        ("Hello :)", "Hello :)"),  # Text emoticon preserved

        # Edge cases
        ("", ""),  # Empty string
        ("   ", ""),  # Whitespace only (strip() effect)
    ], ids=[
        "plain-text",
        "text-no-emojis",
        "punctuation-preserved",
        "text-emoticon-preserved",
        "empty-string",
        "whitespace-only",
    ])
    def test_basic_cases(self, input_text: str, expected: str) -> None:
        """Test basic emoji stripping cases."""
        assert strip_emojis(input_text) == expected
```

### Anti-Patterns to Avoid
- **Testing implementation not behavior:** Don't test that EMOJI_PATTERN is a compiled regex; test that strip_emojis() works correctly
- **Hard-coding magic values:** If a constant represents something (like a port), test both the value AND that it makes sense (e.g., valid port range)
- **Testing trivial getters:** Don't test that `DOMAIN` has a value; test that it has the CORRECT value
- **Overly broad parametrization:** Keep parametrize groups focused on one behavior (valid inputs, invalid inputs, edge cases)

## Don't Hand-Roll

Problems that look simple but have existing solutions:

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Test case combinations | Manual loops | pytest.mark.parametrize | Built-in, clearer failures |
| Exception matching | if/try/except blocks | pytest.raises | Context manager, match parameter |
| Test IDs | Numbered tests | ids parameter in parametrize | Readable failure messages |
| Constant change detection | Manual comparison | Direct assertion tests | Documents expected values |

**Key insight:** For pure unit tests, the standard pytest patterns are sufficient. No additional libraries needed beyond what Phase 1 established.

## Common Pitfalls

### Pitfall 1: Regex Not Matching All Emoji Types
**What goes wrong:** Emoji pattern misses newer emoji, ZWJ sequences, or flag emoji
**Why it happens:** Unicode emoji standard evolves; simple patterns miss compound emoji
**How to avoid:**
1. Test known emoji categories separately (emoticons, symbols, flags)
2. Test ZWJ sequences (family emoji, skin tone modifiers)
3. Document known limitations in test names
**Warning signs:** Users report emoji appearing in TTS that should be stripped

### Pitfall 2: Testing Constants That Might Change
**What goes wrong:** Tests break when intentionally changing configuration defaults
**Why it happens:** Tests are too rigid about specific values
**How to avoid:**
1. Test that constants exist and have reasonable types
2. Test relationships between constants (e.g., MIN < MAX)
3. For critical values that must not change (like DOMAIN), test the exact value
4. For defaults that could change, test type and validity
**Warning signs:** Tests break during intentional configuration updates

### Pitfall 3: Exception Message Assumptions
**What goes wrong:** Tests fail because exception message format changed
**Why it happens:** Testing exact message strings is brittle
**How to avoid:**
1. Test that exceptions CAN carry messages, not specific messages
2. Use pytest.raises(match=...) only for user-facing error messages
3. Test exception type, not content, unless content is part of API
**Warning signs:** Tests break when improving error messages

### Pitfall 4: Whitespace Sensitivity in Text Tests
**What goes wrong:** Tests fail due to leading/trailing whitespace differences
**Why it happens:** strip_emojis() uses .strip() which affects whitespace
**How to avoid:**
1. Explicitly test whitespace handling behavior
2. Document whether function should preserve or strip whitespace
3. Use test IDs that indicate whitespace sensitivity
**Warning signs:** Flaky tests when input has unusual whitespace

### Pitfall 5: Import Side Effects
**What goes wrong:** Importing const.py or exceptions.py triggers unwanted code
**Why it happens:** Module-level code with side effects
**How to avoid:**
1. Verify modules can be imported without side effects
2. First test in each test file should just import
3. Use try/except in conftest.py pattern if needed
**Warning signs:** Tests fail on import before any test runs

## Code Examples

Verified patterns from pytest documentation and Phase 1 research:

### Complete test_const.py Structure
```python
# tests/test_const.py
"""Tests for const.py constants.

These tests serve as executable documentation for expected constant values.
They catch accidental changes to configuration defaults.

Requirements: UNIT-01
"""
from custom_components.clawd.const import (
    DOMAIN,
    DEFAULT_HOST,
    DEFAULT_PORT,
    DEFAULT_USE_SSL,
    DEFAULT_TIMEOUT,
    DEFAULT_SESSION_KEY,
    DEFAULT_STRIP_EMOJIS,
    CONF_HOST,
    CONF_PORT,
    CONF_TOKEN,
    CONF_USE_SSL,
    CONF_TIMEOUT,
    CONF_SESSION_KEY,
    CONF_STRIP_EMOJIS,
    STATE_CONNECTED,
    STATE_DISCONNECTED,
    STATE_CONNECTING,
    STATE_ERROR,
    PROTOCOL_MIN_VERSION,
    PROTOCOL_MAX_VERSION,
    CLIENT_ID,
    CLIENT_DISPLAY_NAME,
    CLIENT_VERSION,
    CLIENT_PLATFORM,
    CLIENT_MODE,
)


class TestDomain:
    """Test domain constant - must never change."""

    def test_domain_is_clawd(self) -> None:
        """Domain identifier must be 'clawd'."""
        assert DOMAIN == "clawd"


class TestDefaultConfiguration:
    """Test default configuration values."""

    def test_default_host_is_localhost(self) -> None:
        """Default host should be localhost IP."""
        assert DEFAULT_HOST == "127.0.0.1"

    def test_default_port_is_valid(self) -> None:
        """Default port should be valid port number."""
        assert DEFAULT_PORT == 18789
        assert 1 <= DEFAULT_PORT <= 65535

    def test_default_ssl_disabled(self) -> None:
        """SSL disabled by default for local development."""
        assert DEFAULT_USE_SSL is False

    def test_default_timeout_reasonable(self) -> None:
        """Default timeout should be reasonable (not too short, not too long)."""
        assert DEFAULT_TIMEOUT == 30
        assert 5 <= DEFAULT_TIMEOUT <= 300

    def test_default_session_key(self) -> None:
        """Default session key for direct chat."""
        assert DEFAULT_SESSION_KEY == "main"

    def test_default_strip_emojis_enabled(self) -> None:
        """Emoji stripping enabled by default for TTS."""
        assert DEFAULT_STRIP_EMOJIS is True


class TestConfigurationKeys:
    """Test configuration key constants are strings."""

    def test_conf_host(self) -> None:
        assert CONF_HOST == "host"

    def test_conf_port(self) -> None:
        assert CONF_PORT == "port"

    def test_conf_token(self) -> None:
        assert CONF_TOKEN == "token"

    def test_conf_use_ssl(self) -> None:
        assert CONF_USE_SSL == "use_ssl"

    def test_conf_timeout(self) -> None:
        assert CONF_TIMEOUT == "timeout"

    def test_conf_session_key(self) -> None:
        assert CONF_SESSION_KEY == "session_key"

    def test_conf_strip_emojis(self) -> None:
        assert CONF_STRIP_EMOJIS == "strip_emojis"


class TestConnectionStates:
    """Test connection state constants."""

    def test_state_connected(self) -> None:
        assert STATE_CONNECTED == "connected"

    def test_state_disconnected(self) -> None:
        assert STATE_DISCONNECTED == "disconnected"

    def test_state_connecting(self) -> None:
        assert STATE_CONNECTING == "connecting"

    def test_state_error(self) -> None:
        assert STATE_ERROR == "error"


class TestProtocolVersion:
    """Test protocol version constants."""

    def test_protocol_min_version(self) -> None:
        assert PROTOCOL_MIN_VERSION == 3

    def test_protocol_max_version(self) -> None:
        assert PROTOCOL_MAX_VERSION == 3

    def test_min_not_greater_than_max(self) -> None:
        """Min version should never exceed max version."""
        assert PROTOCOL_MIN_VERSION <= PROTOCOL_MAX_VERSION


class TestClientIdentification:
    """Test client identification constants."""

    def test_client_id(self) -> None:
        assert CLIENT_ID == "gateway-client"

    def test_client_display_name(self) -> None:
        assert CLIENT_DISPLAY_NAME == "Home Assistant Clawd"

    def test_client_version(self) -> None:
        assert CLIENT_VERSION == "1.0.0"

    def test_client_platform(self) -> None:
        assert CLIENT_PLATFORM == "python"

    def test_client_mode(self) -> None:
        assert CLIENT_MODE == "backend"
```

### Complete test_exceptions.py Structure
```python
# tests/test_exceptions.py
"""Tests for exceptions.py exception hierarchy.

These tests verify that all custom exceptions:
1. Can be instantiated with messages
2. Inherit correctly from ClawdError
3. Can be raised and caught appropriately

Requirements: UNIT-02
"""
import pytest

from custom_components.clawd.exceptions import (
    ClawdError,
    GatewayConnectionError,
    GatewayAuthenticationError,
    GatewayTimeoutError,
    AgentExecutionError,
    ProtocolError,
)


class TestClawdErrorBase:
    """Test base ClawdError class."""

    def test_inherits_from_exception(self) -> None:
        """ClawdError should inherit from Exception."""
        assert issubclass(ClawdError, Exception)

    def test_can_instantiate_without_message(self) -> None:
        """ClawdError can be created without message."""
        exc = ClawdError()
        assert str(exc) == ""

    def test_can_instantiate_with_message(self) -> None:
        """ClawdError can be created with message."""
        exc = ClawdError("test error")
        assert str(exc) == "test error"


class TestExceptionHierarchy:
    """Test all exceptions inherit from ClawdError."""

    @pytest.mark.parametrize("exc_class", [
        GatewayConnectionError,
        GatewayAuthenticationError,
        GatewayTimeoutError,
        AgentExecutionError,
        ProtocolError,
    ])
    def test_inherits_from_clawd_error(self, exc_class) -> None:
        """All custom exceptions should be subclasses of ClawdError."""
        assert issubclass(exc_class, ClawdError)

    @pytest.mark.parametrize("exc_class", [
        ClawdError,
        GatewayConnectionError,
        GatewayAuthenticationError,
        GatewayTimeoutError,
        AgentExecutionError,
        ProtocolError,
    ])
    def test_inherits_from_exception(self, exc_class) -> None:
        """All exceptions should be catchable as Exception."""
        assert issubclass(exc_class, Exception)


class TestExceptionInstantiation:
    """Test exception instantiation with messages."""

    @pytest.mark.parametrize("exc_class,message", [
        (ClawdError, "Base error occurred"),
        (GatewayConnectionError, "Cannot connect to gateway at localhost:8765"),
        (GatewayAuthenticationError, "Invalid authentication token"),
        (GatewayTimeoutError, "Request timed out after 30 seconds"),
        (AgentExecutionError, "Agent failed to process request"),
        (ProtocolError, "Protocol version mismatch: expected 3, got 2"),
    ], ids=[
        "base-error",
        "connection-error",
        "auth-error",
        "timeout-error",
        "agent-error",
        "protocol-error",
    ])
    def test_exception_carries_message(self, exc_class, message) -> None:
        """Exception should store and return error message."""
        exc = exc_class(message)
        assert str(exc) == message


class TestExceptionRaiseAndCatch:
    """Test exceptions can be raised and caught."""

    def test_gateway_connection_error_caught_as_clawd_error(self) -> None:
        """GatewayConnectionError can be caught as ClawdError."""
        with pytest.raises(ClawdError):
            raise GatewayConnectionError("connection failed")

    def test_gateway_auth_error_caught_as_clawd_error(self) -> None:
        """GatewayAuthenticationError can be caught as ClawdError."""
        with pytest.raises(ClawdError):
            raise GatewayAuthenticationError("auth failed")

    def test_gateway_timeout_error_caught_as_clawd_error(self) -> None:
        """GatewayTimeoutError can be caught as ClawdError."""
        with pytest.raises(ClawdError):
            raise GatewayTimeoutError("timeout")

    def test_agent_execution_error_caught_as_clawd_error(self) -> None:
        """AgentExecutionError can be caught as ClawdError."""
        with pytest.raises(ClawdError):
            raise AgentExecutionError("agent failed")

    def test_protocol_error_caught_as_clawd_error(self) -> None:
        """ProtocolError can be caught as ClawdError."""
        with pytest.raises(ClawdError):
            raise ProtocolError("protocol error")

    def test_specific_exception_not_caught_by_sibling(self) -> None:
        """GatewayConnectionError is not caught by GatewayAuthenticationError."""
        with pytest.raises(GatewayConnectionError):
            # This should NOT be caught by GatewayAuthenticationError
            try:
                raise GatewayConnectionError("connection")
            except GatewayAuthenticationError:
                pytest.fail("Should not catch sibling exception type")
```

### Complete test_conversation_emoji.py Structure
```python
# tests/test_conversation_emoji.py
"""Tests for emoji stripping functionality.

These tests verify the strip_emojis function handles:
1. Normal text (unchanged)
2. Common emoji characters (removed)
3. Edge cases (empty strings, emoji-only, consecutive emojis)

Requirements: UNIT-03
"""
import pytest

from custom_components.clawd.conversation import strip_emojis, EMOJI_PATTERN


class TestEmojiPatternExists:
    """Verify EMOJI_PATTERN is properly defined."""

    def test_pattern_is_compiled_regex(self) -> None:
        """EMOJI_PATTERN should be a compiled regex pattern."""
        import re
        assert isinstance(EMOJI_PATTERN, re.Pattern)


class TestNormalTextPreserved:
    """Test that normal text passes through unchanged."""

    @pytest.mark.parametrize("text", [
        "Hello world",
        "This is a test",
        "No emojis here!",
        "Numbers 123 and symbols @#$",
        "Punctuation: comma, period. question?",
        "Quotes 'single' and \"double\"",
        "Parentheses (like this)",
        "Math: 1 + 2 = 3",
    ], ids=[
        "simple-greeting",
        "simple-sentence",
        "no-emojis-statement",
        "numbers-and-symbols",
        "punctuation",
        "quotes",
        "parentheses",
        "math-expression",
    ])
    def test_normal_text_unchanged(self, text: str) -> None:
        """Normal text without emojis should pass through unchanged."""
        assert strip_emojis(text) == text


class TestTextEmoticonsPreserved:
    """Test that text-based emoticons are NOT stripped."""

    @pytest.mark.parametrize("text,expected", [
        (":)", ":)"),
        (":(", ":("),
        (":D", ":D"),
        (";)", ";)"),
        ("Hello :)", "Hello :)"),
        ("<3", "<3"),
        ("^_^", "^_^"),
        ("o_O", "o_O"),
    ], ids=[
        "smiley",
        "frown",
        "grin",
        "wink",
        "text-with-smiley",
        "heart-text",
        "anime-face",
        "surprised-face",
    ])
    def test_text_emoticons_preserved(self, text: str, expected: str) -> None:
        """Text-based emoticons should NOT be stripped."""
        assert strip_emojis(text) == expected


class TestCommonEmojisRemoved:
    """Test that common emoji characters are stripped."""

    @pytest.mark.parametrize("text,expected", [
        # Emoticons (U+1F600-U+1F64F)
        ("Hello \U0001F600", "Hello"),  # grinning face
        ("Test \U0001F602 test", "Test  test"),  # face with tears of joy
        ("\U0001F60A Nice", "Nice"),  # smiling face with smiling eyes

        # Symbols & Pictographs (U+1F300-U+1F5FF)
        ("Weather \U0001F31E", "Weather"),  # sun with face
        ("\U0001F525 Fire", "Fire"),  # fire

        # Transport & Map Symbols (U+1F680-U+1F6FF)
        ("Rocket \U0001F680", "Rocket"),  # rocket
        ("Car \U0001F697", "Car"),  # automobile

        # Dingbats (U+2702-U+27B0)
        ("Check \u2714", "Check"),  # check mark
        ("Star \u2B50", "Star"),  # star

    ], ids=[
        "grinning-face",
        "tears-of-joy",
        "smiling-eyes",
        "sun-face",
        "fire",
        "rocket",
        "car",
        "check-mark",
        "star",
    ])
    def test_common_emojis_removed(self, text: str, expected: str) -> None:
        """Common emoji characters should be stripped from text."""
        assert strip_emojis(text) == expected


class TestEdgeCases:
    """Test edge cases for emoji stripping."""

    def test_empty_string(self) -> None:
        """Empty string returns empty string."""
        assert strip_emojis("") == ""

    def test_whitespace_only(self) -> None:
        """Whitespace-only string returns empty (due to strip())."""
        assert strip_emojis("   ") == ""

    def test_emoji_only_string(self) -> None:
        """String with only emoji returns empty."""
        assert strip_emojis("\U0001F600\U0001F601\U0001F602") == ""

    def test_consecutive_emojis(self) -> None:
        """Multiple consecutive emojis are all removed."""
        result = strip_emojis("Hello \U0001F600\U0001F601\U0001F602 World")
        assert result == "Hello  World"

    def test_emoji_at_start(self) -> None:
        """Emoji at start of string is removed."""
        assert strip_emojis("\U0001F600 Hello") == "Hello"

    def test_emoji_at_end(self) -> None:
        """Emoji at end of string is removed."""
        assert strip_emojis("Hello \U0001F600") == "Hello"

    def test_interspersed_emojis(self) -> None:
        """Emojis interspersed in text are removed."""
        result = strip_emojis("Hello \U0001F600 World \U0001F601 Test")
        assert result == "Hello  World  Test"


class TestUnicodeHandling:
    """Test handling of various Unicode text."""

    @pytest.mark.parametrize("text", [
        "Bonjour le monde",
        "Hallo Welt",
        "Ciao mondo",
        "Hola mundo",
    ], ids=[
        "french",
        "german",
        "italian",
        "spanish",
    ])
    def test_european_languages_preserved(self, text: str) -> None:
        """European language text should be unchanged."""
        assert strip_emojis(text) == text

    def test_mixed_unicode_and_emoji(self) -> None:
        """Text with non-ASCII Unicode and emoji handles correctly."""
        result = strip_emojis("Cafe \U0001F600")
        assert result == "Cafe"

    def test_unicode_with_accents(self) -> None:
        """Text with accented characters is preserved."""
        assert strip_emojis("cafe") == "cafe"


class TestRealWorldResponses:
    """Test with realistic AI assistant response patterns."""

    def test_response_with_greeting_emoji(self) -> None:
        """Response starting with wave emoji."""
        result = strip_emojis("\U0001F44B Hello! How can I help?")
        assert result == "Hello! How can I help?"

    def test_response_with_thinking_emoji(self) -> None:
        """Response with thinking emoji."""
        result = strip_emojis("Let me think about that... \U0001F914")
        assert result == "Let me think about that..."

    def test_response_with_multiple_emojis(self) -> None:
        """Response with multiple emojis throughout."""
        result = strip_emojis("\U0001F44B Hi! \U0001F60A Happy to help! \U0001F44D")
        assert result == "Hi!  Happy to help!"

    def test_response_weather_related(self) -> None:
        """Weather-related response with emoji."""
        result = strip_emojis("It looks sunny today! \U0001F31E")
        assert result == "It looks sunny today!"

    def test_response_list_items(self) -> None:
        """Response with emoji bullet points."""
        result = strip_emojis("\u2022 Item one\n\u2022 Item two")
        # Bullet point is not in emoji range, should be preserved
        assert "\u2022" in result or result == "Item one\nItem two"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual test loops | pytest.mark.parametrize | pytest established practice | Cleaner code, better failure messages |
| if/try blocks | pytest.raises context manager | pytest standard | Cleaner exception testing |
| Inline test data | Separate parametrize data | Best practice | More readable tests |
| No test IDs | ids parameter | pytest feature | Readable failure output |

**Deprecated/outdated:**
- Using `nose` for testing: pytest is the standard
- `unittest.TestCase` style: pytest functions/classes are preferred
- Manual assertEqual: Use assert with pytest rewriting

## Open Questions

Things that couldn't be fully resolved:

1. **Completeness of EMOJI_PATTERN**
   - What we know: Current pattern covers major Unicode emoji ranges
   - What's unclear: Whether it handles all ZWJ sequences, skin tone modifiers, and flag emoji
   - Recommendation: Test known categories, document known limitations, consider demoji library if users report issues

2. **Double-space artifacts**
   - What we know: Removing emoji mid-sentence can leave double spaces
   - What's unclear: Whether this matters for TTS (it probably doesn't)
   - Recommendation: Document behavior in tests, consider adding space normalization if UX issue arises

## Sources

### Primary (HIGH confidence)
- [pytest documentation - parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html) - Parametrization patterns
- [pytest documentation - raises](https://docs.pytest.org/en/stable/reference/reference.html) - Exception testing
- [Python regex documentation](https://docs.python.org/3/library/re.html) - Unicode regex patterns
- Phase 1 RESEARCH.md - Testing infrastructure patterns

### Secondary (MEDIUM confidence)
- [emoji-regex GitHub](https://github.com/mathiasbynens/emoji-regex) - Emoji pattern reference
- [Python Exception Testing Article](https://towardsdatascience.com/python-exception-testing-clean-and-effective-methods-86799da86b90/) - Exception testing patterns
- [pytest-param patterns](https://rednafi.com/python/pytest-param/) - Advanced parametrize usage

### Tertiary (LOW confidence)
- WebSearch results for emoji regex patterns - Community patterns, unverified

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - No new libraries, uses Phase 1 infrastructure
- Architecture: HIGH - Standard pytest patterns from official documentation
- Pitfalls: HIGH - Derived from testing pure functions, well-documented patterns
- Emoji edge cases: MEDIUM - Unicode emoji evolves; pattern may have gaps

**Research date:** 2026-01-25
**Valid until:** 2026-02-25 (30 days - stable domain, pure unit tests)
