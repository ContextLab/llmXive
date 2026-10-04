import os
import json
import tempfile
import pytest
from code.save_model_results import (
    get_default_results,
    initialize_results_file,
    load_results,
    save_results_to_json
)

def test_get_default_results_structure():
    """Test that default results have the correct keys and types."""
    results = get_default_results()
    assert isinstance(results, dict)
    assert "rf_r2" in results
    assert "gb_r2" in results
    assert "cv_scores" in results
    assert "sensitivity_analysis" in results
    assert "vif_scores" in results
    
    assert results["rf_r2"] == 0.0
    assert results["gb_r2"] == 0.0
    assert results["cv_scores"] == []
    assert results["sensitivity_analysis"] == {}
    assert results["vif_scores"] == []

def test_initialize_results_file_creates_file():
    """Test that initialize_results_file creates a valid JSON file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "test_results.json")
        results = initialize_results_file(filepath)
        
        assert os.path.exists(filepath)
        
        with open(filepath, 'r') as f:
            loaded = json.load(f)
        
        assert loaded == results
        assert loaded == get_default_results()

def test_load_results_creates_default_if_missing():
    """Test that load_results returns defaults if file doesn't exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "nonexistent.json")
        results = load_results(filepath)
        
        assert results == get_default_results()

def test_save_and_load_results():
    """Test round-trip save and load."""
    with tempfile.TemporaryDirectory() as tmpdir:
        filepath = os.path.join(tmpdir, "roundtrip.json")
        
        # Create custom results
        custom_results = {
            "rf_r2": 0.85,
            "gb_r2": 0.88,
            "cv_scores": [0.82, 0.84, 0.86, 0.85, 0.87],
            "sensitivity_analysis": {"threshold_2.5": 0.83},
            "vif_scores": [5.2, 4.1, 3.8]
        }
        
        save_results_to_json(custom_results, filepath)
        loaded = load_results(filepath)
        
        assert loaded == custom_results
