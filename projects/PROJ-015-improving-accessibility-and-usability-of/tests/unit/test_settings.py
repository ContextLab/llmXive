"""
Unit tests for the settings configuration module.
"""
import os
import json
import tempfile
import pytest
from pathlib import Path

# Import the module under test
from config.settings import Settings, get_settings, reset_settings, DEFAULT_CONFIG

@pytest.fixture(autouse=True)
def reset_global_settings():
    """Reset global settings before and after each test."""
    reset_settings()
    yield
    reset_settings()

@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        config_data = {
            "study_name": "test_study",
            "n_participants": 15,
            "random_seed": 12345,
            "interface_variants": ["test_interface"]
        }
        json.dump(config_data, f)
        temp_path = f.name
    yield temp_path
    os.unlink(temp_path)

def test_default_settings():
    """Test that default settings are loaded correctly."""
    settings = Settings()
    
    assert settings.study_name == DEFAULT_CONFIG["study_name"]
    assert settings.random_seed == DEFAULT_CONFIG["random_seed"]
    assert settings.n_participants == DEFAULT_CONFIG["n_participants"]
    assert settings.interface_variants == DEFAULT_CONFIG["interface_variants"]

def test_env_variable_override():
    """Test that environment variables override defaults."""
    # Set environment variable
    os.environ["STUDY_N_PARTICIPANTS"] = "99"
    os.environ["STUDY_STUDY_NAME"] = "env_test_study"
    
    try:
        settings = Settings()
        assert settings.n_participants == 99
        assert settings.study_name == "env_test_study"
    finally:
        # Clean up environment
        del os.environ["STUDY_N_PARTICIPANTS"]
        del os.environ["STUDY_STUDY_NAME"]

def test_file_config_override(temp_config_file):
    """Test that config file overrides defaults."""
    settings = Settings(temp_config_file)
    
    assert settings.study_name == "test_study"
    assert settings.n_participants == 15
    assert settings.random_seed == 12345
    assert settings.interface_variants == ["test_interface"]

def test_missing_required_fields():
    """Test that missing required fields raise an error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({"study_name": "test"}, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Missing required configuration fields"):
            Settings(temp_path)
    finally:
        os.unlink(temp_path)

def test_invalid_random_seed():
    """Test that invalid random seed raises an error."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "study_name": "test",
            "n_participants": 10,
            "random_seed": -5
        }, f)
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError, match="Random seed must be non-negative"):
            Settings(temp_path)
    finally:
        os.unlink(temp_path)

def test_get_methods():
    """Test various getter methods."""
    settings = Settings()
    
    # Test get_int
    assert isinstance(settings.get_int("n_participants"), int)
    
    # Test get_float
    assert isinstance(settings.get_float("statistical_alpha"), float)
    
    # Test get_list
    assert isinstance(settings.get_list("interface_variants"), list)
    
    # Test get_dict
    assert isinstance(settings.get_dict("data_dirs"), dict)
    
    # Test get_path
    assert isinstance(settings.get_path("data_dirs.raw"), Path)

def test_property_accessors():
    """Test property accessors."""
    settings = Settings()
    
    assert settings.study_name is not None
    assert settings.random_seed is not None
    assert settings.n_participants is not None
    assert settings.data_raw_dir is not None
    assert settings.data_processed_dir is not None
    assert settings.figures_dir is not None

def test_to_dict():
    """Test conversion to dictionary."""
    settings = Settings()
    config_dict = settings.to_dict()
    
    assert isinstance(config_dict, dict)
    assert "study_name" in config_dict
    assert "random_seed" in config_dict

def test_save_and_load(temp_config_file):
    """Test saving and reloading configuration."""
    settings = Settings()
    new_temp_file = tempfile.mktemp(suffix='.json')
    
    try:
        settings.save_to_file(new_temp_file)
        
        # Load from saved file
        loaded_settings = Settings(new_temp_file)
        
        assert loaded_settings.study_name == settings.study_name
        assert loaded_settings.random_seed == settings.random_seed
    finally:
        if os.path.exists(new_temp_file):
            os.unlink(new_temp_file)

def test_global_settings_singleton():
    """Test that get_settings returns a singleton."""
    settings1 = get_settings()
    settings2 = get_settings()
    
    assert settings1 is settings2

def test_reset_settings():
    """Test resetting the global settings."""
    settings1 = get_settings()
    reset_settings()
    settings2 = get_settings()
    
    assert settings1 is not settings2