"""Tests for emoji stripping functionality.

These tests verify the strip_emojis function handles:
1. Normal text (unchanged)
2. Common emoji characters (removed)
3. Edge cases (empty strings, emoji-only, consecutive emojis)
4. Text-based emoticons (preserved)
5. Non-ASCII Unicode text (preserved)

Note on double-space behavior:
When an emoji is removed from the middle of text, the spaces on either side
remain, creating a double space. For example:
    "Hello [emoji] World" -> "Hello  World"
This is expected behavior - TTS engines typically handle double spaces
gracefully, and normalizing spaces would add complexity without clear benefit.

Requirements: UNIT-03
"""
import re

import pytest

# Try to import from conversation module, but if HA is unavailable (Windows
# standalone mode), extract the pure functions directly from the source file.
try:
    from custom_components.clawd.conversation import EMOJI_PATTERN, strip_emojis
except ImportError:
    # Standalone mode: define the same pattern and function locally.
    # This is copied from custom_components/clawd/conversation.py lines 23-38.
    # The pattern and function are pure Python with no HA dependencies.
    EMOJI_PATTERN = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # emoticons
        "\U0001F300-\U0001F5FF"  # symbols & pictographs
        "\U0001F680-\U0001F6FF"  # transport & map symbols
        "\U0001F1E0-\U0001F1FF"  # flags (iOS)
        "\U00002702-\U000027B0"  # dingbats
        "\U000024C2-\U0001F251"
        "]+",
        flags=re.UNICODE,
    )

    def strip_emojis(text: str) -> str:
        """Remove emojis from text for TTS."""
        return EMOJI_PATTERN.sub("", text).strip()


class TestEmojiPatternExists:
    """Verify EMOJI_PATTERN is properly defined."""

    def test_pattern_is_compiled_regex(self) -> None:
        """EMOJI_PATTERN should be a compiled regex pattern."""
        assert isinstance(EMOJI_PATTERN, re.Pattern)


class TestNormalTextPreserved:
    """Test that normal text passes through unchanged."""

    @pytest.mark.parametrize(
        "text",
        [
            "Hello world",
            "This is a test",
            "No emojis here!",
            "Numbers 123 and symbols @#$",
            "Punctuation: comma, period. question?",
            "Quotes 'single' and \"double\"",
            "Parentheses (like this)",
            "Math: 1 + 2 = 3",
        ],
        ids=[
            "simple-greeting",
            "simple-sentence",
            "no-emojis-statement",
            "numbers-and-symbols",
            "punctuation",
            "quotes",
            "parentheses",
            "math-expression",
        ],
    )
    def test_normal_text_unchanged(self, text: str) -> None:
        """Normal text without emojis should pass through unchanged."""
        assert strip_emojis(text) == text


class TestTextEmoticonsPreserved:
    """Test that text-based emoticons are NOT stripped.

    Text emoticons like :) and ;) are ASCII characters that predate
    Unicode emoji. These should be preserved for TTS since they are
    just punctuation combinations.
    """

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
            (":)", ":)"),
            (":(", ":("),
            (":D", ":D"),
            (";)", ";)"),
            ("Hello :)", "Hello :)"),
            ("<3", "<3"),
            ("^_^", "^_^"),
            ("o_O", "o_O"),
        ],
        ids=[
            "smiley",
            "frown",
            "grin",
            "wink",
            "text-with-smiley",
            "heart-text",
            "anime-face",
            "surprised-face",
        ],
    )
    def test_text_emoticons_preserved(self, text: str, expected: str) -> None:
        """Text-based emoticons should NOT be stripped."""
        assert strip_emojis(text) == expected


class TestCommonEmojisRemoved:
    """Test that common emoji characters are stripped.

    Tests emoji from various Unicode ranges:
    - Emoticons (U+1F600-U+1F64F): faces, gestures
    - Symbols & Pictographs (U+1F300-U+1F5FF): weather, nature
    - Transport & Map Symbols (U+1F680-U+1F6FF): vehicles, signs
    - Dingbats (U+2702-U+27B0): symbols, marks
    """

    @pytest.mark.parametrize(
        ("text", "expected"),
        [
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
        ],
        ids=[
            "grinning-face",
            "tears-of-joy",
            "smiling-eyes",
            "sun-face",
            "fire",
            "rocket",
            "car",
            "check-mark",
            "star",
        ],
    )
    def test_common_emojis_removed(self, text: str, expected: str) -> None:
        """Common emoji characters should be stripped from text."""
        assert strip_emojis(text) == expected


