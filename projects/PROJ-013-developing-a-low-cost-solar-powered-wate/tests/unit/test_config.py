"""
Unit tests for the configuration management module.
"""
import os
import tempfile
from pathlib import Path
import pytest

from code.config import Config, get_config, reload_config
from code.utils import ProjectError

@pytest.fixture
def temp_env_file():
    """Create a temporary .env file for testing."""
    content = (
        "NASA_POWER_API_KEY=test_key_123\n"
        "SIMULATION_TIME_HOURS=48\n"
        "DEFAULT_LATITUDE=10.5\n"
    )
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.env') as f:
        f.write(content)
        temp_path = Path(f.name)
    yield temp_path
    os.unlink(temp_path)

def test_config_loads_from_env_file(temp_env_file):
    """Test that Config loads values from a .env file."""
    config = Config(env_path=temp_env_file)
    
    assert config.nasa_power_api_key == "test_key_123"
    assert config.simulation_time_hours == 48
    assert config.default_latitude == 10.5

def test_config_overrides_env_with_os_environ(temp_env_file):
    """Test that os.environ overrides .env file values."""
    # Set an environment variable
    os.environ["NASA_POWER_API_KEY"] = "os_env_key"
    
    try:
        config = Config(env_path=temp_env_file)
        # Should use the OS environment variable, not the .env file
        assert config.nasa_power_api_key == "os_env_key"
    finally:
        del os.environ["NASA_POWER_API_KEY"]

def test_config_uses_defaults_when_missing():
    """Test that Config uses default values when env vars are missing."""
    # Ensure no conflicting env vars
    if "NASA_POWER_API_KEY" in os.environ:
        del os.environ["NASA_POWER_API_KEY"]
    
    config = Config()
    
    assert config.nasa_power_api_key is None
    assert config.nasa_power_base_url == "https://power.larc.nasa.gov/api"
    assert config.simulation_time_hours == 24
    assert config.default_latitude == 0.0

def test_get_required_raises_on_missing():
    """Test that get_required raises ProjectError for missing keys."""
    config = Config()
    
    with pytest.raises(ProjectError) as exc_info:
        config.get_required("NASA_POWER_API_KEY")
    
    assert "missing" in str(exc_info.value).lower()

def test_get_required_returns_value_when_present(temp_env_file):
    """Test that get_required returns the value when present."""
    config = Config(env_path=temp_env_file)
    
    value = config.get_required("NASA_POWER_API_KEY")
    assert value == "test_key_123"

def test_global_config_singleton():
    """Test that get_config returns a singleton instance."""
    # Clear any existing instance
    reload_config()
    
    config1 = get_config()
    config2 = get_config()
    
    assert config1 is config2

def test_reload_config_creates_new_instance(temp_env_file):
    """Test that reload_config creates a new instance with updated values."""
    config1 = reload_config()
    
    # Modify the temp file
    with open(temp_env_file, 'w') as f:
        f.write("NASA_POWER_API_KEY=new_key_456\n")
    
    config2 = reload_config(env_path=temp_env_file)
    
    assert config1 is not config2
    assert config2.nasa_power_api_key == "new_key_456"

def test_to_dict_returns_copy():
    """Test that to_dict returns a copy of the config."""
    config = Config()
    config_dict = config.to_dict()
    
    # Modify the returned dict
    config_dict["TEST_KEY"] = "test_value"
    
    # Ensure original config is not affected
    assert config.get("TEST_KEY") is None

def test_invalid_integer_falls_back_to_default(temp_env_file):
    """Test that invalid integer values fall back to defaults."""
    # Create a file with invalid integer
    with open(temp_env_file, 'w') as f:
        f.write("SIMULATION_TIME_HOURS=not_a_number\n")
    
    config = Config(env_path=temp_env_file)
    
    # Should use default value (24)
    assert config.simulation_time_hours == 24