import pytest
import yaml
from pathlib import Path
import sys
import os

# Add project root to path if needed
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.astm_g59_parser import (
    load_astm_tolerance_config,
    get_tolerance_value,
    get_tolerance_source_info,
    validate_tolerance_for_comparison
)
from utils.exceptions import DataInsufficientError

@pytest.fixture
def valid_config_path():
    return "config/astm_g59_tolerance.yaml"

@pytest.fixture
def config_data(valid_config_path):
    return load_astm_tolerance_config(valid_config_path)

def test_load_config_exists(valid_config_path):
    """Test that the config file exists and loads correctly."""
    path = Path(valid_config_path)
    assert path.exists(), f"Config file not found at {valid_config_path}"
    
    config = load_astm_tolerance_config(valid_config_path)
    assert isinstance(config, dict)
    assert "tolerance_source" in config
    assert "absolute_tolerance_mv" in config
    assert "relative_tolerance_percent" in config

def test_absolute_tolerance_missing_raises_error(config_data):
    """
    Test that get_tolerance_value raises DataInsufficientError when 
    absolute_tolerance_mv is null.
    """
    # The config should have absolute_tolerance_mv as null per the standard
    assert config_data.get("absolute_tolerance_mv") is None
    
    with pytest.raises(DataInsufficientError) as excinfo:
        get_tolerance_value(config_data, tolerance_type="absolute")
    
    assert "ASTM G59 standard does not define a specific absolute prediction error tolerance" in str(excinfo.value)

def test_relative_tolerance_exists(config_data):
    """Test that relative tolerance is present."""
    value = get_tolerance_value(config_data, tolerance_type="relative")
    assert value is not None
    assert value == 20.0

def test_source_info(config_data):
    """Test source info extraction."""
    info = get_tolerance_source_info(config_data)
    assert info["source"] == "ASTM G59-97(2014)"
    assert info["defined_absolute"] is False
    assert info["defined_relative"] is True

def test_validate_tolerance_absolute_mode_fails(config_data):
    """Test validation fails for absolute mode when value is null."""
    is_valid, msg = validate_tolerance_for_comparison(config_data, comparison_mode="absolute")
    assert is_valid is False
    assert "Absolute tolerance is required but not defined" in msg

def test_validate_tolerance_relative_mode_passes(config_data):
    """Test validation passes for relative mode."""
    is_valid, msg = validate_tolerance_for_comparison(config_data, comparison_mode="relative")
    assert is_valid is True
    assert "Relative tolerance of 20.0% is available" in msg
