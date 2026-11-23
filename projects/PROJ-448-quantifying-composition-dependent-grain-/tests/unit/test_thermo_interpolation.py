"""
Unit tests for ternary parameter interpolation functionality.
"""
import pytest
import json
import logging
from pathlib import Path
import tempfile
import os
from unittest.mock import patch, MagicMock
import numpy as np
from sklearn.linear_model import LinearRegression
from errors import ThermodynamicError, ConfigurationError

# Import the module under test
from code.services.thermo_interpolation import (
    interpolate_ternary_parameters,
    set_no_ternary_data_flag,
    validate_and_interpolate_ternary,
    load_binary_parameters,
    MANIFEST_PATH
)

@pytest.fixture
def temp_manifest():
    """Create a temporary manifest file for testing."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "systems": [
                {"name": "Fe-Cr-Mo", "data": "test"},
                {"name": "Fe-Cr-V", "data": "test"}
            ]
        }, f)
        temp_path = f.name
    
    # Temporarily override MANIFEST_PATH
    original_path = MANIFEST_PATH
    MANIFEST_PATH = Path(temp_path)
    
    yield temp_path
    
    # Cleanup
    os.unlink(temp_path)
    # Restore original path
    MANIFEST_PATH = original_path

def test_load_binary_parameters():
    """Test loading binary interaction parameters."""
    params = load_binary_parameters("Fe-Cr", 1000)
    assert "L0" in params
    assert "L1" in params
    assert "L2" in params
    assert isinstance(params["L0"], float)

def test_load_binary_parameters_not_found():
    """Test error handling for missing binary parameters."""
    with pytest.raises(ThermodynamicError):
        load_binary_parameters("NonExistent-System", 1000)

def test_interpolate_ternary_parameters():
    """Test linear interpolation of ternary parameters."""
    binary_systems = ["Fe-Cr", "Fe-Mo", "Cr-Mo"]
    params = interpolate_ternary_parameters("Fe-Cr-Mo", 1000, binary_systems)
    
    assert "L0" in params
    assert "L1" in params
    assert "L2" in params
    assert params["interpolation_method"] == "linear_regression"
    assert params["binary_sources"] == binary_systems
    assert params["temperature"] == 1000

def test_interpolate_with_insufficient_binary_data():
    """Test error handling with insufficient binary data."""
    with pytest.raises(ThermodynamicError):
        interpolate_ternary_parameters("Fe-Cr-Mo", 1000, ["Fe-Cr"])

def test_set_no_ternary_data_flag(temp_manifest):
    """Test setting the NO_TERNARY_DATA flag in manifest."""
    # Update the MANIFEST_PATH to point to our temp file
    import code.services.thermo_interpolation as module
    module.MANIFEST_PATH = Path(temp_manifest)
    
    success = set_no_ternary_data_flag("Fe-Cr-Mo", "Test reason")
    assert success is True
    
    # Verify the flag was set
    with open(temp_manifest, 'r') as f:
        manifest = json.load(f)
    
    system_found = False
    for system in manifest["systems"]:
        if system["name"] == "Fe-Cr-Mo":
            system_found = True
            assert "NO_TERNARY_DATA" in system.get("flags", [])
            assert system.get("flag_reason") == "Test reason"
            break
    
    assert system_found is True

def test_set_flag_for_new_system(temp_manifest):
    """Test setting flag for a system not in the manifest."""
    import code.services.thermo_interpolation as module
    module.MANIFEST_PATH = Path(temp_manifest)
    
    success = set_no_ternary_data_flag("New-Ternary-System", "New system reason")
    assert success is True
    
    # Verify the new system was added with the flag
    with open(temp_manifest, 'r') as f:
        manifest = json.load(f)
    
    system_found = False
    for system in manifest["systems"]:
        if system["name"] == "New-Ternary-System":
            system_found = True
            assert "NO_TERNARY_DATA" in system.get("flags", [])
            assert system.get("flag_reason") == "New system reason"
            break
    
    assert system_found is True

def test_validate_and_interpolate_ternary():
    """Test the full validation and interpolation workflow."""
    success, params = validate_and_interpolate_ternary("Fe-Cr-Mo", 1000)
    
    # Since we simulate missing parameters, this should succeed with interpolation
    assert success is True
    assert params is not None
    assert "L0" in params
    assert params["interpolation_method"] == "linear_regression"

def test_validate_and_interpolate_with_custom_binary_systems():
    """Test interpolation with explicitly provided binary systems."""
    binary_systems = ["Fe-Cr", "Fe-Mo"]
    success, params = validate_and_interpolate_ternary(
        "Fe-Cr-Mo", 1000, binary_systems
    )
    
    assert success is True
    assert params["binary_sources"] == binary_systems

def test_logging_of_warnings(caplog):
    """Test that appropriate warnings are logged during interpolation."""
    caplog.set_level(logging.WARNING)
    
    with caplog.at_level(logging.WARNING):
        success, params = validate_and_interpolate_ternary("Fe-Cr-Mo", 1000)
    
    # Check that warning messages were logged
    assert any("Missing ternary parameters" in record.message for record in caplog.records)
    assert any("linear interpolation" in record.message for record in caplog.records)
    assert any("NO_TERNARY_DATA" in record.message for record in caplog.records)