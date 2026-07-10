"""
Unit tests for the calibration module (T016).
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import json
import os
import sys

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from analysis.calibration import (
    apply_calibration,
    load_calibration_factors,
    log_calibration_run,
    run_calibration_pipeline
)
from config import get_processed_data_path, get_raw_data_path, ensure_directories

@pytest.fixture
def sample_raw_data():
    """Create a sample raw DataFrame."""
    data = {
        "time": [0.0, 1.0, 2.0, 3.0],
        "wavelength": [400.0, 400.0, 400.0, 400.0],
        "absorbance": [0.5, 0.4, 0.3, 0.2],
        "solvent": ["hexane"] * 4
    }
    return pd.DataFrame(data)

@pytest.fixture
def calibration_factors():
    return {
        "wavelength_shift_nm": 0.5,
        "detector_sensitivity": 2.0,
        "dark_current_offset": 0.1,
        "integration_time_ms": 100.0
    }

def test_apply_calibration_wavelength_shift(sample_raw_data, calibration_factors):
    """Test that wavelength shift is applied correctly."""
    result = apply_calibration(sample_raw_data, calibration_factors)
    # Original wavelength was 400.0, shift is 0.5
    expected_wavelength = 400.5
    assert all(result["wavelength"] == expected_wavelength)

def test_apply_calibration_sensitivity(sample_raw_data, calibration_factors):
    """Test that detector sensitivity scaling is applied correctly."""
    result = apply_calibration(sample_raw_data, calibration_factors)
    # Original absorbance 0.5, sensitivity 2.0 -> 1.0
    # Then dark current 0.1 -> 0.9
    expected_abs = [0.9, 0.7, 0.5, 0.3]
    assert all(abs(result["absorbance"].iloc[i] - expected_abs[i]) < 1e-6 for i in range(len(expected_abs)))

def test_apply_calibration_dark_current_only():
    """Test dark current correction in isolation."""
    data = pd.DataFrame({
        "time": [0.0],
        "wavelength": [400.0],
        "absorbance": [0.5]
    })
    factors = {
        "wavelength_shift_nm": 0.0,
        "detector_sensitivity": 1.0,
        "dark_current_offset": 0.1
    }
    result = apply_calibration(data, factors)
    # 0.5 - 0.1 = 0.4
    assert abs(result["absorbance"].iloc[0] - 0.4) < 1e-6

def test_apply_calibration_clamping():
    """Test that negative absorbance values are clamped to 0."""
    data = pd.DataFrame({
        "time": [0.0],
        "wavelength": [400.0],
        "absorbance": [0.05]
    })
    factors = {
        "wavelength_shift_nm": 0.0,
        "detector_sensitivity": 1.0,
        "dark_current_offset": 0.1
    }
    result = apply_calibration(data, factors)
    # 0.05 - 0.1 = -0.05 -> clamped to 0.0
    assert result["absorbance"].iloc[0] == 0.0

def test_load_calibration_factors_defaults():
    """Test that default factors are returned if config is missing."""
    # Ensure no calibration file exists in the chemicals path for this test
    # (This relies on the fixture or environment state, but we test the logic)
    factors = load_calibration_factors()
    assert "detector_sensitivity" in factors
    assert "wavelength_shift_nm" in factors
    assert factors["detector_sensitivity"] == 1.0 # Default

def test_log_calibration_run(tmp_path, sample_raw_data, calibration_factors):
    """Test that calibration run is logged correctly."""
    # Mock paths to use tmp_path
    # We need to patch get_processed_data_path to return tmp_path for this test
    # Or just test the log writing logic directly by manipulating the config if possible
    # For simplicity, we test the function's ability to write JSON
    
    # Create a temporary directory for logs
    log_dir = tmp_path / "processed"
    log_dir.mkdir()
    
    # Mock the get_processed_data_path temporarily
    import analysis.calibration as cal_module
    original_get_path = cal_module.get_processed_data_path
    cal_module.get_processed_data_path = lambda: log_dir
    
    try:
        result = log_calibration_run(
            factors=calibration_factors,
            input_file="test_input.csv",
            output_file="test_output.csv",
            status="success"
        )
        
        assert result["status"] == "success"
        assert result["factors_applied"] == calibration_factors
        
        # Check file existence
        log_file = log_dir / "calibration_log.json"
        assert log_file.exists()
        
        with open(log_file, "r") as f:
            log_data = json.load(f)
        
        assert len(log_data) == 1
        assert log_data[0]["status"] == "success"
    finally:
        cal_module.get_processed_data_path = original_get_path