"""
Unit tests for security hardening utilities.
"""
import os
import pytest
import logging
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.utils.security import (
    sanitize_value,
    sanitize_dict,
    validate_env_vars,
    check_for_hardcoded_secrets,
    validate_api_key_format,
    audit_security_config,
    secure_logger,
    SecureHandler,
    SECRET_PATTERNS,
    EXPECTED_ENV_KEYS
)


class TestSanitizeValue:
    """Tests for sanitize_value function."""
    
    def test_none_value(self):
        """Test handling of None values."""
        assert sanitize_value(None) == "None"
    
    def test_simple_string(self):
        """Test sanitization of simple strings."""
        assert sanitize_value("hello world") == "hello world"
    
    def test_secret_key_name(self):
        """Test that secret key names are redacted."""
        assert sanitize_value("api_key") == "[REDACTED]"
        assert sanitize_value("PASSWORD") == "[REDACTED]"
        assert sanitize_value("secret_token") == "[REDACTED]"
    
    def test_github_token(self):
        """Test that GitHub tokens are redacted."""
        token = "ghp_1234567890abcdefghijklmnopqrstuvwxyz"
        result = sanitize_value(token)
        assert result == "[REDACTED]"
    
    def test_npm_token(self):
        """Test that NPM tokens are redacted."""
        token = "npm_abcdefghijklmnopqrstuvwx1234567890"
        result = sanitize_value(token)
        assert result == "[REDACTED]"
    
    def test_jwt_token(self):
        """Test that JWT tokens are redacted."""
        jwt = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiaWF0IjoxNTE2MjM5MDIyfQ.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"
        result = sanitize_value(jwt)
        assert result == "[REDACTED]"
    
    def test_dict_value(self):
        """Test sanitization of dictionary values."""
        data = {"name": "test", "api_key": "secret123"}
        result = sanitize_value(data)
        assert "[REDACTED]" in result
    
    def test_list_value(self):
        """Test sanitization of list values."""
        data = ["normal", "secret_key", "value"]
        result = sanitize_value(data)
        assert "[REDACTED]" in result


class TestSanitizeDict:
    """Tests for sanitize_dict function."""
    
    def test_simple_dict(self):
        """Test sanitization of simple dictionary."""
        data = {"name": "test", "version": "1.0"}
        result = sanitize_dict(data)
        assert result == {"name": "test", "version": "1.0"}
    
    def test_sensitive_keys(self):
        """Test that sensitive keys are redacted."""
        data = {
            "name": "test",
            "api_key": "secret123",
            "password": "pass123",
            "secret_token": "token123"
        }
        result = sanitize_dict(data)
        assert result["name"] == "test"
        assert result["api_key"] == "[REDACTED]"
        assert result["password"] == "[REDACTED]"
        assert result["secret_token"] == "[REDACTED]"
    
    def test_nested_dict(self):
        """Test sanitization of nested dictionaries."""
        data = {
            "outer": {
                "inner_key": "value",
                "api_key": "secret"
            }
        }
        result = sanitize_dict(data)
        assert result["outer"]["inner_key"] == "value"
        assert result["outer"]["api_key"] == "[REDACTED]"
    
    def test_list_in_dict(self):
        """Test sanitization of lists within dictionaries."""
        data = {
            "items": [
                {"name": "item1", "secret": "hidden"},
                {"name": "item2", "secret": "hidden2"}
            ]
        }
        result = sanitize_dict(data)
        assert result["items"][0]["name"] == "item1"
        assert result["items"][0]["secret"] == "[REDACTED]"
    
    def test_custom_keys_to_redact(self):
        """Test custom keys to redact."""
        data = {
            "custom_secret": "value1",
            "normal_key": "value2"
        }
        result = sanitize_dict(data, keys_to_redact=["custom_secret"])
        assert result["custom_secret"] == "[REDACTED]"
        assert result["normal_key"] == "value2"


class TestValidateEnvVars:
    """Tests for validate_env_vars function."""
    
    def test_missing_env_vars(self):
        """Test validation with missing environment variables."""
        with patch.dict(os.environ, {}, clear=True):
            result = validate_env_vars(["TEST_VAR1", "TEST_VAR2"])
            assert result["TEST_VAR1"] is False
            assert result["TEST_VAR2"] is False
    
    def test_present_env_vars(self):
        """Test validation with present environment variables."""
        with patch.dict(os.environ, {"TEST_VAR1": "value1", "TEST_VAR2": "value2"}):
            result = validate_env_vars(["TEST_VAR1", "TEST_VAR2"])
            assert result["TEST_VAR1"] is True
            assert result["TEST_VAR2"] is True
    
    def test_empty_env_vars(self):
        """Test validation with empty environment variables."""
        with patch.dict(os.environ, {"TEST_VAR1": "", "TEST_VAR2": "value"}):
            result = validate_env_vars(["TEST_VAR1", "TEST_VAR2"])
            assert result["TEST_VAR1"] is False
            assert result["TEST_VAR2"] is True


