"""
Integration test for T035: Verify heatmap generation script runs and produces output.
"""
import os
import json
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from unittest.mock import patch, MagicMock

# We need to ensure the script can be imported and run
# Since T035 depends on T030 and T012/T023 artifacts, we mock the loading functions
# to return valid synthetic data if the real files don't exist in the test environment.

@pytest.fixture
def mock_metrics():
    """
    Create mock baseline and cleaned metrics to satisfy T035 dependencies.
    """
    baseline = {
        "dataset_A": {"n": 100, "ci_width": 0.5, "p_value": 0.04},
        "dataset_B": {"n": 50, "ci_width": 0.8, "p_value": 0.06},
        "dataset_C": {"n": 300, "ci_width": 0.3, "p_value": 0.01}
    }
    
    cleaned = {
        "dataset_A": {
            "iqr_outlier": {"ci_width": 0.4, "p_value": 0.03},
            "mean_imputation": {"ci_width": 0.55, "p_value": 0.045}
        },
        "dataset_B": {
            "iqr_outlier": {"ci_width": 0.7, "p_value": 0.055},
            "knn_imputation": {"ci_width": 0.85, "p_value": 0.065}
        },
        "dataset_C": {
            "median_imputation": {"ci_width": 0.25, "p_value": 0.009}
        }
    }
    return baseline, cleaned

def test_t035_generates_heatmap(mock_metrics, tmp_path):
    """
    Verify that t035_generate_ci_heatmap.py runs successfully and creates the PNG file.
    """
    baseline_data, cleaned_data = mock_metrics
    
    # Create temporary directories for input/output
    processed_dir = tmp_path / "data" / "processed"
    processed_dir.mkdir(parents=True)
    
    # Write mock metrics to files
    with open(processed_dir / "baseline_metrics.json", "w") as f:
        json.dump(baseline_data, f)
    
    with open(processed_dir / "cleaned_metrics.json", "w") as f:
        json.dump(cleaned_data, f)
    
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    
    # Mock the config to point to our temp dirs
    with patch('t035_generate_ci_heatmap.get_config') as mock_config, \
         patch('t035_generate_ci_heatmap.setup_logging') as mock_logging:
         
         mock_config_instance = MagicMock()
         mock_config_instance.OUTPUT_PATH = str(output_dir)
         mock_config_instance.RANDOM_SEED = 42
         mock_config.return_value = mock_config_instance
         
         # Mock logging to avoid console spam
         mock_logging.return_value = MagicMock()
         
         # Import and run main
         # We need to reload the module or import it fresh if we changed paths, 
         # but here we assume the script uses the mocked functions correctly.
         # Since we can't easily change the script's internal imports without modifying the script,
         # we rely on the script's structure. 
         # However, the script imports load_baseline_metrics from t030.
         # We must patch t030's functions.
         
         with patch('t035_generate_ci_heatmap.load_baseline_metrics', return_value=baseline_data), \
              patch('t035_generate_ci_heatmap.load_cleaned_metrics', return_value=cleaned_data):
             
             from code.t035_generate_ci_heatmap import main
             result = main()
             
             assert result == 0, "Script exited with non-zero status"
             
             # Check if file exists
             expected_file = output_dir / "heatmap_ci_widths.png"
             assert expected_file.exists(), f"Heatmap file not found at {expected_file}"
             
             # Check file size is reasonable (> 1KB)
             assert expected_file.stat().st_size > 1024, "Generated heatmap file is too small"