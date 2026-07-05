"""
Unit tests for helper functions in src.utils.helpers
"""
import pytest
import os
import tempfile
from pathlib import Path
from code.src.utils.helpers import checksum, domain_from_url, safe_float, parse_inequality_p


class TestChecksum:
    """Tests for the checksum function"""

    def test_checksum_sha256(self):
        """Test SHA256 checksum calculation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = checksum(temp_path, "sha256")
            assert len(result) == 64  # SHA256 produces 64 hex chars
            assert all(c in '0123456789abcdef' for c in result)
        finally:
            os.unlink(temp_path)

    def test_checksum_md5(self):
        """Test MD5 checksum calculation"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("test content")
            temp_path = f.name

        try:
            result = checksum(temp_path, "md5")
            assert len(result) == 32  # MD5 produces 32 hex chars
        finally:
            os.unlink(temp_path)

    def test_checksum_file_not_found(self):
        """Test that FileNotFoundError is raised for missing files"""
        with pytest.raises(FileNotFoundError):
            checksum("/nonexistent/path/file.txt")

    def test_checksum_consistency(self):
        """Test that checksum is consistent for same content"""
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("consistent content")
            temp_path = f.name

        try:
            result1 = checksum(temp_path)
            result2 = checksum(temp_path)
            assert result1 == result2
        finally:
            os.unlink(temp_path)


class TestDomainFromUrl:
    """Tests for the domain_from_url function"""

    def test_domain_from_full_url(self):
        """Test extracting domain from full URL"""
        assert domain_from_url("https://www.example.com/path") == "www.example.com"
        assert domain_from_url("http://subdomain.example.org/page?query=1") == "subdomain.example.org"

    def test_domain_from_url_without_scheme(self):
        """Test extracting domain from URL without scheme"""
        assert domain_from_url("example.com/path") == "example.com"
        assert domain_from_url("sub.domain.co.uk") == "sub.domain.co.uk"

    def test_domain_lowercase(self):
        """Test that domain is returned in lowercase"""
        assert domain_from_url("HTTPS://EXAMPLE.COM") == "example.com"

    def test_domain_invalid_url(self):
        """Test handling of invalid URLs"""
        assert domain_from_url("") is None
        assert domain_from_url("not a url") is None
        assert domain_from_url(None) is None

    def test_domain_with_port(self):
        """Test extracting domain with port number"""
        assert domain_from_url("http://example.com:8080/path") == "example.com:8080"


class TestSafeFloat:
    """Tests for the safe_float function"""

    def test_safe_float_string(self):
        """Test parsing string to float"""
        assert safe_float("3.14") == 3.14
        assert safe_float("0.05") == 0.05
        assert safe_float("1e-5") == 1e-5

    def test_safe_float_integer(self):
        """Test converting integer to float"""
        assert safe_float(5) == 5.0
        assert safe_float(0) == 0.0

    def test_safe_float_float(self):
        """Test that float remains float"""
        assert safe_float(3.14) == 3.14

    def test_safe_float_none(self):
        """Test handling of None"""
        assert safe_float(None) is None
        assert safe_float(None, default=0.0) == 0.0

    def test_safe_float_invalid_string(self):
        """Test handling of invalid strings"""
        assert safe_float("not a number") is None
        assert safe_float("not a number", default=-1.0) == -1.0

    def test_safe_float_empty_string(self):
        """Test handling of empty string"""
        assert safe_float("") is None
        assert safe_float("  ", default=0.5) == 0.5

    def test_safe_float_whitespace(self):
        """Test handling of whitespace"""
        assert safe_float("  3.14  ") == 3.14


class TestParseInequalityP:
    """Tests for the parse_inequality_p function"""

    def test_parse_inequality_less_than(self):
        """Test parsing less-than inequality"""
        value, op = parse_inequality_p("< 0.05")
        assert value == 0.05
        assert op == "<"

    def test_parse_inequality_greater_than(self):
        """Test parsing greater-than inequality"""
        value, op = parse_inequality_p("> 0.1")
        assert value == 0.1
        assert op == ">"

    def test_parse_inequality_with_p_prefix(self):
        """Test parsing with 'p' prefix"""
        value, op = parse_inequality_p("p < 0.01")
        assert value == 0.01
        assert op == "<"

        value, op = parse_inequality_p("p > 0.05")
        assert value == 0.05
        assert op == ">"

    def test_parse_plain_number(self):
        """Test parsing plain number without inequality"""
        value, op = parse_inequality_p("0.03")
        assert value == 0.03
        assert op is None

    def test_parse_leq_geq(self):
        """Test parsing <= and >= operators"""
        value, op = parse_inequality_p("<= 0.05")
        assert value == 0.05
        assert op == "<="

        value, op = parse_inequality_p(">= 0.1")
        assert value == 0.1
        assert op == ">="

    def test_parse_invalid_input(self):
        """Test handling of invalid input"""
        value, op = parse_inequality_p("invalid")
        assert value is None
        assert op is None

    def test_parse_empty_string(self):
        """Test handling of empty string"""
        value, op = parse_inequality_p("")
        assert value is None
        assert op is None

    def test_parse_whitespace_handling(self):
        """Test handling of extra whitespace"""
        value, op = parse_inequality_p("  <  0.05  ")
        assert value == 0.05
        assert op == "<"

    def test_parse_case_insensitivity(self):
        """Test that parsing is case insensitive"""
        value, op = parse_inequality_p("P < 0.05")
        assert value == 0.05
        assert op == "<"

        value, op = parse_inequality_p("p < 0.05")
        assert value == 0.05
        assert op == "<"