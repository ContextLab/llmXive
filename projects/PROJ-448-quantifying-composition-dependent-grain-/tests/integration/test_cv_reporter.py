import json
import os
import tempfile
from pathlib import Path
import pytest
import numpy as np

# Mock the config paths for testing
from unittest.mock import patch, MagicMock

@pytest.fixture
def mock_cv_data():
    """Generate mock cross-validation results data."""
    return [
        {"fold_index": 0, "r2": 0.85, "mse": 0.05, "train_size": 80, "test_size": 20},
        {"fold_index": 1, "r2": 0.88, "mse": 0.04, "train_size": 80, "test_size": 20},
        {"fold_index": 2, "r2": 0.82, "mse": 0.06, "train_size": 80, "test_size": 20},
        {"fold_index": 3, "r2": 0.87, "mse": 0.045, "train_size": 80, "test_size": 20},
        {"fold_index": 4, "r2": 0.84, "mse": 0.055, "train_size": 80, "test_size": 20}
    ]

@pytest.fixture
def temp_processed_dir(tmp_path):
    """Create a temporary directory structure mimicking the project's processed path."""
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)
    return processed_dir

def test_cv_reporter_calculation(mock_cv_data, temp_processed_dir, caplog):
    """
    Test that cv_reporter correctly calculates Mean R² and Std Dev,
    logs the required format, and saves the JSON report.
    """
    # Setup input file
    input_path = temp_processed_dir / "cross_validation_results.json"
    with open(input_path, 'w') as f:
        json.dump(mock_cv_data, f)

    # Patch the PROCESSED_PATH in the module
    import code.services.cv_reporter as reporter_module
    
    with patch.object(reporter_module, 'PROCESSED_PATH', temp_processed_dir):
        # Run main
        reporter_module.main()

    # 1. Verify Log Output
    # Expected: "Mean R²: X, Std Dev: Y"
    # Calculate expected values
    r2_values = [item["r2"] for item in mock_cv_data]
    expected_mean = np.mean(r2_values)
    expected_std = np.std(r2_values)
    
    expected_log_msg = f"Mean R²: {expected_mean:.4f}, Std Dev: {expected_std:.4f}"
    
    assert expected_log_msg in caplog.text, f"Expected log message '{expected_log_msg}' not found in logs. Logs: {caplog.text}"

    # 2. Verify Output File
    output_path = temp_processed_dir / "cv_metrics.json"
    assert output_path.exists(), "cv_metrics.json was not created."

    with open(output_path, 'r') as f:
        report_data = json.load(f)

    assert "summary" in report_data
    assert "fold_details" in report_data
    
    summary = report_data["summary"]
    assert abs(summary["mean_r2"] - expected_mean) < 1e-6
    assert abs(summary["std_r2"] - expected_std) < 1e-6
    assert summary["num_folds"] == 5
    
    # Check stability flag (std < 0.05 in this mock)
    assert summary["is_stable"] is True

def test_cv_reporter_unstable_case(mock_cv_data, temp_processed_dir, caplog):
    """
    Test that the reporter flags instability when Std Dev > 0.05.
    """
    # Modify data to create high variance
    high_variance_data = [
        {"fold_index": 0, "r2": 0.50, "mse": 0.1, "train_size": 80, "test_size": 20},
        {"fold_index": 1, "r2": 0.95, "mse": 0.01, "train_size": 80, "test_size": 20},
        {"fold_index": 2, "r2": 0.60, "mse": 0.09, "train_size": 80, "test_size": 20},
        {"fold_index": 3, "r2": 0.90, "mse": 0.02, "train_size": 80, "test_size": 20},
        {"fold_index": 4, "r2": 0.55, "mse": 0.08, "train_size": 80, "test_size": 20}
    ]

    input_path = temp_processed_dir / "cross_validation_results.json"
    with open(input_path, 'w') as f:
        json.dump(high_variance_data, f)

    import code.services.cv_reporter as reporter_module
    with patch.object(reporter_module, 'PROCESSED_PATH', temp_processed_dir):
        reporter_module.main()

    # Verify warning is logged
    assert "Cross-validation instability detected" in caplog.text
    
    # Verify JSON flag
    output_path = temp_processed_dir / "cv_metrics.json"
    with open(output_path, 'r') as f:
        report_data = json.load(f)
    
    assert report_data["summary"]["is_stable"] is False

def test_cv_reporter_missing_file(temp_processed_dir):
    """Test that the script fails loudly if input file is missing."""
    import code.services.cv_reporter as reporter_module
    
    with patch.object(reporter_module, 'PROCESSED_PATH', temp_processed_dir):
        with pytest.raises(FileNotFoundError):
            reporter_module.main()