"""
Unit tests for the Eco-Director configuration loader.
"""
import pytest
import os
import tempfile
import yaml
import sys
import numpy as np

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim.eco_director import load_config, validate_config, run_simulation

def test_load_config_valid():
    """Test loading a valid YAML configuration."""
    config_data = {
        'locality': {'radius': 1},
        'memory': {'depth': 1},
        'non_linearity': {'type': 'linear'},
        'grid_size': 10,
        'steps': 5
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        loaded = load_config(temp_path)
        assert loaded == config_data
        assert loaded['grid_size'] == 10
    finally:
        os.unlink(temp_path)

def test_load_config_file_not_found():
    """Test that FileNotFoundError is raised for missing file."""
    with pytest.raises(FileNotFoundError):
        load_config('non_existent_file.yaml')

def test_load_config_empty():
    """Test that ValueError is raised for empty file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        f.write("")
        temp_path = f.name
    
    try:
        with pytest.raises(ValueError):
            load_config(temp_path)
    finally:
        os.unlink(temp_path)

def test_validate_config_missing_key():
    """Test validation fails on missing required key."""
    config = {
        'locality': {'radius': 1},
        # missing memory, non_linearity, grid_size, steps
    }
    # Note: validate_config checks for required keys
    # It should raise ValueError
    with pytest.raises(ValueError):
        validate_config(config)

def test_run_simulation_integration():
    """Test the full simulation run with a temp config."""
    config_data = {
        'locality': {'radius': 1},
        'memory': {'depth': 1},
        'non_linearity': {'type': 'linear'},
        'grid_size': 5,
        'steps': 3
    }
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
        yaml.dump(config_data, f)
        temp_path = f.name
    
    try:
        result = run_simulation(temp_path)
        assert 'final_state' in result
        assert 'history' in result
        assert len(result['history']) == 3
        assert result['final_state'].shape == (5, 5)
    finally:
        os.unlink(temp_path)