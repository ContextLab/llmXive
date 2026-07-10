import pytest
from pathlib import Path
import os
import json
import tempfile
import shutil

from code.config.env_config import (
    ProjectConfig, get_config, get_path, get_param, reset_config, 
    save_config, load_config, _global_config
)

@pytest.fixture(autouse=True)
def clear_global_config():
    """Reset global config before each test to ensure isolation."""
    reset_config()
    yield
    reset_config()

@pytest.fixture
def temp_dir():
    """Create a temporary directory for testing file operations."""
    tmp = tempfile.mkdtemp()
    yield Path(tmp)
    shutil.rmtree(tmp)

def test_get_config_defaults():
    """Test that get_config returns a valid ProjectConfig with defaults."""
    config = get_config()
    assert isinstance(config, ProjectConfig)
    assert config.default_seed == 42
    assert config.bootstrap_resamples == 10000
    assert config.power_sim_iterations == 1000
    assert config.compliance_social_media_max_min == 30
    assert config.compliance_news_blocked is True

def test_get_path_valid_keys():
    """Test get_path with valid keys returns Path objects."""
    config = get_config()
    
    assert get_path('data_raw') == config.data_raw
    assert get_path('data_processed') == config.data_processed
    assert get_path('data_compliance') == config.data_compliance
    assert get_path('results_dir') == config.results_dir
    assert get_path('figures_dir') == config.figures_dir

def test_get_path_invalid_key():
    """Test get_path raises KeyError for invalid keys."""
    with pytest.raises(KeyError):
        get_path('invalid_key')

def test_get_param_valid_keys():
    """Test get_param with valid keys returns correct values."""
    config = get_config()
    
    assert get_param('default_seed') == config.default_seed
    assert get_param('bootstrap_resamples') == config.bootstrap_resamples
    assert get_param('power_sim_iterations') == config.power_sim_iterations
    assert get_param('compliance_social_media_max_min') == config.compliance_social_media_max_min
    assert get_param('compliance_news_blocked') == config.compliance_news_blocked

def test_get_param_invalid_key():
    """Test get_param raises KeyError for invalid keys."""
    with pytest.raises(KeyError):
        get_param('invalid_param')

def test_save_and_load_config(temp_dir):
    """Test saving and loading configuration to/from JSON."""
    config = get_config()
    save_path = temp_dir / "test_config.json"
    
    # Save config
    save_config(config, save_path)
    assert save_path.exists()
    
    # Load config
    loaded_config = load_config(save_path)
    assert loaded_config.default_seed == config.default_seed
    assert loaded_config.bootstrap_resamples == config.bootstrap_resamples
    assert loaded_config.compliance_news_blocked == config.compliance_news_blocked
    
    # Verify paths are preserved as strings in JSON and loaded as Paths
    assert str(loaded_config.data_raw) == str(config.data_raw)

def test_env_variable_override(temp_dir, monkeypatch):
    """Test that environment variables override default configuration."""
    monkeypatch.setenv('DEFAULT_SEED', '12345')
    monkeypatch.setenv('BOOTSTRAP_RESAMPLES', '5000')
    monkeypatch.setenv('DATA_RAW', str(temp_dir / "custom_raw"))
    monkeypatch.setenv('COMPLIANCE_NEWS_BLOCKED', 'false')
    
    # Reset config to force re-reading environment variables
    reset_config()
    config = get_config()
    
    assert config.default_seed == 12345
    assert config.bootstrap_resamples == 5000
    assert config.data_raw == temp_dir / "custom_raw"
    assert config.compliance_news_blocked is False

def test_reset_config():
    """Test that reset_config clears the global config."""
    config1 = get_config()
    reset_config()
    config2 = get_config()
    
    # They should be different instances after reset
    assert config1 is not config2

def test_config_path_resolution(temp_dir, monkeypatch):
    """Test that relative paths are resolved relative to project root."""
    # Set a custom project root
    monkeypatch.setenv('PROJECT_ROOT', str(temp_dir))
    reset_config()
    config = get_config()
    
    # Verify data_raw is absolute and under the project root
    assert config.data_raw.is_absolute()
    assert str(config.data_raw).startswith(str(temp_dir))
    assert config.data_raw.name == "raw"
