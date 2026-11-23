import os
import pytest
from pathlib import Path
import tempfile
from src.utils.env_config import (
    get_required_env_vars,
    validate_environment,
    load_environment_config,
    setup_environment
)

class TestEnvConfig:
    def test_get_required_env_vars(self):
        """Test that the function returns the correct required variables."""
        vars = get_required_env_vars()
        assert "JOYAI_VL_MODEL_PATH" in vars
        assert "DATA_SEED" in vars

    def test_validate_environment_missing_vars(self, monkeypatch):
        """Test validation fails when variables are missing."""
        # Clear existing env vars for this test
        monkeypatch.delenv("JOYAI_VL_MODEL_PATH", raising=False)
        monkeypatch.delenv("DATA_SEED", raising=False)
        
        error = validate_environment()
        assert error is not None
        assert "JOYAI_VL_MODEL_PATH" in error
        assert "DATA_SEED" in error

    def test_validate_environment_invalid_seed(self, monkeypatch):
        """Test validation fails when DATA_SEED is not an integer."""
        monkeypatch.setenv("JOYAI_VL_MODEL_PATH", "/fake/path")
        monkeypatch.setenv("DATA_SEED", "not_an_integer")
        
        error = validate_environment()
        assert error is not None
        assert "DATA_SEED must be an integer" in error

    def test_validate_environment_success(self, monkeypatch):
        """Test validation succeeds with valid inputs."""
        monkeypatch.setenv("JOYAI_VL_MODEL_PATH", "/fake/path")
        monkeypatch.setenv("DATA_SEED", "42")
        
        error = validate_environment()
        assert error is None

    def test_load_environment_config_success(self, monkeypatch):
        """Test loading config returns correct values."""
        monkeypatch.setenv("JOYAI_VL_MODEL_PATH", "/fake/path")
        monkeypatch.setenv("DATA_SEED", "123")
        
        config = load_environment_config()
        assert config["JOYAI_VL_MODEL_PATH"] == "/fake/path"
        assert config["DATA_SEED"] == 123

    def test_load_environment_config_failure(self, monkeypatch):
        """Test loading config raises error if validation fails."""
        monkeypatch.delenv("DATA_SEED", raising=False)
        
        with pytest.raises(ValueError):
            load_environment_config()

    def test_setup_environment_from_file(self, tmp_path):
        """Test setup_environment loads from a .env file."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "JOYAI_VL_MODEL_PATH=/test/model\n"
            "DATA_SEED=99\n"
        )
        
        # Temporarily set project root logic or pass explicit path
        config = setup_environment(env_file)
        
        assert config["JOYAI_VL_MODEL_PATH"] == "/test/model"
        assert config["DATA_SEED"] == 99

    def test_setup_environment_invalid_file(self, tmp_path):
        """Test setup_environment raises error if file has invalid values."""
        env_file = tmp_path / ".env"
        env_file.write_text(
            "JOYAI_VL_MODEL_PATH=/test/model\n"
            "DATA_SEED=invalid\n"
        )
        
        with pytest.raises(ValueError):
            setup_environment(env_file)