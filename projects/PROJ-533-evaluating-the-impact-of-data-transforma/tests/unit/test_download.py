"""
Unit tests for URL validation logic in the download pipeline.
"""
import pytest
from urllib.parse import urlparse
import re


def is_valid_url(url: str) -> bool:
    """
    Validates if a string is a well-formed HTTP/HTTPS URL.
    
    Args:
        url: The string to validate.
        
    Returns:
        True if the URL is valid and uses http or https scheme, False otherwise.
    """
    if not url or not isinstance(url, str):
        return False
        
    try:
        result = urlparse(url)
        # Check if scheme is http or https and netloc (domain) exists
        if result.scheme not in ['http', 'https']:
            return False
        if not result.netloc:
            return False
        
        # Additional regex check for basic URL structure safety
        # Ensures no obvious malformed patterns
        url_pattern = re.compile(
            r'^https?://'  # http or https
            r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+[A-Z]{2,6}\.?|'  # domain...
            r'localhost|'  # localhost...
            r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'  # ...or ip
            r'(?::\d+)?'  # optional port
            r'(?:/?|[/?]\S+)$', re.IGNORECASE)
            
        return bool(url_pattern.match(url))
    except Exception:
        return False


class TestValidUrl:
    """Tests for valid URL validation scenarios."""

    def test_valid_url_returns_true_for_valid_url(self):
        """
        Asserts that is_valid_url returns True for a standard valid URL.
        """
        valid_urls = [
            "https://archive.ics.uci.edu/ml/datasets.php",
            "http://example.com/data.csv",
            "https://www.openml.org/api/v1/data",
            "https://sub.domain.example.org/path/to/file?query=1"
        ]
        
        for url in valid_urls:
            assert is_valid_url(url) is True, f"Expected {url} to be valid"

    def test_valid_url_with_https(self):
        """Test HTTPS URL specifically."""
        assert is_valid_url("https://secure.site.com") is True

    def test_valid_url_with_localhost(self):
        """Test localhost URL."""
        assert is_valid_url("http://localhost:8080/api") is True

    def test_valid_url_with_ip_address(self):
        """Test IP address URL."""
        assert is_valid_url("http://192.168.1.1/resource") is True


class TestInvalidUrl:
    """Tests for invalid URL validation scenarios."""

    def test_invalid_url_returns_false(self):
        """
        Asserts that is_valid_url returns False for invalid strings.
        """
        invalid_inputs = [
            "not_a_url",
            "ftp://files.example.com",  # Wrong scheme
            "www.example.com",  # Missing scheme
            "http://",  # Missing domain
            "https://",  # Missing domain
            "",  # Empty string
            None,  # None value
            12345,  # Non-string type
            "javascript:alert('xss')",  # Malicious scheme
        ]
        
        for invalid in invalid_inputs:
            assert is_valid_url(invalid) is False, f"Expected {invalid} to be invalid"

    def test_invalid_url_missing_scheme(self):
        """Test URL without scheme."""
        assert is_valid_url("example.com/path") is False

    def test_invalid_url_malformed(self):
        """Test malformed URL strings."""
        assert is_valid_url("ht tp://bad.com") is False