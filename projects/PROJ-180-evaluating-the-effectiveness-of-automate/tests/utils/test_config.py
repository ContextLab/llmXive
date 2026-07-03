"""
Tests for environment configuration management.
"""

import os
import tempfile
from pathlib import Path
import pytest

# Import the module under test
# We need to mock the actual loading to avoid requiring a real .env
import code.utils.config as config_module


class TestConfigLoading:
    """Test configuration loading functionality."""

    def test_load_env_missing_required(self, monkeypatch):
        """Test that loading fails when required env vars are missing."""
        # Ensure _loaded is False
        config_module._loaded = False
        config_module._config = {}
        
        # Remove GITHUB_TOKEN if it exists
        monkeypatch.delenv("GITHUB_TOKEN", raising=False)
        
        # Create a temporary .env file without required vars
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("OPTIONAL_VAR=value\n")
            temp_env_path = f.name
        
        try:
            with pytest.raises(ValueError) as exc_info:
                config_module.load_env(Path(temp_env_path))
            
            assert "GITHUB_TOKEN" in str(exc_info.value)
        finally:
            os.unlink(temp_env_path)
            # Reset state
            config_module._loaded = False
            config_module._config = {}

    def test_load_env_with_required(self, monkeypatch):
        """Test successful loading with required environment variables."""
        # Ensure _loaded is False
        config_module._loaded = False
        config_module._config = {}
        
        # Set required env var
        monkeypatch.setenv("GITHUB_TOKEN", "test_token_123")
        
        # Create a temporary .env file with optional vars
        with tempfile.NamedTemporaryFile(mode='w', suffix='.env', delete=False) as f:
            f.write("MAX_REPOS=50\n")
            f.write("LOG_LEVEL=DEBUG\n")
            temp_env_path = f.name
        
        try:
            result = config_module.load_env(Path(temp_env_path))
            assert result is True
            assert config_module._loaded is True
            assert config_module._config["GITHUB_TOKEN"] == "test_token_123"
            assert config_module._config["MAX_REPOS"] == "50"
            assert config_module._config["LOG_LEVEL"] == "DEBUG"
        finally:
            os.unlink(temp_env_path)
            # Reset state
            config_module._loaded = False
            config_module._config = {}

    def test_get_github_token(self, monkeypatch):
        """Test getting GitHub token."""
        monkeypatch.setenv("GITHUB_TOKEN", "secret_token")
        config_module._loaded = False
        config_module._config = {}
        
        token = config_module.get_github_token()
        assert token == "secret_token"

    def test_get_data_dirs(self, monkeypatch):
        """Test getting data directory paths."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        monkeypatch.setenv("DATA_RAW_DIR", "/custom/raw")
        monkeypatch.setenv("DATA_PROCESSED_DIR", "/custom/processed")
        
        config_module._loaded = False
        config_module._config = {}
        
        assert config_module.get_data_raw_dir() == Path("/custom/raw")
        assert config_module.get_data_processed_dir() == Path("/custom/processed")

    def test_get_max_repos(self, monkeypatch):
        """Test getting max repos configuration."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        monkeypatch.setenv("MAX_REPOS", "100")
        
        config_module._loaded = False
        config_module._config = {}
        
        assert config_module.get_max_repos() == 100

    def test_get_log_level_default(self, monkeypatch):
        """Test default log level."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        
        config_module._loaded = False
        config_module._config = {}
        
        assert config_module.get_log_level() == "INFO"

    def test_validate_paths_creates_dirs(self, monkeypatch, tmp_path):
        """Test that validate_paths creates missing directories."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        
        # Set custom temp directories
        raw_dir = tmp_path / "raw"
        processed_dir = tmp_path / "processed"
        results_dir = tmp_path / "results"
        specs_dir = tmp_path / "specs"
        code_dir = tmp_path / "code"
        
        monkeypatch.setenv("DATA_RAW_DIR", str(raw_dir))
        monkeypatch.setenv("DATA_PROCESSED_DIR", str(processed_dir))
        monkeypatch.setenv("RESULTS_DIR", str(results_dir))
        monkeypatch.setenv("SPECS_DIR", str(specs_dir))
        monkeypatch.setenv("CODE_DIR", str(code_dir))
        
        config_module._loaded = False
        config_module._config = {}
        
        assert not raw_dir.exists()
        
        result = config_module.validate_paths()
        
        assert result is True
        assert raw_dir.exists()
        assert processed_dir.exists()
        assert results_dir.exists()
        assert specs_dir.exists()
        assert code_dir.exists()

    def test_config_singleton_behavior(self, monkeypatch):
        """Test that config is loaded only once."""
        monkeypatch.setenv("GITHUB_TOKEN", "test_token")
        
        config_module._loaded = False
        config_module._config = {}
        
        # First call should load
        config_module.load_env()
        first_call_id = id(config_module._config)
        
        # Second call should not reload
        config_module.load_env()
        second_call_id = id(config_module._config)
        
        assert first_call_id == second_call_id
        assert config_module._loaded is True