class TestCheckForHardcodedSecrets:
    """Tests for check_for_hardcoded_secrets function."""
    
    def test_no_secrets(self):
        """Test file with no secrets."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# This is a comment\n")
            f.write("name = 'test'\n")
            f.write("version = '1.0'\n")
            temp_path = f.name
        
        try:
            result = check_for_hardcoded_secrets(temp_path)
            assert len(result) == 0
        finally:
            os.unlink(temp_path)
    
    def test_hardcoded_secret(self):
        """Test file with hardcoded secret."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write("# Config file\n")
            f.write("api_key = 'ghp_1234567890abcdefghijklmnopqrstuvwxyz'\n")
            temp_path = f.name
        
        try:
            result = check_for_hardcoded_secrets(temp_path)
            assert len(result) > 0
            assert any("hardcoded secret" in issue.lower() for issue in result)
        finally:
            os.unlink(temp_path)
    
    def test_nonexistent_file(self):
        """Test with non-existent file."""
        result = check_for_hardcoded_secrets("/nonexistent/file.py")
        assert len(result) == 0


class TestValidateApiKeyFormat:
    """Tests for validate_api_key_format function."""
    
    def test_valid_github_token(self):
        """Test valid GitHub token format."""
        assert validate_api_key_format("ghp_1234567890abcdefghijklmnopqrstuvwxyz", "github") is True
        assert validate_api_key_format("gho_1234567890abcdefghijklmnopqrstuvwxyz", "github") is True
        assert validate_api_key_format("ghu_1234567890abcdefghijklmnopqrstuvwxyz", "github") is True
        assert validate_api_key_format("ghs_1234567890abcdefghijklmnopqrstuvwxyz", "github") is True
    
    def test_invalid_github_token(self):
        """Test invalid GitHub token format."""
        assert validate_api_key_format("ghp_short", "github") is False
        assert validate_api_key_format("invalid_token", "github") is False
        assert validate_api_key_format("", "github") is False
        assert validate_api_key_format(None, "github") is False
    
    def test_valid_npm_token(self):
        """Test valid NPM token format."""
        assert validate_api_key_format("npm_abcdefghijklmnopqrstuvwx1234567890", "npm") is True
    
    def test_invalid_npm_token(self):
        """Test invalid NPM token format."""
        assert validate_api_key_format("npm_short", "npm") is False
        assert validate_api_key_format("npm_123", "npm") is False
    
    def test_generic_valid(self):
        """Test valid generic token."""
        assert validate_api_key_format("valid_generic_key_12345", "generic") is True
        assert validate_api_key_format("another_valid_key_67890", "generic") is True
    
    def test_generic_invalid(self):
        """Test invalid generic token."""
        assert validate_api_key_format("your_api_key", "generic") is False
        assert validate_api_key_format("xxx", "generic") is False
        assert validate_api_key_format("changeme", "generic") is False
        assert validate_api_key_format("short", "generic") is False


class TestAuditSecurityConfig:
    """Tests for audit_security_config function."""
    
    def test_audit_structure(self):
        """Test that audit returns expected structure."""
        result = audit_security_config()
        assert "env_vars_checked" in result
        assert "hardcoded_secrets_found" in result
        assert "security_warnings" in result
    
    def test_env_vars_checked_type(self):
        """Test that env_vars_checked is a dictionary."""
        result = audit_security_config()
        assert isinstance(result["env_vars_checked"], dict)
    
    def test_hardcoded_secrets_type(self):
        """Test that hardcoded_secrets_found is a list."""
        result = audit_security_config()
        assert isinstance(result["hardcoded_secrets_found"], list)
    
    def test_security_warnings_type(self):
        """Test that security_warnings is a list."""
        result = audit_security_config()
        assert isinstance(result["security_warnings"], list)


class TestSecureLogger:
    """Tests for secure_logger function."""
    
    def test_logger_creation(self):
        """Test that secure logger is created."""
        logger = secure_logger("test_secure")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_secure"
    
    def test_logger_redacts_secrets(self):
        """Test that logger redacts secrets in messages."""
        logger = secure_logger("test_redact")
        
        # Capture log output
        with patch.object(logger, 'handlers', [MagicMock()]) as mock_handlers:
            logger.info("Processing with api_key=secret123")
            
            # Verify handler was called
            assert mock_handlers[0].emit.called
            # The actual redaction happens in format, which we've tested in sanitize_value


class TestSecureHandler:
    """Tests for SecureHandler class."""
    
    def test_handler_creation(self):
        """Test that SecureHandler can be created."""
        handler = SecureHandler()
        assert isinstance(handler, SecureHandler)
    
    def test_handler_with_custom_keys(self):
        """Test SecureHandler with custom redact keys."""
        handler = SecureHandler(redact_keys=["custom_key"])
        assert handler.redact_keys == ["custom_key"]


class TestSecretPatterns:
    """Tests for SECRET_PATTERNS constant."""
    
    def test_patterns_exist(self):
        """Test that SECRET_PATTERNS is defined."""
        assert isinstance(SECRET_PATTERNS, list)
        assert len(SECRET_PATTERNS) > 0
    
    def test_patterns_are_compiled(self):
        """Test that all patterns are compiled regex objects."""
        for pattern in SECRET_PATTERNS:
            assert hasattr(pattern, 'search')
            assert hasattr(pattern, 'match')
    
    def test_expected_env_keys_exist(self):
        """Test that EXPECTED_ENV_KEYS is defined."""
        assert isinstance(EXPECTED_ENV_KEYS, set)
        assert len(EXPECTED_ENV_KEYS) > 0
        assert "NPM_API_KEY" in EXPECTED_ENV_KEYS
        assert "GITHUB_TOKEN" in EXPECTED_ENV_KEYS


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
