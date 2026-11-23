import os
import tempfile
from pathlib import Path
import pytest
from code.config.env_config import (
    ConfigError,
    EnvironmentConfig,
    get_env_config,
    reload_config,
)

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    with tempfile.NamedTemporaryFile(
        mode="w", suffix=".env", delete=False
    ) as f:
        f.write("LOG_LEVEL=DEBUG\n")
        f.write("SAMPLING_RATE_THRESHOLD=1000\n")
        f.write("RANDOM_SEED=123\n")
        f.write("DATA_DIR=/custom/data\n")
        env_path = f.name
    yield env_path
    os.unlink(env_path)

def test_default_values():
    """Test that default values are set correctly."""
    config = EnvironmentConfig()
    assert config.get("LOG_LEVEL") == "INFO"
    assert config.get_int("SAMPLING_RATE_THRESHOLD") == 500
    assert config.get_int("TRIAL_ODDBALL_MIN") == 100
    assert config.get_int("TRIAL_STANDARD_MIN") == 300
    assert config.get_int("RANDOM_SEED") == 42

def test_env_file_loading(temp_env_file):
    """Test that values are loaded from .env file."""
    config = EnvironmentConfig(env_path=temp_env_file)
    assert config.get("LOG_LEVEL") == "DEBUG"
    assert config.get_int("SAMPLING_RATE_THRESHOLD") == 1000
    assert config.get_int("RANDOM_SEED") == 123
    assert config.get("DATA_DIR") == "/custom/data"

def test_invalid_sampling_rate():
    """Test validation of negative sampling rate."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("SAMPLING_RATE_THRESHOLD=-100\n")
        env_path = f.name
    
    try:
        with pytest.raises(ConfigError, match="must be positive"):
            EnvironmentConfig(env_path=env_path)
    finally:
        os.unlink(env_path)

def test_invalid_log_level():
    """Test validation of invalid log level."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("LOG_LEVEL=INVALID\n")
        env_path = f.name
    
    try:
        with pytest.raises(ConfigError, match="Invalid LOG_LEVEL"):
            EnvironmentConfig(env_path=env_path)
    finally:
        os.unlink(env_path)

def test_get_int():
    """Test integer conversion."""
    config = EnvironmentConfig()
    assert isinstance(config.get_int("SAMPLING_RATE_THRESHOLD"), int)

def test_get_float():
    """Test float conversion."""
    config = EnvironmentConfig()
    assert isinstance(config.get_float("TIME_WINDOW_START"), float)

def test_get_bool():
    """Test boolean conversion."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".env", delete=False) as f:
        f.write("DEBUG_MODE=true\n")
        f.write("VERBOSE=1\n")
        f.write("QUIET=no\n")
        env_path = f.name
    
    try:
        config = EnvironmentConfig(env_path=env_path)
        assert config.get_bool("DEBUG_MODE") is True
        assert config.get_bool("VERBOSE") is True
        assert config.get_bool("QUIET") is False
    finally:
        os.unlink(env_path)

def test_get_path():
    """Test Path conversion."""
    config = EnvironmentConfig()
    data_path = config.get_path("DATA_DIR")
    assert isinstance(data_path, Path)

def test_to_dict():
    """Test dictionary export."""
    config = EnvironmentConfig()
    config_dict = config.to_dict()
    assert isinstance(config_dict, dict)
    assert "LOG_LEVEL" in config_dict

def test_missing_key():
    """Test error on missing key."""
    config = EnvironmentConfig()
    with pytest.raises(ConfigError):
        config.get_int("NONEXISTENT_KEY")

def test_reload_config():
    """Test configuration reload."""
    config1 = get_env_config()
    config2 = reload_config()
    assert config1 is not config2

def test_global_instance():
    """Test global config instance."""
    config1 = get_env_config()
    config2 = get_env_config()
    assert config1 is config2