"""
Unit tests for Task T051: Simulation Transparency.
"""
import os
import json
import pytest
from pathlib import Path
import tempfile
import shutil

# Import the function to test
# Note: We import the logic directly to test it in isolation
import sys
sys.path.insert(0, 'code')
from task_t051_simulation_transparency import update_simulation_methodology, check_simulation_mode, SIMULATION_SEED

def test_check_simulation_mode_true():
    metadata = {"simulation_mode": True}
    assert check_simulation_mode(metadata) is True

def test_check_simulation_mode_false():
    metadata = {"simulation_mode": False}
    assert check_simulation_mode(metadata) is False

def test_check_simulation_mode_missing():
    metadata = {}
    assert check_simulation_mode(metadata) is False

def test_update_simulation_methodology_adds_field():
    """Test that the field is added when in simulation mode."""
    metadata = {"simulation_mode": True, "other_key": "value"}
    updated = update_simulation_methodology(metadata)
    
    assert "simulation_methodology" in updated
    assert updated["simulation_methodology"]["seed"] == SIMULATION_SEED
    assert "sample_size" in updated["simulation_methodology"]
    assert "distributions" in updated["simulation_methodology"]
    assert updated["other_key"] == "value" # Ensure existing keys are preserved

def test_update_simulation_methodology_skips_if_false():
    """Test that the field is NOT added when not in simulation mode."""
    metadata = {"simulation_mode": False, "other_key": "value"}
    updated = update_simulation_methodology(metadata)
    
    assert "simulation_methodology" not in updated
    assert updated["other_key"] == "value"

def test_update_simulation_methodology_skips_if_missing():
    """Test that the field is NOT added when simulation_mode is missing."""
    metadata = {"other_key": "value"}
    updated = update_simulation_methodology(metadata)
    
    assert "simulation_methodology" not in updated
    assert updated["other_key"] == "value"