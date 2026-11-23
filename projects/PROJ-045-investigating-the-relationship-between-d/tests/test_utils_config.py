"""
Tests for environment configuration management (T007).
"""
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import the function under test
# We need to ensure we are testing the actual implementation in utils.py
import sys
import importlib

# Ensure we are importing from the project code directory
code_dir = Path(__file__).parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from utils import load_config, _resolve_log_level

class TestConfigLoading:
    def test_load_config_from_file(self, tmp_path):
        """Test loading config from a YAML file."""
        config_content = {
            "project": {"name": "test_project"},
            "logging": {"level": "DEBUG"}
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        config = load_config(config_file)
        
        assert config["project"]["name"] == "test_project"
        assert config["logging"]["level"] == "DEBUG"

    def test_load_config_missing_file(self, tmp_path):
        """Test behavior when config file is missing."""
        non_existent = tmp_path / "non_existent.yaml"
        config = load_config(non_existent)
        
        # Should return empty dict or defaults, not crash
        assert isinstance(config, dict)

    def test_env_var_override(self, tmp_path):
        """Test that environment variables override config file values."""
        config_content = {
            "logging": {"level": "INFO"},
            "data": {"raw_dir": "data/raw"}
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        # Set environment variable
        os.environ["PROJ_LOGGING_LEVEL"] = "WARNING"
        
        try:
            config = load_config(config_file)
            assert config["logging"]["level"] == "WARNING"
        finally:
            # Clean up env var
            del os.environ["PROJ_LOGGING_LEVEL"]

    def test_nested_env_var_override(self, tmp_path):
        """Test environment variable override for nested keys."""
        config_content = {
            "data": {"raw_dir": "data/raw", "processed_dir": "data/processed"}
        }
        config_file = tmp_path / "config.yaml"
        with open(config_file, "w") as f:
            yaml.dump(config_content, f)

        os.environ["PROJ_DATA_RAW_DIR"] = "custom/raw"
        
        try:
            config = load_config(config_file)
            assert config["data"]["raw_dir"] == "custom/raw"
            # Other keys should remain unchanged
            assert config["data"]["processed_dir"] == "data/processed"
        finally:
            del os.environ["PROJ_DATA_RAW_DIR"]

class TestLogLevelResolution:
    def test_resolve_string_level(self):
        """Test resolving string log levels."""
        assert _resolve_log_level("DEBUG") == 10
        assert _resolve_log_level("INFO") == 20
        assert _resolve_log_level("WARNING") == 30
        assert _resolve_log_level("WARN") == 30
        assert _resolve_log_level("ERROR") == 40
        assert _resolve_log_level("CRITICAL") == 50

    def test_resolve_integer_level(self):
        """Test resolving integer log levels."""
        assert _resolve_log_level(10) == 10
        assert _resolve_log_level(20) == 20
        assert _resolve_log_level(30) == 30

    def test_resolve_invalid_level(self):
        """Test that invalid log levels raise ValueError."""
        with pytest.raises(ValueError, match="Unknown level"):
            _resolve_log_level("INVALID_LEVEL")
        
        with pytest.raises(ValueError, match="Unknown level type"):
            _resolve_log_level(3.14)
