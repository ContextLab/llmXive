"""
Unit tests for environment configuration utilities.
"""
import os
import tempfile
import pytest
from pathlib import Path
from code.utils.env_config import (
    EnvConfigError,
    load_env_config,
    get_hf_token,
    validate_env_config,
    create_env_template,
    ensure_env_file_exists
)


class TestEnvConfig:
    """Tests for env_config module."""

    def test_create_env_template(self, tmp_path):
        """Test that create_env_template generates a valid file."""
        output_path = tmp_path / ".env.example"
        template_vars = {
            "HF_TOKEN": "Test Token Description",
            "API_KEY": "Another Key Description"
        }
        
        create_env_template(output_path, template_vars)
        
        assert output_path.exists()
        content = output_path.read_text()
        
        # Check that all variables are present
        for var in template_vars:
            assert f"{var}=" in content
            
        # Check that descriptions are present
        for desc in template_vars.values():
            assert desc in content

    def test_ensure_env_file_exists_creates_from_template(self, tmp_path):
        """Test that ensure_env_file_exists copies from .env.example if missing."""
        # Create a fake .env.example
        example_path = tmp_path / ".env.example"
        example_path.write_text("HF_TOKEN=placeholder\n")
        
        env_path = tmp_path / ".env"
        
        # Call the function
        result = ensure_env_file_exists(env_path)
        
        assert result == env_path
        assert env_path.exists()
        assert env_path.read_text() == "HF_TOKEN=placeholder\n"

    def test_ensure_env_file_exists_noop_if_exists(self, tmp_path):
        """Test that ensure_env_file_exists does nothing if .env already exists."""
        env_path = tmp_path / ".env"
        env_path.write_text("EXISTING=value\n")
        
        result = ensure_env_file_exists(env_path)
        
        assert result == env_path
        assert env_path.read_text() == "EXISTING=value\n"

    def test_get_hf_token_raises_when_missing_and_required(self):
        """Test that get_hf_token raises EnvConfigError when required and missing."""
        # Ensure HF_TOKEN is not set
        original = os.environ.pop("HF_TOKEN", None)
        
        try:
            with pytest.raises(EnvConfigError, match="HF_TOKEN is not set"):
                get_hf_token(required=True)
        finally:
            # Restore original state
            if original:
                os.environ["HF_TOKEN"] = original

    def test_get_hf_token_returns_none_when_missing_and_not_required(self):
        """Test that get_hf_token returns None when not required and missing."""
        original = os.environ.pop("HF_TOKEN", None)
        
        try:
            result = get_hf_token(required=False)
            assert result is None
        finally:
            if original:
                os.environ["HF_TOKEN"] = original

    def test_get_hf_token_returns_value_when_present(self, monkeypatch):
        """Test that get_hf_token returns the token when present."""
        monkeypatch.setenv("HF_TOKEN", "test_token_123")
        
        result = get_hf_token(required=True)
        assert result == "test_token_123"

    def test_validate_env_config_passes_when_all_present(self, monkeypatch):
        """Test validate_env_config when all required vars are present."""
        monkeypatch.setenv("VAR1", "value1")
        monkeypatch.setenv("VAR2", "value2")
        
        result = validate_env_config(["VAR1", "VAR2"])
        
        assert result == {"VAR1": True, "VAR2": True}

    def test_validate_env_config_raises_when_missing(self, monkeypatch):
        """Test validate_env_config raises when a required var is missing."""
        monkeypatch.setenv("VAR1", "value1")
        # VAR2 is not set
        
        with pytest.raises(EnvConfigError, match="Missing or empty required environment variables"):
            validate_env_config(["VAR1", "VAR2"])