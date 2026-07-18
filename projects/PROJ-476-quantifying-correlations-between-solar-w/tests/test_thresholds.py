import pytest
import os
import json
import pandas as pd
import numpy as np
from pathlib import Path
from code.analysis.thresholds import calculate_global_thresholds, validate_threshold_schema, write_global_thresholds
from code.config import TRAIN_START, TRAIN_END

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def load_test_data():
    """Load or create test data for threshold calculations."""
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "synced.csv"
    
    if data_path.exists():
        return pd.read_csv(data_path)
    else:
        # Create minimal synthetic data for testing purposes only
        # This is used ONLY for unit tests when real data is not available
        dates = pd.date_range(start=f"{TRAIN_START}-01-01", end=f"{TRAIN_END}-12-31", freq='H')
        n = len(dates)
        
        data = {
            'timestamp': dates,
            'N_p': np.random.randn(n) * 5 + 10,
            'T_p': np.random.randn(n) * 5000 + 150000,
            'He2+_ratio': np.random.randn(n) * 0.02 + 0.04,
            'Kp': np.random.randint(0, 10, n),
            'Dst': np.random.randn(n) * 20 + (-30)
        }
        return pd.DataFrame(data)

def test_calculate_global_thresholds_structure():
    """Test that calculate_global_thresholds returns the expected structure."""
    # This test will run only if synced.csv exists, otherwise it's skipped
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "synced.csv"
    
    if not data_path.exists():
        pytest.skip("synced.csv not found - cannot test threshold calculation without real data")
    
    result = calculate_global_thresholds()
    
    assert "neff_values" in result
    assert "alpha_adj" in result
    assert "total_tests" in result
    assert "period" in result
    assert "variables" in result
    assert "methodology" in result
    
    assert result["total_tests"] == 30
    assert abs(result["alpha_adj"] - (0.05 / 30)) < 1e-10
    assert result["period"]["start"] == TRAIN_START
    assert result["period"]["end"] == TRAIN_END

def test_validate_threshold_schema_valid():
    """Test validation with valid threshold data."""
    valid_data = {
        "neff_values": {"N_p": 100.5, "T_p": 95.2},
        "alpha_adj": 0.0016666666666666668,
        "total_tests": 30,
        "period": {"start": 1998, "end": 2017}
    }
    
    assert validate_threshold_schema(valid_data) is True

def test_validate_threshold_schema_missing_keys():
    """Test validation fails with missing keys."""
    invalid_data = {
        "neff_values": {},
        "alpha_adj": 0.0016666666666666668
    }
    
    with pytest.raises(ValueError, match="Missing required key"):
        validate_threshold_schema(invalid_data)

def test_validate_threshold_schema_invalid_types():
    """Test validation fails with invalid types."""
    invalid_data = {
        "neff_values": "not_a_dict",
        "alpha_adj": 0.0016666666666666668,
        "total_tests": 30,
        "period": {"start": 1998, "end": 2017}
    }
    
    with pytest.raises(ValueError, match="neff_values must be a dictionary"):
        validate_threshold_schema(invalid_data)

def test_write_global_thresholds_creates_file():
    """Test that write_global_thresholds creates the expected file."""
    project_root = get_project_root()
    data_path = project_root / "data" / "processed" / "synced.csv"
    
    if not data_path.exists():
        pytest.skip("synced.csv not found - cannot test file writing without real data")
    
    output_path = project_root / "artifacts" / "thresholds" / "test_global_threshold.json"
    
    try:
        result_path = write_global_thresholds(str(output_path))
        
        assert os.path.exists(result_path)
        
        with open(result_path, 'r') as f:
            data = json.load(f)
        
        assert "neff_values" in data
        assert "alpha_adj" in data
        assert data["total_tests"] == 30
        
    finally:
        if output_path.exists():
            output_path.unlink()
