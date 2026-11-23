"""
Integration tests for configuration loading.
"""
import pytest
import os
import tempfile
from utils import load_config_env

def test_load_config_from_env():
    """Test loading configuration from environment variables."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up a mock config file
        config_path = os.path.join(tmpdir, "config.yaml")
        with open(config_path, "w") as f:
            f.write("test_key: test_value\n")
        
        os.environ["TEST_CONFIG_PATH"] = config_path
        try:
            config = load_config_env("TEST_CONFIG_PATH")
            assert config["test_key"] == "test_value"
        finally:
            del os.environ["TEST_CONFIG_PATH"]
