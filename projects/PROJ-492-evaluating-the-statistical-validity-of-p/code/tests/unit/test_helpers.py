"""
Unit tests for helper functions in src/utils/helpers.py.

Tests cover:
- checksum: SHA256 file hashing
- domain_from_url: URL domain extraction
- safe_float: Safe float conversion
- parse_inequality_p: Inequality p-value parsing
"""

import pytest
import tempfile
import os
from pathlib import Path

from code.src.utils.helpers import (
    checksum,
    domain_from_url,
    safe_float,
    parse_inequality_p,
)


class TestChecksum:
    """Tests for the checksum function."""

    def test_checksum_basic(self, tmp_path: Path):
        """Test basic SHA256 checksum computation."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Hello, World!")

        result = checksum(test_file)

        assert len(result) == 64  # SHA256 hex length
        assert all(c in "0123456789abcdef" for c in result)

    def test_checksum_file_not_found(self):
        """Test checksum raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            checksum("/nonexistent/path/file.txt")

    def test_checksum_directory_error(self, tmp_path: Path):
        """Test checksum raises IsADirectoryError for directories."""
        with pytest.raises(IsADirectoryError):
            checksum(tmp_path)

    def test_checksum_consistency(self, tmp_path: Path):
        """Test checksum returns same value for same file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("Consistency test")

        result1 = checksum(test_file)
        result2 = checksum(test_file)

        assert result1 == result2

    def test_checksum_empty_file(self, tmp_path: Path):
        """Test checksum for empty file."""
        test_file = tmp_path / "empty.txt"
        test_file.write_text("")

        result = checksum(test_file)

        assert len(result) == 64


class TestDomainFromUrl:
    """Tests for the domain_from_url function."""

    def test_basic_url(self):
        """Test extraction from basic URL."""
        result = domain_from_url("https://example.com/path/to/page")
        assert result == "example.com"

    def test_http_url(self):
        """Test extraction from HTTP URL."""
        result = domain_from_url("http://test.org/page")
        assert result == "test.org"

    def test_url_with_www(self):
        """Test extraction removes www prefix."""
        result = domain_from_url("https://www.example.com/page")
        assert result == "example.com"

    def test_url_with_port(self):
        """Test extraction handles port numbers."""
        result = domain_from_url("https://example.com:8080/path")
        assert result == "example.com"

    def test_url_with_query_string(self):
        """Test extraction stops at query string."""
        result = domain_from_url("https://example.com/page?foo=bar")
        assert result == "example.com"

    def test_empty_url(self):
        """Test empty URL returns None."""
        result = domain_from_url("")
        assert result is None

    def test_whitespace_url(self):
        """Test URL with whitespace returns None."""
        result = domain_from_url("   ")
        assert result is None

    def test_complex_domain(self):
        """Test extraction from complex domain."""
        result = domain_from_url("https://sub.example.co.uk/path")
        assert result == "sub.example.co.uk"


class TestSafeFloat:
    """Tests for the safe_float function."""

    def test_valid_string(self):
        """Test conversion of valid numeric string."""
        result = safe_float("3.14")
        assert result == 3.14

    def test_integer_string(self):
        """Test conversion of integer string."""
        result = safe_float("42")
        assert result == 42.0

    def test_integer_input(self):
        """Test conversion of integer input."""
        result = safe_float(42)
        assert result == 42.0

    def test_float_input(self):
        """Test float input passes through."""
        result = safe_float(3.14)
        assert result == 3.14

    def test_none_input(self):
        """Test None input returns None."""
        result = safe_float(None)
        assert result is None

    def test_none_with_default(self):
        """Test None input with default returns default."""
        result = safe_float(None, default=0.0)
        assert result == 0.0

    def test_invalid_string(self):
        """Test invalid string returns default."""
        result = safe_float("not_a_number")
        assert result is None

    def test_invalid_string_with_default(self):
        """Test invalid string with default returns default."""
        result = safe_float("invalid", default=-1.0)
        assert result == -1.0

    def test_empty_string(self):
        """Test empty string returns None."""
        result = safe_float("")
        assert result is None

    def test_whitespace_string(self):
        """Test whitespace string returns None."""
        result = safe_float("   ")
        assert result is None

    def test_nan_strings(self):
        """Test NaN-like strings return None."""
        for nan_str in ["nan", "NaN", "none", "None", "null", "n/a", "-"]:
            result = safe_float(nan_str)
            assert result is None

    def test_negative_number(self):
        """Test negative number string."""
        result = safe_float("-3.14")
        assert result == -3.14

    def test_scientific_notation(self):
        """Test scientific notation string."""
        result = safe_float("1.5e-10")
        assert result == 1.5e-10


class TestParseInequalityP:
    """Tests for the parse_inequality_p function."""

    def test_less_than(self):
        """Test parsing p < value."""
        value, op = parse_inequality_p("p < 0.05")
        assert value == 0.05
        assert op == "<"

    def test_greater_than(self):
        """Test parsing p > value."""
        value, op = parse_inequality_p("p > 0.10")
        assert value == 0.10
        assert op == ">"

    def test_less_than_or_equal(self):
        """Test parsing p <= value."""
        value, op = parse_inequality_p("p <= 0.01")
        assert value == 0.01
        assert op == "<="

    def test_greater_than_or_equal(self):
        """Test parsing p >= value."""
        value, op = parse_inequality_p("p >= 0.05")
        assert value == 0.05
        assert op == ">="

    def test_equals(self):
        """Test parsing p = value."""
        value, op = parse_inequality_p("p = 0.03")
        assert value == 0.03
        assert op == "="

    def test_plain_number(self):
        """Test parsing plain number without p prefix."""
        value, op = parse_inequality_p("0.05")
        assert value == 0.05
        assert op is None

    def test_with_spaces(self):
        """Test parsing with extra spaces."""
        value, op = parse_inequality_p("  p  <  0.05  ")
        assert value == 0.05
        assert op == "<"

    def test_no_prefix(self):
        """Test parsing without p prefix."""
        value, op = parse_inequality_p("< 0.05")
        assert value == 0.05
        assert op == "<"

    def test_empty_string(self):
        """Test empty string returns (None, None)."""
        value, op = parse_inequality_p("")
        assert value is None
        assert op is None

    def test_none_input(self):
        """Test None input returns (None, None)."""
        value, op = parse_inequality_p(None)
        assert value is None
        assert op is None

    def test_invalid_string(self):
        """Test invalid string returns (None, None)."""
        value, op = parse_inequality_p("invalid")
        assert value is None
        assert op is None

    def test_case_insensitive(self):
        """Test case insensitivity."""
        value, op = parse_inequality_p("P < 0.05")
        assert value == 0.05
        assert op == "<"

    def test_probability_prefix(self):
        """Test probability prefix."""
        value, op = parse_inequality_p("probability < 0.05")
        assert value == 0.05
        assert op == "<"