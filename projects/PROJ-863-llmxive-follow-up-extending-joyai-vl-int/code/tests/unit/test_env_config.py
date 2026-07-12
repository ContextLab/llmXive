"""
Unit tests for environment configuration validation.
"""
import os
import pytest
from pathlib import Path
import tempfile

# Import the module under test
from src.utils.env_config import (
    validate_environment,
    load_environment_config,
    get_required_env_vars,
    ENV_MODEL_PATH,
    ENV_DATA_SEED
)

class TestEnvConfig:
    
    def test_get_required_env_vars(self):
        """Test that the correct variable names are returned."""
        model_var, seed_var = get_required_env_vars()
        assert model_var == "JOYAI_VL_MODEL_PATH"
        assert seed_var == "DATA_SEED"

    def test_validate_missing_model_path(self, monkeypatch):
        """Test validation fails when model path is missing."""
        monkeypatch.delenv(ENV_MODEL_PATH, raising=False)
        monkeypatch.setenv(ENV_DATA_SEED, "42")
        
        is_valid, error_msg = validate_environment()
        assert is_valid is False
        assert ENV_MODEL_PATH in error_msg

    def test_validate_missing_data_seed(self, monkeypatch, tmp_path):
        """Test validation fails when data seed is missing."""
        monkeypatch.setenv(ENV_MODEL_PATH, str(tmp_path))
        monkeypatch.delenv(ENV_DATA_SEED, raising=False)
        
        is_valid, error_msg = validate_environment()
        assert is_valid is False
        assert ENV_DATA_SEED in error_msg

    def test_validate_invalid_model_path(self, monkeypatch):
        """Test validation fails when model path does not exist."""
        monkeypatch.setenv(ENV_MODEL_PATH, "/nonexistent/path/xyz")
        monkeypatch.setenv(ENV_DATA_SEED, "42")
        
        is_valid, error_msg = validate_environment()
        assert is_valid is False
        assert "does not exist" in error_msg

    def test_validate_invalid_seed_type(self, monkeypatch, tmp_path):
        """Test validation fails when data seed is not an integer."""
        monkeypatch.setenv(ENV_MODEL_PATH, str(tmp_path))
        monkeypatch.setenv(ENV_DATA_SEED, "not_a_number")
        
        is_valid, error_msg = validate_environment()
        assert is_valid is False
        assert "valid integer" in error_msg

    def test_validate_success(self, monkeypatch, tmp_path):
        """Test validation passes with correct inputs."""
        monkeypatch.setenv(ENV_MODEL_PATH, str(tmp_path))
        monkeypatch.setenv(ENV_DATA_SEED, "12345")
        
        is_valid, error_msg = validate_environment()
        assert is_valid is True
        assert error_msg == ""

    def test_load_environment_config_success(self, monkeypatch, tmp_path):
        """Test loading config returns correct dictionary."""
        monkeypatch.setenv(ENV_MODEL_PATH, str(tmp_path))
        monkeypatch.setenv(ENV_DATA_SEED, "999")
        
        config = load_environment_config()
        assert config["model_path"] == str(tmp_path)
        assert config["data_seed"] == 999

    def test_load_environment_config_failure(self, monkeypatch, tmp_path):
        """Test loading config raises ValueError on invalid input."""
        monkeypatch.setenv(ENV_MODEL_PATH, str(tmp_path))
        monkeypatch.setenv(ENV_DATA_SEED, "invalid")
        
        with pytest.raises(ValueError):
            load_environment_config()
