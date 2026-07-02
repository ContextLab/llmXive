import os
import json
import pytest
import tempfile
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from code.analysis.thresholds import calculate_global_thresholds, validate_threshold_schema, write_global_thresholds
from code.config import ACE_VARS, NOAA_VARS, TRAIN_START, TRAIN_END

@pytest.fixture
def sample_synced_data():
    """Create a sample synced dataset for testing."""
    n_points = 1000
    dates = pd.date_range(start=f"{TRAIN_START}-01-01", periods=n_points, freq='h')
    
    # Generate synthetic data with some autocorrelation
    np.random.seed(42)
    noise = np.random.randn(n_points)
    ace_data = {}
    for var in ACE_VARS:
        # Create AR(1) process for realistic autocorrelation
        ar_process = np.zeros(n_points)
        ar_process[0] = noise[0]
        for i in range(1, n_points):
            ar_process[i] = 0.9 * ar_process[i-1] + 0.1 * noise[i]
        ace_data[var] = ar_process
    
    noaa_data = {}
    for var in NOAA_VARS:
        noaa_data[var] = np.cumsum(np.random.randn(n_points)) / 10
    
    df = pd.DataFrame({
        'timestamp': dates,
        **ace_data,
        **noaa_data
    })
    return df

def test_calculate_global_thresholds_structure(sample_synced_data):
    """Test that calculate_global_thresholds returns the expected structure."""
    # Mock the load_synced_data function to use our sample data
    import code.analysis.thresholds as thresholds_module
    original_load = thresholds_module.load_synced_data
    
    def mock_load():
        return sample_synced_data
    
    thresholds_module.load_synced_data = mock_load
    
    try:
        result = calculate_global_thresholds()
        
        assert "neff_values" in result
        assert "alpha_adj" in result
        assert "total_tests" in result
        assert "train_period" in result
        
        # Check alpha_adj calculation (0.05 / 30)
        assert abs(result["alpha_adj"] - 0.05/30) < 1e-10
        
        # Check total_tests
        assert result["total_tests"] == 30
        
        # Check train_period
        assert result["train_period"] == [TRAIN_START, TRAIN_END]
        
        # Check that Neff values exist for expected variables
        expected_vars = ACE_VARS + NOAA_VARS
        for var in expected_vars:
            if var in sample_synced_data.columns:
                assert var in result["neff_values"]
                assert isinstance(result["neff_values"][var], float)
                assert result["neff_values"][var] > 0
    finally:
        thresholds_module.load_synced_data = original_load

def test_validate_threshold_schema_valid():
    """Test validation with valid data."""
    valid_data = {
        "neff_values": {"N_p": 500.5, "Kp": 450.2},
        "alpha_adj": 0.0016666666666666668,
        "total_tests": 30,
        "train_period": [1998, 2017]
    }
    
    assert validate_threshold_schema(valid_data) is True

def test_validate_threshold_schema_missing_key():
    """Test validation fails with missing required key."""
    invalid_data = {
        "neff_values": {"N_p": 500.5},
        "alpha_adj": 0.0016666666666666668,
        # Missing "total_tests"
        "train_period": [1998, 2017]
    }
    
    with pytest.raises(ValueError, match="Missing required key"):
        validate_threshold_schema(invalid_data)

def test_validate_threshold_schema_wrong_type():
    """Test validation fails with wrong type for neff_values."""
    invalid_data = {
        "neff_values": "not a dict",  # Should be dict
        "alpha_adj": 0.0016666666666666668,
        "total_tests": 30,
        "train_period": [1998, 2017]
    }
    
    with pytest.raises(ValueError, match="neff_values must be a dictionary"):
        validate_threshold_schema(invalid_data)

def test_write_global_thresholds_file_creation(sample_synced_data):
    """Test that write_global_thresholds creates the file correctly."""
    import code.analysis.thresholds as thresholds_module
    original_load = thresholds_module.load_synced_data
    
    def mock_load():
        return sample_synced_data
    
    thresholds_module.load_synced_data = mock_load
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = os.path.join(tmpdir, "test_thresholds.json")
        
        try:
            result_path = write_global_thresholds(output_path)
            
            assert os.path.exists(result_path)
            assert result_path == output_path
            
            with open(result_path, 'r') as f:
                data = json.load(f)
            
            assert "neff_values" in data
            assert "alpha_adj" in data
            assert "total_tests" in data
            assert data["total_tests"] == 30
            
        finally:
            thresholds_module.load_synced_data = original_load