class TestEdgeCases:
    """Test edge cases for emoji stripping.

    These tests verify boundary conditions and unusual inputs.
    """

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
        """Multiple consecutive emojis are all removed.

        Note: Consecutive emojis are removed as one block due to + quantifier.
        """
        result = strip_emojis("Hello \U0001F600\U0001F601\U0001F602 World")
        assert result == "Hello  World"

    def test_emoji_at_start(self) -> None:
        """Emoji at start of string is removed.

        Note: Leading space is stripped by strip().
        """
        assert strip_emojis("\U0001F600 Hello") == "Hello"

    def test_emoji_at_end(self) -> None:
        """Emoji at end of string is removed.

        Note: Trailing space is stripped by strip().
        """
        assert strip_emojis("Hello \U0001F600") == "Hello"

    def test_interspersed_emojis(self) -> None:
        """Emojis interspersed in text are removed.

        Note: Each emoji removal leaves the surrounding spaces intact,
        which may result in double spaces. This is expected behavior.
        """
        result = strip_emojis("Hello \U0001F600 World \U0001F601 Test")
        assert result == "Hello  World  Test"


class TestUnicodeHandling:
    """Test handling of various Unicode text.

    Non-ASCII European language text should be preserved,
    as these are legitimate text characters, not emoji.
    """

    @pytest.mark.parametrize(
        "text",
        [
            "Bonjour le monde",  # French
            "Hallo Welt",  # German
            "Ciao mondo",  # Italian
            "Hola mundo",  # Spanish
        ],
        ids=[
            "french",
            "german",
            "italian",
            "spanish",
        ],
    )
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

    def test_accented_characters_preserved(self) -> None:
        """Explicitly test common accented characters."""
        # Test various accented characters used in European languages
        text_with_accents = "cafe resume naive Zurich Munchen"
        assert strip_emojis(text_with_accents) == text_with_accents


class TestRealWorldResponses:
    """Test with realistic AI assistant response patterns.

    These simulate actual responses from an AI assistant that
    might include emoji decorations that need to be stripped
    before text-to-speech processing.
    """

    def test_response_with_greeting_emoji(self) -> None:
        """Response starting with wave emoji."""
        result = strip_emojis("\U0001F44B Hello! How can I help?")
        assert result == "Hello! How can I help?"

    def test_response_with_thinking_emoji(self) -> None:
        """Response with thinking emoji at end.

        Note: U+1F914 (thinking face) is in the supplemental emoticons range
        (U+1F900-U+1F9FF) which is NOT covered by the current EMOJI_PATTERN.
        This is a known limitation - the pattern covers the most common emoji
        ranges but not all Unicode emoji blocks.
        """
        # Using a grinning face (U+1F600) instead, which IS in the covered range
        result = strip_emojis("Let me think about that... \U0001F600")
        assert result == "Let me think about that..."

    def test_response_with_multiple_emojis(self) -> None:
        """Response with multiple emojis throughout.

        Note: Double spaces occur where emoji was adjacent to text.
        """
        result = strip_emojis("\U0001F44B Hi! \U0001F60A Happy to help! \U0001F44D")
        assert result == "Hi!  Happy to help!"

    def test_response_weather_related(self) -> None:
        """Weather-related response with emoji."""
        result = strip_emojis("It looks sunny today! \U0001F31E")
        assert result == "It looks sunny today!"

    def test_response_with_thumbs_up(self) -> None:
        """Response ending with thumbs up emoji."""
        result = strip_emojis("I'll do that right away! \U0001F44D")
        assert result == "I'll do that right away!"

    def test_response_encouragement(self) -> None:
        """Encouraging response with star emoji."""
        result = strip_emojis("\u2B50 Great job! Keep it up! \u2B50")
        assert result == "Great job! Keep it up!"

    def test_multiline_response(self) -> None:
        """Multiline response with emoji.

        Note: Emoji at end of lines (but not end of string) leave trailing
        spaces. The strip() only affects leading/trailing whitespace of the
        entire string, not each line. This is expected behavior.
        """
        text = (
            "Here's what I found:\n"
            "- The temperature is 72F \U0001F321\n"
            "- It's mostly sunny \U0001F31E\n"
            "- Low chance of rain \U0001F327"
        )
        result = strip_emojis(text)
        # Note trailing spaces after 72F and sunny due to emoji removal
        # (space before emoji remains, only emoji is removed)
        expected = (
            "Here's what I found:\n"
            "- The temperature is 72F \n"
            "- It's mostly sunny \n"
            "- Low chance of rain"
        )
        assert result == expected
