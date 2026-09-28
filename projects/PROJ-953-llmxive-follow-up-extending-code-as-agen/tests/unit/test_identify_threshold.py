"""
Unit tests for the threshold identification logic (T030).
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from scripts.identify_threshold import (
    load_threshold_sweep,
    identify_optimal_threshold,
    save_decision_boundary
)


def test_load_threshold_sweep():
    """Test loading threshold sweep from JSON file."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump({
            "thresholds": {
                "0.01": {"fnr": 0.0005},
                "0.05": {"fnr": 0.002},
                "0.1": {"fnr": 0.008}
            },
            "min_achievable_fnr": 0.0005
        }, f)
        temp_path = Path(f.name)
    
    try:
        result = load_threshold_sweep(temp_path)
        assert "thresholds" in result
        assert "0.01" in result["thresholds"]
        assert result["thresholds"]["0.01"]["fnr"] == 0.0005
    finally:
        temp_path.unlink()


def test_identify_optimal_threshold_safe():
    """Test identifying optimal threshold when constraint is met."""
    sweep_data = {
        "thresholds": {
            "0.01": {"fnr": 0.0005},  # Meets constraint (0.05% < 0.1%)
            "0.05": {"fnr": 0.002},   # Does not meet constraint
            "0.1": {"fnr": 0.008}     # Does not meet constraint
        },
        "min_achievable_fnr": 0.0005
    }
    
    optimal = identify_optimal_threshold(sweep_data)
    assert optimal == 0.01, "Should select 0.01 as it meets the FNR constraint"


def test_identify_optimal_threshold_unsafe():
    """Test identifying optimal threshold when constraint is not met."""
    sweep_data = {
        "thresholds": {
            "0.01": {"fnr": 0.002},   # 0.2% > 0.1%
            "0.05": {"fnr": 0.001},   # 0.1% = 0.1% (meets constraint)
            "0.1": {"fnr": 0.005}     # 0.5% > 0.1%
        },
        "min_achievable_fnr": 0.001
    }
    
    optimal = identify_optimal_threshold(sweep_data)
    assert optimal == 0.05, "Should select 0.05 as it is the lowest FNR meeting constraint"


def test_identify_optimal_threshold_no_safe_threshold():
    """Test when no threshold meets the safety constraint."""
    sweep_data = {
        "thresholds": {
            "0.01": {"fnr": 0.002},   # 0.2% > 0.1%
            "0.05": {"fnr": 0.003},   # 0.3% > 0.1%
            "0.1": {"fnr": 0.001}     # 0.1% = 0.1% (meets constraint)
        },
        "min_achievable_fnr": 0.001
    }
    
    optimal = identify_optimal_threshold(sweep_data)
    assert optimal == 0.1, "Should select 0.1 as it has the lowest FNR"


def test_identify_optimal_threshold_empty_data():
    """Test handling of empty threshold data."""
    sweep_data = {"thresholds": {}}
    
    try:
        identify_optimal_threshold(sweep_data)
        assert False, "Should raise ValueError for empty thresholds"
    except ValueError:
        pass  # Expected


def test_save_decision_boundary_creates_file():
    """Test that save_decision_boundary creates the model file."""
    with tempfile.TemporaryDirectory() as tmpdir:
        model_path = Path(tmpdir) / "decision_boundary.pkl"
        
        mock_model = MagicMock()
        mock_features = MagicMock()
        mock_features.columns = ["feature1", "feature2"]
        
        sweep_results = {
            "thresholds": {"0.01": {"fnr": 0.0005}},
            "min_achievable_fnr": 0.0005
        }
        
        with patch('scripts.identify_threshold.load_model_and_features', 
                  return_value=(mock_model, mock_features)):
            save_decision_boundary(model_path, 0.01, sweep_results)
        
        assert model_path.exists(), "Model file should be created"
        
        # Verify the file is a valid pickle
        import pickle
        with open(model_path, 'rb') as f:
            data = pickle.load(f)
        
        assert "optimal_threshold" in data
        assert data["optimal_threshold"] == 0.01
        assert data["safety_status"] == "safe"
        assert "thresholds_evaluated" in data