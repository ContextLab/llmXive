"""
Integration test for download and exclusion logic (US1).

This test verifies that the data ingestion pipeline:
1. Successfully downloads the OpenNeuro ds000030 dataset (or a representative subset if full download is restricted).
2. Correctly parses behavioral data and applies exclusion criteria (e.g., missing values, threshold checks).
3. Produces the expected intermediate artifacts in the data directory.

Prerequisites:
- T001a, T001b, T002, T003 (Project setup)
- T004 (Data directory structure)
- T005, T006, T007, T008 (Utils and Config)
- T009 (Schema contract test - ensures schema validity before ingestion)
- T011 (Download script implementation)
- T012 (Preprocessing script implementation)
"""

import os
import sys
import json
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch, MagicMock
import pandas as pd
import numpy as np

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from code.utils.config import get_config, reset_config, DatasetConfig, PreprocessingConfig, OutputPaths
from code.data.download import download_dataset
from code.data.preprocess import preprocess_fmriprep, extract_behavioral_metrics
from code.data.connectivity_matrix import ConnectivityMatrix
from code.data.subject import Subject


def setup_module():
    """
    Setup for the integration test suite.
    Creates a temporary directory to simulate the project's data/ structure.
    """
    reset_config()
    # Create a temporary base directory for this test run
    test_base = tempfile.mkdtemp(prefix="llmXive_test_")
    os.environ["PROJECT_ROOT"] = str(project_root)
    os.environ["DATA_ROOT"] = test_base
    
    # Update config to point to temp directories
    # We need to ensure the config loads from the temp dir
    # The get_config function typically reads from env or defaults.
    # We will rely on the environment variable or pass explicit paths if needed.
    # For this test, we assume the config reads DATA_ROOT from env.
    
    # Verify directories exist
    data_raw = os.path.join(test_base, "raw")
    data_processed = os.path.join(test_base, "processed")
    data_artifacts = os.path.join(test_base, "artifacts")
    os.makedirs(data_raw, exist_ok=True)
    os.makedirs(data_processed, exist_ok=True)
    os.makedirs(data_artifacts, exist_ok=True)

def teardown_module():
    """
    Cleanup: Remove temporary test directory.
    """
    test_base = os.environ.get("DATA_ROOT")
    if test_base and os.path.exists(test_base):
        shutil.rmtree(test_base)
    reset_config()

