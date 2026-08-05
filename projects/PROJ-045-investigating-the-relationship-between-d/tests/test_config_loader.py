import os
import tempfile
import pytest
from pathlib import Path
from utils import load_config

def test_load_config_from_yaml():
    """Test loading config from a YAML file."""
    config_content = """
    data_dir: "test_data"
    log_level: "DEBUG"
    api_timeout: 60
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    try:
        config = load_config(temp_path)
        assert config["data_dir"] == "test_data"
        assert config["log_level"] == "DEBUG"
        assert config["api_timeout"] == 60
    finally:
        os.unlink(temp_path)

def test_load_config_from_env_vars():
    """Test that environment variables override YAML config."""
    # Set up a temporary YAML file
    config_content = """
    data_dir: "yaml_data"
    log_level: "INFO"
    """
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write(config_content)
        temp_path = f.name

    # Set environment variables
    os.environ["PROJ_045_DATA_DIR"] = "env_data"
    os.environ["PROJ_045_LOG_LEVEL"] = "WARNING"
    os.environ["PROJ_045_API_TIMEOUT"] = "120"

    try:
        config = load_config(temp_path)
        # Env vars should override YAML
        assert config["data_dir"] == "env_data"
        assert config["log_level"] == "WARNING"
        assert config["api_timeout"] == 120
    finally:
        os.unlink(temp_path)
        del os.environ["PROJ_045_DATA_DIR"]
        del os.environ["PROJ_045_LOG_LEVEL"]
        del os.environ["PROJ_045_API_TIMEOUT"]

def test_load_config_missing_file():
    """Test loading config when YAML file is missing (should return empty dict or env only)."""
    config = load_config("non_existent_file.yaml")
    # Should not crash, may return empty dict if no env vars set
    assert isinstance(config, dict)

def test_load_config_boolean_parsing():
    """Test that boolean strings are parsed correctly."""
    os.environ["PROJ_045_USE_GPU"] = "true"
    os.environ["PROJ_045_USE_GPU_FALSE"] = "false" # Not mapped, but good to know behavior
    
    # Create a dummy config to load
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("use_gpu: false\n")
        temp_path = f.name
    
    try:
        config = load_config(temp_path)
        # The env var PROJ_045_USE_GPU maps to 'use_gpu' key
        assert config["use_gpu"] is True
    finally:
        os.unlink(temp_path)
        if "PROJ_045_USE_GPU" in os.environ:
            del os.environ["PROJ_045_USE_GPU"]