"""Unit tests for environment configuration management."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from code.utils.env_config import (
    EnvConfigError,
    create_env_template,
    ensure_env_file_exists,
    get_hf_token,
    load_env_config,
    validate_env_config,
)


class TestEnvConfig:
    """Tests for environment configuration utilities."""

    def test_create_env_template(self, tmp_path):
        """Test that env template is created with correct content."""
        env_path = tmp_path / ".env"
        
        result = create_env_template(env_path)
        
        assert result is True
        assert env_path.exists()
        
        content = env_path.read_text()
        assert "HF_TOKEN=" in content
        assert "This file is for local development only" in content
        assert "NEVER commit your actual .env file" in content

    def test_ensure_env_file_exists_creates_if_missing(self, tmp_path):
        """Test that ensure_env_file_exists creates .env if missing."""
        env_path = tmp_path / ".env"
        
        with patch("code.utils.env_config.create_env_template", return_value=True):
            result = ensure_env_file_exists(tmp_path)
        
        assert result is True

    def test_ensure_env_file_exists_returns_true_if_exists(self, tmp_path):
        """Test that ensure_env_file_exists returns True if .env exists."""
        env_path = tmp_path / ".env"
        env_path.write_text("HF_TOKEN=test")
        
        result = ensure_env_file_exists(tmp_path)
        
        assert result is True

    def test_load_env_config_loads_variables(self, tmp_path):
        """Test that load_env_config loads environment variables from .env."""
        env_path = tmp_path / ".env"
        env_path.write_text("HF_TOKEN=test_token_123\nOTHER_VAR=value")
        
        with patch("code.utils.env_config.find_dotenv", return_value=str(env_path)):
            with patch("code.utils.env_config.load_dotenv", return_value=True):
                result = load_env_config(tmp_path)
        
        assert result is True

    def test_get_hf_token_returns_token(self, tmp_path):
        """Test that get_hf_token returns the HF token from .env."""
        env_path = tmp_path / ".env"
        env_path.write_text("HF_TOKEN=my_secret_token")
        
        with patch("code.utils.env_config.find_dotenv", return_value=str(env_path)):
            with patch("code.utils.env_config.load_dotenv", return_value=True):
                with patch.dict(os.environ, {"HF_TOKEN": "my_secret_token"}):
                    result = get_hf_token()
        
        assert result == "my_secret_token"

    def test_get_hf_token_raises_when_missing(self, tmp_path):
        """Test that get_hf_token raises EnvConfigError when token is missing."""
        env_path = tmp_path / ".env"
        env_path.write_text("OTHER_VAR=value")
        
        with patch("code.utils.env_config.find_dotenv", return_value=str(env_path)):
            with patch("code.utils.env_config.load_dotenv", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    with pytest.raises(EnvConfigError, match="HF_TOKEN not found"):
                        get_hf_token()

    def test_validate_env_config_passes_with_token(self, tmp_path):
        """Test that validate_env_config passes when HF_TOKEN is present."""
        env_path = tmp_path / ".env"
        env_path.write_text("HF_TOKEN=test_token")
        
        with patch("code.utils.env_config.find_dotenv", return_value=str(env_path)):
            with patch("code.utils.env_config.load_dotenv", return_value=True):
                with patch.dict(os.environ, {"HF_TOKEN": "test_token"}):
                    result = validate_env_config()
        
        assert result is True

    def test_validate_env_config_fails_without_token(self, tmp_path):
        """Test that validate_env_config fails when HF_TOKEN is missing."""
        env_path = tmp_path / ".env"
        env_path.write_text("OTHER_VAR=value")
        
        with patch("code.utils.env_config.find_dotenv", return_value=str(env_path)):
            with patch("code.utils.env_config.load_dotenv", return_value=True):
                with patch.dict(os.environ, {}, clear=True):
                    with pytest.raises(EnvConfigError, match="HF_TOKEN is required"):
                        validate_env_config()

    def test_env_template_has_correct_documentation(self, tmp_path):
        """Test that the env template includes required documentation."""
        env_path = tmp_path / ".env"
        
        create_env_template(env_path)
        
        content = env_path.read_text()
        
        # Check for required documentation sections
        assert "local development only" in content.lower()
        assert "CI/CD" in content or "github actions" in content.lower()
        assert "HF_TOKEN=" in content
        assert "secrets" in content.lower()