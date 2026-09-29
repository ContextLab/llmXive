"""
Unit tests for save_model_results.py (T033a/T033b).
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

# Mock config to use a temporary directory for tests
@pytest.fixture(autouse=True)
def mock_config(tmp_path):
    with patch('code.save_model_results.DATA_PATH', str(tmp_path)):
        yield tmp_path

from code.save_model_results import (
    get_default_results,
    initialize_results_file,
    save_results_to_json,
    load_results,
    RESULTS_PATH
)

def test_get_default_structure():
    """Verify T033a default structure keys and types."""
    defaults = get_default_results()
    assert isinstance(defaults, dict)
    assert 'rf_r2' in defaults and isinstance(defaults['rf_r2'], float)
    assert defaults['rf_r2'] == 0.0
    assert 'gb_r2' in defaults and isinstance(defaults['gb_r2'], float)
    assert defaults['gb_r2'] == 0.0
    assert 'cv_scores' in defaults and isinstance(defaults['cv_scores'], list)
    assert 'sensitivity_analysis' in defaults and isinstance(defaults['sensitivity_analysis'], dict)
    assert 'vif_scores' in defaults and isinstance(defaults['vif_scores'], list)

def test_initialize_creates_file(mock_config):
    """Test that initialize_results_file creates the JSON file."""
    assert not os.path.exists(RESULTS_PATH)
    initialize_results_file()
    assert os.path.exists(RESULTS_PATH)
    
    with open(RESULTS_PATH, 'r') as f:
        data = json.load(f)
    
    assert data == get_default_results()

def test_initialize_skips_existing(mock_config):
    """Test that initialize_results_file does not overwrite existing file."""
    # Create a file with custom data
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    custom_data = {"rf_r2": 0.99, "custom_key": "value"}
    with open(RESULTS_PATH, 'w') as f:
        json.dump(custom_data, f)
    
    initialize_results_file()
    
    with open(RESULTS_PATH, 'r') as f:
        data = json.load(f)
    
    # Should still have custom data
    assert data == custom_data
    assert data['rf_r2'] == 0.99

def test_save_results_overwrites(mock_config):
    """Test that save_results_to_json writes new data."""
    initialize_results_file() # Start with defaults
    
    new_results = {
        "rf_r2": 0.85,
        "gb_r2": 0.82,
        "cv_scores": [0.8, 0.85, 0.81],
        "sensitivity_analysis": {"threshold_3.0": 0.85},
        "vif_scores": [{"iteration": 1, "vif": 12.0}]
    }
    
    save_results_to_json(new_results)
    
    loaded = load_results()
    assert loaded == new_results

def test_load_results_returns_default_on_missing(mock_config):
    """Test load_results returns defaults if file is missing."""
    assert not os.path.exists(RESULTS_PATH)
    data = load_results()
    assert data == get_default_results()

def test_load_results_handles_invalid_json(mock_config):
    """Test load_results handles corrupted JSON gracefully."""
    os.makedirs(os.path.dirname(RESULTS_PATH), exist_ok=True)
    with open(RESULTS_PATH, 'w') as f:
        f.write("{ invalid json }")
    
    data = load_results()
    assert data == get_default_results()