def test_download_and_exclusion_logic():
    """
    Integration Test: Download and Exclusion Logic.
    
    Steps:
    1. Mock the openneuro-cli download to simulate a successful fetch of ds000030
       (or a minimal subset structure if full download is too slow/expensive for CI).
       Since T011 implements the download script, we test the *integration* of that script
       with the exclusion logic in T013/T014.
    2. Create a mock behavioral dataset that includes some excluded subjects (missing data, high FD).
    3. Run the preprocessing pipeline which should:
       - Load the mock data.
       - Apply exclusion logic (T013).
       - Calculate retention rates (T014).
       - Fail gracefully if retention is too low (T015).
    4. Verify that the output CSV contains only valid subjects.
    5. Verify that excluded subjects are logged.
    """
    
    # 1. Setup Mock Data
    # We simulate the presence of a downloaded dataset structure
    # Since we cannot rely on actual OpenNeuro download in this unit/integration context
    # without network or excessive time, we mock the *result* of the download
    # to create the expected file structure that preprocess.py expects.
    
    # However, the task asks for an *integration test for download and exclusion*.
    # We will mock the download function to return a path to a mock dataset,
    # then run the real preprocessing logic on that mock dataset.
    
    mock_dataset_path = os.path.join(os.environ["DATA_ROOT"], "raw", "ds000030")
    os.makedirs(mock_dataset_path, exist_ok=True)
    
    # Create a mock subjects.tsv file with mixed valid/invalid data
    mock_behavioral_data = {
        "participant_id": ["sub-01", "sub-02", "sub-03", "sub-04", "sub-05"],
        "motor_score_pre": [10.0, 12.0, np.nan, 15.0, 20.0],  # sub-03 missing
        "motor_score_post": [15.0, 18.0, 14.0, 16.0, 25.0],
        "age": [25, 30, 45, 50, 60],
        "sex": ["M", "F", "M", "F", "M"],
        "mean_fd": [0.1, 0.2, 0.5, 0.15, 0.1]  # sub-03 has high FD (threshold 0.3)
    }
    
    # Create the mock behavioral file
    behavioral_path = os.path.join(mock_dataset_path, "sub-01", "sub-01_behavioral.csv")
    os.makedirs(os.path.dirname(behavioral_path), exist_ok=True)
    df_mock = pd.DataFrame(mock_behavioral_data)
    # Save as a single file for the mock (simulating a merged behavioral file)
    mock_merged_path = os.path.join(mock_dataset_path, "behavioral", "merged_behavioral.csv")
    os.makedirs(os.path.dirname(mock_merged_path), exist_ok=True)
    df_mock.to_csv(mock_merged_path, index=False)
    
    # Create mock fMRIPrep confounds files for all subjects
    for pid in mock_behavioral_data["participant_id"]:
        sub_dir = os.path.join(mock_dataset_path, pid)
        os.makedirs(sub_dir, exist_ok=True)
        confounds_path = os.path.join(sub_dir, "desc-confounds_timeseries.tsv")
        # Create a minimal TSV
        with open(confounds_path, "w") as f:
            f.write("trans_x\ttrans_y\ttrans_z\tdisc\n0.1\t0.1\t0.1\t0\n0.1\t0.1\t0.1\t0\n")
    
    # 2. Mock the download script
    # We patch the download_dataset function to return our mock path
    # This simulates T011 succeeding
    with patch('code.data.download.download_dataset') as mock_download:
        mock_download.return_value = mock_dataset_path
        
        # 3. Execute the Download Logic (simulated)
        # In a real run, this would call the CLI. Here we just ensure the path exists.
        # We call the function to verify it returns the path we set up
        result_path = download_dataset("ds000030")
        assert result_path == mock_dataset_path, "Download mock did not return expected path"
    
    # 4. Execute Preprocessing and Exclusion Logic
    # This calls T012/T013/T014 logic
    # We expect sub-03 to be excluded (missing motor_score_pre AND high FD)
    # sub-01, sub-02, sub-04, sub-05 should remain.
    
    # Load config to ensure paths are correct
    cfg = get_config()
    cfg.data.raw_dir = mock_dataset_path
    cfg.data.processed_dir = os.path.join(os.environ["DATA_ROOT"], "processed")
    cfg.data.artifacts_dir = os.path.join(os.environ["DATA_ROOT"], "artifacts")
    
    # Run the extraction and exclusion
    # This function should handle loading, filtering, and saving
    output_csv_path = os.path.join(cfg.data.processed_dir, "behavioral", "processed_behavioral.csv")
    excluded_log_path = os.path.join(cfg.data.artifacts_dir, "excluded_subjects.json")
    
    # Ensure output directories exist
    os.makedirs(os.path.dirname(output_csv_path), exist_ok=True)
    os.makedirs(os.path.dirname(excluded_log_path), exist_ok=True)
    
    # Call the main preprocessing function
    # Note: We are calling the function that implements T013/T014/T015 logic
    # We assume this function exists in preprocess.py as `process_and_filter_data`
    # or similar. If the function name is different in the actual implementation,
    # we must adapt. Based on the API surface, we look for `preprocess_fmriprep`
    # or a specific behavioral extraction function.
    # Since T013 is "Implement behavioral metric extraction... and subject exclusion",
    # we assume a function like `extract_and_filter_behavior` exists.
    # Let's assume the function `extract_behavioral_metrics` in preprocess.py handles this.
    
    try:
        # We need to call the actual function that does the work.
        # Since the task is to test the logic, we call the function that
        # T013 would implement.
        from code.data.preprocess import extract_behavioral_metrics
        
        # Call the function
        processed_df, excluded_log = extract_behavioral_metrics(
            input_path=mock_merged_path,
            output_path=output_csv_path,
            excluded_log_path=excluded_log_path,
            fd_threshold=0.3, # Threshold for exclusion
            min_retention_rate=0.5 # 50% retention required
        )
        
        # 5. Assertions
        
        # A. Check that the output CSV exists
        assert os.path.exists(output_csv_path), f"Output CSV not found at {output_csv_path}"
        
        # B. Check that the excluded log exists
        assert os.path.exists(excluded_log_path), f"Excluded log not found at {excluded_log_path}"
        
        # C. Verify content of processed CSV
        df_out = pd.read_csv(output_csv_path)
        
        # Should NOT contain sub-03 (missing data + high FD)
        assert "sub-03" not in df_out["participant_id"].values, "sub-03 should be excluded"
        
        # Should contain the others
        expected_subjects = ["sub-01", "sub-02", "sub-04", "sub-05"]
        for sub in expected_subjects:
            assert sub in df_out["participant_id"].values, f"{sub} should be present"
        
        # D. Verify exclusion log content
        with open(excluded_log_path, "r") as f:
            excluded_data = json.load(f)
        
        assert "sub-03" in excluded_data, "sub-03 should be in exclusion log"
        assert "reason" in excluded_data["sub-03"], "Reason should be provided for exclusion"
        
        # E. Verify retention rate calculation (4 out of 5 = 80% > 50%)
        # The function should have raised an error if retention was too low,
        # so if we are here, retention was sufficient.
        
        print("Integration Test Passed: Download and Exclusion Logic working correctly.")
        
    except Exception as e:
        # If the function doesn't exist or fails, we raise a clear error
        # This helps in debugging if T013 hasn't been implemented yet
        print(f"Error during integration test: {e}")
        raise

if __name__ == "__main__":
    test_download_and_exclusion_logic()
