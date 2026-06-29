"""
Unit tests for security hardening (T041).

Tests credential masking, secret detection, and logging filters.
"""
import unittest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from security import (
    mask_secret,
    is_secret_key,
    sanitize_dict_for_logging,
    check_for_secret_leaks_in_config
)


class TestMaskSecret(unittest.TestCase):
    """Tests for mask_secret function."""

    def test_long_secret(self):
        """Test masking a long secret."""
        result = mask_secret("very_long_secret_value")
        self.assertTrue(result.startswith("ver"))
        self.assertTrue('*' in result)
        self.assertEqual(len(result), len("very_long_secret_value"))

    def test_short_secret(self):
        """Test masking a short secret."""
        result = mask_secret("abc")
        self.assertEqual(result, "abc")

    def test_empty_secret(self):
        """Test masking empty string."""
        result = mask_secret("")
        self.assertEqual(result, "***")

    def test_custom_visible_length(self):
        """Test with custom visible length."""
        result = mask_secret("secret123", visible_chars=2)
        self.assertEqual(result[:2], "se")
        self.assertEqual(len(result), 9)


class TestIsSecretKey(unittest.TestCase):
    """Tests for is_secret_key function."""

    def test_api_key_variants(self):
        """Test various API key patterns."""
        self.assertTrue(is_secret_key("api_key"))
        self.assertTrue(is_secret_key("API_KEY"))
        self.assertTrue(is_secret_key("Api-Key"))
        self.assertTrue(is_secret_key("apikey"))

    def test_password_variants(self):
        """Test password patterns."""
        self.assertTrue(is_secret_key("password"))
        self.assertTrue(is_secret_key("PASSWORD"))
        self.assertTrue(is_secret_key("user_password"))

    def test_token_variants(self):
        """Test token patterns."""
        self.assertTrue(is_secret_key("auth_token"))
        self.assertTrue(is_secret_key("token"))
        self.assertTrue(is_secret_key("bearer_token"))

    def test_safe_keys(self):
        """Test keys that should not be flagged."""
        self.assertFalse(is_secret_key("username"))
        self.assertFalse(is_secret_key("subject_id"))
        self.assertFalse(is_secret_key("batch_size"))
        self.assertFalse(is_secret_key("config_path"))
        self.assertFalse(is_secret_key("output_dir"))


class TestSanitizeDictForLogging(unittest.TestCase):
    """Tests for sanitize_dict_for_logging function."""

    def test_flatten_dict(self):
        """Test sanitizing a flat dictionary."""
        data = {
            "username": "user123",
            "api_key": "secret123",
            "password": "pass456"
        }
        
        result = sanitize_dict_for_logging(data)
        
        self.assertEqual(result["username"], "user123")
        self.assertNotEqual(result["api_key"], "secret123")
        self.assertNotEqual(result["password"], "pass456")
        self.assertEqual(len(result["api_key"]), len("secret123"))

    def test_nested_dict(self):
        """Test sanitizing a nested dictionary."""
        data = {
            "config": {
                "api_key": "secret",
                "normal": "value"
            }
        }
        
        result = sanitize_dict_for_logging(data)
        
        self.assertNotEqual(result["config"]["api_key"], "secret")
        self.assertEqual(result["config"]["normal"], "value")

    def test_empty_dict(self):
        """Test sanitizing empty dictionary."""
        result = sanitize_dict_for_logging({})
        self.assertEqual(result, {})


class TestCheckForSecretLeaksInConfig(unittest.TestCase):
    """Tests for check_for_secret_leaks_in_config function."""

    def test_detect_leaks(self):
        """Test detection of secret leaks."""
        config = {
            "safe": "value",
            "api_key": "secret",
            "nested": {
                "password": "hidden"
            }
        }
        
        leaks = check_for_secret_leaks_in_config(config)
        
        self.assertIn("api_key", leaks)
        self.assertIn("password", leaks)
        self.assertNotIn("safe", leaks)

    def test_no_leaks(self):
        """Test when no leaks are present."""
        config = {
            "username": "user",
            "batch_size": 10,
            "output_path": "/data"
        }
        
        leaks = check_for_secret_leaks_in_config(config)
        self.assertEqual(len(leaks), 0)


if __name__ == '__main__':
    unittest.main()
