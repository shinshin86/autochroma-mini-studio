"""Tests for ffmpeg_tools module."""
import pytest

from app.ffmpeg_tools import (
    validate_hex_color,
    validate_chromakey_params,
    parse_progress,
    InvalidParameterError,
)


class TestValidateHexColor:
    """Tests for validate_hex_color function."""

    def test_valid_hex_color(self):
        """Valid hex colors should be accepted."""
        assert validate_hex_color("00FF00") == "00FF00"
        assert validate_hex_color("ff0000") == "FF0000"
        assert validate_hex_color("AABBCC") == "AABBCC"

    def test_valid_hex_color_with_hash(self):
        """Hex colors with # prefix should be accepted."""
        assert validate_hex_color("#00FF00") == "00FF00"
        assert validate_hex_color("#ff0000") == "FF0000"

    def test_invalid_hex_color_short(self):
        """Short hex colors should be rejected."""
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_hex_color("00FF")
        assert "Invalid hex color format" in str(exc_info.value)

    def test_invalid_hex_color_long(self):
        """Long hex colors should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_hex_color("00FF00FF")

    def test_invalid_hex_color_characters(self):
        """Invalid characters should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_hex_color("GGHHII")

    def test_empty_hex_color(self):
        """Empty string should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_hex_color("")

    def test_only_hash(self):
        """Only # should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_hex_color("#")


class TestValidateChromakeyParams:
    """Tests for validate_chromakey_params function."""

    def test_valid_params(self):
        """Valid parameters should be accepted."""
        sim, blend = validate_chromakey_params(0.4, 0.1)
        assert sim == 0.4
        assert blend == 0.1

    def test_boundary_values(self):
        """Boundary values should be accepted."""
        assert validate_chromakey_params(0.0, 0.0) == (0.0, 0.0)
        assert validate_chromakey_params(1.0, 1.0) == (1.0, 1.0)
        assert validate_chromakey_params(0.5, 0.5) == (0.5, 0.5)

    def test_integer_values(self):
        """Integer values should be converted to float."""
        sim, blend = validate_chromakey_params(0, 1)
        assert sim == 0.0
        assert blend == 1.0
        assert isinstance(sim, float)
        assert isinstance(blend, float)

    def test_similarity_too_low(self):
        """Similarity below 0 should be rejected."""
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_chromakey_params(-0.1, 0.1)
        assert "similarity" in str(exc_info.value).lower()

    def test_similarity_too_high(self):
        """Similarity above 1 should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_chromakey_params(1.1, 0.1)

    def test_blend_too_low(self):
        """Blend below 0 should be rejected."""
        with pytest.raises(InvalidParameterError) as exc_info:
            validate_chromakey_params(0.4, -0.1)
        assert "blend" in str(exc_info.value).lower()

    def test_blend_too_high(self):
        """Blend above 1 should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_chromakey_params(0.4, 1.1)

    def test_non_numeric_similarity(self):
        """Non-numeric similarity should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_chromakey_params("0.4", 0.1)

    def test_non_numeric_blend(self):
        """Non-numeric blend should be rejected."""
        with pytest.raises(InvalidParameterError):
            validate_chromakey_params(0.4, "0.1")


class TestParseProgress:
    """Tests for parse_progress function."""

    def test_valid_progress_line(self):
        """Valid progress line should be parsed."""
        assert parse_progress("out_time_ms=1000000") == 1000000
        assert parse_progress("out_time_ms=0") == 0
        assert parse_progress("out_time_ms=5000") == 5000

    def test_non_progress_line(self):
        """Non-progress lines should return None."""
        assert parse_progress("frame=100") is None
        assert parse_progress("fps=30") is None
        assert parse_progress("progress=continue") is None

    def test_malformed_progress_line(self):
        """Malformed progress lines should return None."""
        assert parse_progress("out_time_ms=") is None
        assert parse_progress("out_time_ms=abc") is None
        assert parse_progress("out_time_ms") is None

    def test_empty_line(self):
        """Empty line should return None."""
        assert parse_progress("") is None

    def test_progress_with_whitespace(self):
        """Progress line with surrounding whitespace."""
        # The function expects clean lines
        assert parse_progress("out_time_ms=1000") == 1000
