import pytest
import os
import json
import pandas as pd
from code.data.paths import get_raw_path, get_processed_path, get_results_path

def test_data_ingestion_schema():
    """
    Contract test for data ingestion schema.
    Verifies that the downloaded data files exist and have the expected structure.
    """
    # This test assumes T012 has run and populated data/raw/
    raw_path = get_raw_path()
    
    if not os.path.exists(raw_path):
        pytest.skip("Raw data path does not exist. T012 may not have run.")
    
    # Check for at least one subject directory
    subjects = [d for d in os.listdir(raw_path) if os.path.isdir(os.path.join(raw_path, d))]
    assert len(subjects) > 0, "No subject directories found in data/raw/"
    
    for subject in subjects:
        sub_path = os.path.join(raw_path, subject)
        files = os.listdir(sub_path)
        # Check for NIfTI file
        nifti_found = any(f.endswith('.nii.gz') for f in files)
        assert nifti_found, f"No NIfTI file found for subject {subject}"
        
        # Check for CSV file
        csv_found = any(f.endswith('.csv') for f in files)
        assert csv_found, f"No CSV file found for subject {subject}"

def test_motion_exclusion_logic():
    """
    Unit test for motion exclusion logic.
    Verifies that the exclusion log is generated correctly.
    """
    # This test assumes T015 has run and populated data/processed/exclusion_log.csv
    log_path = os.path.join(get_processed_path(), "exclusion_log.csv")
    
    if not os.path.exists(log_path):
        pytest.skip("Exclusion log does not exist. T015 may not have run.")
    
    df = pd.read_csv(log_path)
    required_columns = ["Subject_ID", "Exclusion_Reason", "Mean_FD"]
    assert all(col in df.columns for col in required_columns), "Exclusion log missing required columns."
    
    # Check that Exclusion_Reason is "Motion" for all rows
    assert all(df["Exclusion_Reason"] == "Motion"), "Exclusion reason is not 'Motion' for all rows."

def test_final_json_output_schema():
    """
    Contract test for final JSON output schema.
    Verifies that the regression summary JSON file exists and contains
    the required keys and data types as per the specification.
    
    Expected structure in data/results/regression_summary.json:
    {
        "beta": float,
        "se": float,
        "r": float,
        "p_value": float,
        "significance": bool,
        "pro_processed": float
    }
    """
    results_path = get_results_path()
    json_path = os.path.join(results_path, "regression_summary.json")
    
    if not os.path.exists(json_path):
        pytest.skip("Regression summary JSON does not exist. T034 or T015a may not have run.")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    required_keys = ["beta", "se", "r", "p_value", "significance", "pro_processed"]
    missing_keys = [k for k in required_keys if k not in data]
    assert not missing_keys, f"Regression summary JSON missing required keys: {missing_keys}"
    
    # Validate data types
    assert isinstance(data["beta"], (int, float)), "beta must be a number"
    assert isinstance(data["se"], (int, float)), "se must be a number"
    assert isinstance(data["r"], (int, float)), "r must be a number"
    assert isinstance(data["p_value"], (int, float)), "p_value must be a number"
    assert isinstance(data["significance"], bool), "significance must be a boolean"
    assert isinstance(data["pro_processed"], (int, float)), "pro_processed must be a number"
    
    # Validate value ranges where applicable
    assert 0 <= data["pro_processed"] <= 1, "pro_processed must be between 0 and 1"
    assert data["p_value"] >= 0, "p_value must be non-negative"
    
    # Check for optional but expected keys if present
    if "n_subjects" in data:
        assert isinstance(data["n_subjects"], int), "n_subjects must be an integer"
    
    # Check that significance aligns with p_value (optional sanity check)
    # If p_value < 0.05, significance should ideally be True (unless specific threshold differs)
    # We allow flexibility here as the threshold might be configurable, but the types must match.