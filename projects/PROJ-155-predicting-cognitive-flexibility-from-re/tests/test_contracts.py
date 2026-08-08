import pytest
import os
import pandas as pd
from code.data.paths import get_raw_path, get_processed_path

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
