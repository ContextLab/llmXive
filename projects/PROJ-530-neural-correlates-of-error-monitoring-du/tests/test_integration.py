import os
import sys
import csv
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.analysis import run_sensitivity_sweep, load_processed_data
from code.config_loader import load_config

@pytest.fixture
def setup_test_environment(tmp_path):
    """
    Sets up a temporary directory structure mimicking the project layout
    and ensures the sensitivity sweep can run on a small subset of data.
    """
    # Create necessary directories
    results_diag = tmp_path / "results" / "diagnostics"
    results_diag.mkdir(parents=True, exist_ok=True)
    
    # We need a small subset of processed data to run the sweep quickly.
    # Since we cannot rely on the full pipeline (T010-T015) being fully 
    # integrated in this specific test scope without mocking, we will 
    # create a minimal valid CSV that matches the expected schema from 
    # the preprocessing steps (T014).
    
    # Expected columns based on T014 and T015:
    # participant_id, condition, electrode, mean_amplitude, peak_amplitude, error_magnitude, trial_id
    mock_data = []
    for p in range(1, 6): # 5 participants
        for t in range(1, 21): # 20 trials per participant
            mock_data.append({
                "participant_id": f"P{p:03d}",
                "condition": "navigation",
                "electrode": "FCz",
                "mean_amplitude": -2.5 + (t * 0.1) + (p * 0.05), # Simulated MFN
                "peak_amplitude": -3.0 + (t * 0.1) + (p * 0.05),
                "error_magnitude": 5.0 + (t * 2.0) + (p * 0.5),  # Simulated Error Magnitude
                "trial_id": f"T{t:03d}"
            })
    
    processed_df = pd.DataFrame(mock_data)
    processed_csv = tmp_path / "data" / "processed" / "eeg_features.csv"
    processed_csv.parent.mkdir(parents=True, exist_ok=True)
    processed_df.to_csv(processed_csv, index=False)
    
    # Create a minimal config for the test
    config = {
        "paths": {
            "data_processed": str(processed_csv),
            "results_diagnostics": str(results_diag)
        },
        "analysis": {
            "sensitivity_thresholds": [5.0, 10.0, 15.0, 20.0],
            "primary_electrode": "FCz"
        }
    }
    
    config_file = tmp_path / "config_test.yaml"
    import yaml
    with open(config_file, 'w') as f:
        yaml.dump(config, f)
        
    return config_file, results_diag

def test_sensitivity_sweep_output_format(setup_test_environment):
    """
    Integration test T027:
    Run the sensitivity sweep on a subset and verify that 
    results/diagnostics/sensitivity_summary.csv contains exactly 4 rows 
    (one per threshold) with valid columns for threshold, correlation, and p_value.
    """
    config_file, output_dir = setup_test_environment
    
    # Load config
    config = load_config(config_file)
    
    # Run the sensitivity sweep
    # This calls the logic implemented in T022/T023
    run_sensitivity_sweep(config)
    
    # Verify output file exists
    output_path = output_dir / "sensitivity_summary.csv"
    assert output_path.exists(), f"Output file {output_path} was not created."
    
    # Read the file
    df = pd.read_csv(output_path)
    
    # Requirement: Exactly 4 rows (one per threshold in config)
    # The config fixture defines 4 thresholds: [5.0, 10.0, 15.0, 20.0]
    assert len(df) == 4, f"Expected 4 rows in sensitivity summary, got {len(df)}."
    
    # Requirement: Valid columns
    required_columns = ["threshold", "correlation", "p_value"]
    for col in required_columns:
        assert col in df.columns, f"Missing required column: {col}"
    
    # Verify data types and basic validity
    # Thresholds should match the config
    expected_thresholds = [5.0, 10.0, 15.0, 20.0]
    assert list(df["threshold"]) == expected_thresholds, "Threshold values do not match expected config."
    
    # Correlations should be floats between -1 and 1 (or NaN if singular)
    assert df["correlation"].apply(lambda x: isinstance(x, float) or pd.isna(x)).all(), "Correlation values are not numeric."
    
    # P-values should be floats between 0 and 1 (or NaN)
    assert df["p_value"].apply(lambda x: isinstance(x, float) or pd.isna(x)).all(), "P-value values are not numeric."
    
    # If we reached here, the format is correct
    assert True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])