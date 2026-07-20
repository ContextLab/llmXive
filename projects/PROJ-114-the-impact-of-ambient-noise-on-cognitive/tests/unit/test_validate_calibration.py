"""
Unit tests for calibration validation logic.
"""
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
from code.scripts.validate_calibration import simulate_device_response, run_calibration_validation

def test_simulate_device_response_distribution():
    """Test that simulated responses follow expected statistical properties."""
    target = 60.0
    sample_size = 10000
    seed = 42
    
    measurements = simulate_device_response(target, 2.0, sample_size, seed)
    
    # Check size
    assert len(measurements) == sample_size
    
    # Check mean is close to target (within 0.1 for large sample)
    assert np.abs(np.mean(measurements) - target) < 0.1
    
    # Check std is close to 0.8 (within 0.05)
    assert np.abs(np.std(measurements) - 0.8) < 0.05

def test_calibration_validation_report_structure():
    """Test that the validation report contains all required keys."""
    report = run_calibration_validation()
    
    required_keys = [
        "parameters", "statistics", "validation_results", "config_summary", "notes"
    ]
    
    for key in required_keys:
        assert key in report, f"Missing key: {key}"
    
    # Check nested keys
    assert "target_db" in report["parameters"]
    assert "mean_db" in report["statistics"]
    assert "pass_rate" in report["validation_results"]
    assert "fidelity_status" in report["validation_results"]

def test_fidelity_status_logic():
    """Test that fidelity status is calculated correctly based on pass rate."""
    # We can't easily force a low pass rate without changing the simulation logic,
    # but we can verify the status is one of the expected values.
    report = run_calibration_validation()
    status = report["validation_results"]["fidelity_status"]
    assert status in ["PASS", "FAIL"]
    
    # Given our simulation parameters (target=60, tol=2, std=0.8), 
    # we expect a PASS.
    assert status == "PASS"

def test_output_file_generation():
    """Test that the script generates the output file correctly."""
    # Mock the PROCESSED_DIR to a temp directory
    with tempfile.TemporaryDirectory() as tmpdir:
        # Patch the module's PROCESSED_DIR
        with patch('code.scripts.validate_calibration.PROCESSED_DIR', tmpdir):
            from code.scripts.validate_calibration import main
            
            # Run main
            result = main()
            
            # Check return code
            assert result == 0
            
            # Check file exists
            output_path = Path(tmpdir) / "calibration_validation_report.json"
            assert output_path.exists(), "Output file was not created"
            
            # Check JSON validity
            with open(output_path, 'r') as f:
                data = json.load(f)
                assert "validation_results" in data