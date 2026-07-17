"""
Unit tests for the secrets management module.
"""
import os
import pytest
from unittest.mock import patch, MagicMock
from pathlib import Path
import tempfile

# Import the module to test
import sys
sys.path.insert(0, 'code')
from secrets import (
    SecretsManager,
    get_secrets_manager,
    get_api_key,
    validate_hf_token,
    validate_prolific_token,
    create_env_template_file,
    REQUIRED_KEYS,
    OPTIONAL_KEYS
)


class TestSecretsManager:
    """Tests for the SecretsManager class."""

    def setup_method(self):
        """Set up test fixtures before each test."""
        # Clear the global instance to ensure clean state
        import secrets
        secrets._secrets_manager = None
        
        # Store original environment
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Clean up after each test."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)
        
        # Clear the global instance
        import secrets
        secrets._secrets_manager = None

    def test_missing_required_keys_raises_error(self):
        """Test that missing required keys raise ValueError."""
        # Ensure no required keys are set
        for key in REQUIRED_KEYS:
            os.environ.pop(key, None)
        
        with pytest.raises(ValueError) as exc_info:
            SecretsManager()
        
        assert "Missing required API keys" in str(exc_info.value)
        for key in REQUIRED_KEYS:
            assert key in str(exc_info.value)

    def test_all_required_keys_load_successfully(self):
        """Test that all required keys are loaded when present."""
        # Set all required keys
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        manager = SecretsManager()
        secrets_dict = manager.get_all()
        
        assert len(secrets_dict) == len(REQUIRED_KEYS)
        for key in REQUIRED_KEYS:
            assert key in secrets_dict
            assert secrets_dict[key] == f"test_{key}_value"

    def test_get_method_returns_correct_value(self):
        """Test the get method returns correct values."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        manager = SecretsManager()
        
        for key in REQUIRED_KEYS:
            assert manager.get(key) == f"test_{key}_value"

    def test_get_with_default_for_optional_keys(self):
        """Test get method with default for optional keys."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        manager = SecretsManager()
        
        # Test with default value
        assert manager.get("SLACK_WEBHOOK_URL", "default_value") == "default_value"
        
        # Test without default (should return None)
        assert manager.get("SLACK_WEBHOOK_URL") is None

    def test_get_missing_required_key_raises_keyerror(self):
        """Test that getting a non-existent key raises KeyError."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        manager = SecretsManager()
        
        with pytest.raises(KeyError) as exc_info:
            manager.get("NON_EXISTENT_KEY")
        
        assert "NON_EXISTENT_KEY" in str(exc_info.value)

    def test_check_key_valid_returns_true_for_valid_key(self):
        """Test check_key_valid returns True for valid keys."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        manager = SecretsManager()
        
        for key in REQUIRED_KEYS:
            assert manager.check_key_valid(key) is True

    def test_check_key_valid_returns_false_for_invalid_key(self):
        """Test check_key_valid returns False for missing keys."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        manager = SecretsManager()
        
        assert manager.check_key_valid("SLACK_WEBHOOK_URL") is False


class TestGetApiKey:
    """Tests for the get_api_key convenience function."""

    def setup_method(self):
        """Set up test fixtures."""
        import secrets
        secrets._secrets_manager = None
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Clean up."""
        os.environ.clear()
        os.environ.update(self.original_env)
        import secrets
        secrets._secrets_manager = None

    def test_get_api_key_returns_correct_value(self):
        """Test get_api_key returns correct values."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        for key in REQUIRED_KEYS:
            assert get_api_key(key) == f"test_{key}_value"

    def test_get_api_key_raises_value_error_for_missing_required(self):
        """Test get_api_key raises ValueError for missing required keys."""
        # Only set some keys
        if len(REQUIRED_KEYS) > 1:
            os.environ[REQUIRED_KEYS[0]] = "test_value"
            # Don't set the second one
            
            with pytest.raises(ValueError):
                get_api_key(REQUIRED_KEYS[1])


class TestTokenValidation:
    """Tests for token validation functions."""

    def setup_method(self):
        """Set up test fixtures."""
        import secrets
        secrets._secrets_manager = None
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Clean up."""
        os.environ.clear()
        os.environ.update(self.original_env)
        import secrets
        secrets._secrets_manager = None

    def test_validate_hf_token_with_valid_token(self):
        """Test HF token validation with valid format."""
        os.environ["HF_TOKEN"] = "hf_valid_token_that_is_long_enough_12345"
        
        assert validate_hf_token() is True

    def test_validate_hf_token_with_invalid_format(self):
        """Test HF token validation with invalid format."""
        os.environ["HF_TOKEN"] = "invalid_token"
        
        assert validate_hf_token() is False

    def test_validate_hf_token_with_empty_token(self):
        """Test HF token validation with empty token."""
        os.environ["HF_TOKEN"] = ""
        
        assert validate_hf_token() is False

    def test_validate_prolific_token_with_valid_token(self):
        """Test Prolific token validation with valid format."""
        os.environ["PROLIFIC_API_TOKEN"] = "a" * 20  # Long enough alphanumeric
        
        assert validate_prolific_token() is True

    def test_validate_prolific_token_with_invalid_format(self):
        """Test Prolific token validation with invalid format."""
        os.environ["PROLIFIC_API_TOKEN"] = "a" * 5  # Too short
        
        assert validate_prolific_token() is False

    def test_validate_hf_token_with_explicit_token(self):
        """Test HF token validation with explicit token parameter."""
        assert validate_hf_token("hf_valid_token_that_is_long_enough_12345") is True
        assert validate_hf_token("invalid") is False

    def test_validate_prolific_token_with_explicit_token(self):
        """Test Prolific token validation with explicit token parameter."""
        assert validate_prolific_token("a" * 20) is True
        assert validate_prolific_token("a" * 5) is False


class TestCreateEnvTemplateFile:
    """Tests for create_env_template_file function."""

    def test_creates_env_template_file(self):
        """Test that the function creates the template file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = os.path.join(tmpdir, ".env.example")
            
            create_env_template_file(output_path)
            
            assert os.path.exists(output_path)
            
            content = Path(output_path).read_text()
            assert "HF_TOKEN=" in content
            assert "PROLIFIC_API_TOKEN=" in content
            assert "your_huggingface_token_here" in content
            assert "your_prolific_token_here" in content
            assert "SLACK_WEBHOOK_URL" in content

    def test_default_output_path(self):
        """Test default output path is .env.example."""
        with tempfile.TemporaryDirectory() as tmpdir:
            original_cwd = os.getcwd()
            try:
                os.chdir(tmpdir)
                create_env_template_file()
                assert os.path.exists(".env.example")
            finally:
                os.chdir(original_cwd)


class TestGlobalInstance:
    """Tests for global secrets manager instance."""

    def setup_method(self):
        """Set up test fixtures."""
        import secrets
        secrets._secrets_manager = None
        self.original_env = os.environ.copy()

    def teardown_method(self):
        """Clean up."""
        os.environ.clear()
        os.environ.update(self.original_env)
        import secrets
        secrets._secrets_manager = None

    def test_get_secrets_manager_returns_same_instance(self):
        """Test that get_secrets_manager returns the same instance."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        instance1 = get_secrets_manager()
        instance2 = get_secrets_manager()
        
        assert instance1 is instance2

    def test_get_secrets_manager_creates_instance_if_none(self):
        """Test that get_secrets_manager creates instance if none exists."""
        for key in REQUIRED_KEYS:
            os.environ[key] = f"test_{key}_value"
        
        instance = get_secrets_manager()
        assert instance is not None
        assert isinstance(instance, SecretsManager)