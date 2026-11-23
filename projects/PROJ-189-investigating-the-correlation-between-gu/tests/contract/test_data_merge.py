import pytest
import pandas as pd
import os
import json

def test_merged_dataframe_schema():
    """
    Contract test for merged dataframe schema.
    Validates that the merged dataset meets the required schema and constraints.
    """
    log_path = "data/processed/merge_log.json"
    merged_path = "data/processed/merged_dataset.csv"
    
    if not os.path.exists(log_path):
        pytest.skip("Merge log not found. Run code/01_data_ingestion.py first.")
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    # Validate overlap count constraint
    assert log_data['overlap_count'] >= 500, "Overlap count must be >= 500"
    
    # Validate merged dataset exists and has correct schema
    if os.path.exists(merged_path):
        df = pd.read_csv(merged_path)
        
        # Check for required ID column
        assert 'sample_id' in df.columns or 'participant_id' in df.columns, \
            "Dataset must contain 'sample_id' or 'participant_id' column"
        
        # Check for required age column
        assert 'age' in df.columns, "Dataset must contain 'age' column"
        
        # Check for other critical columns as per US-1 requirements
        required_columns = ['age', 'sex', 'BMI', 'cognitive_score']
        missing_columns = [col for col in required_columns if col not in df.columns]
        if missing_columns:
            pytest.fail(f"Missing required columns: {missing_columns}")
        
        # Validate no null values in critical columns after imputation
        for col in required_columns:
            null_count = df[col].isnull().sum()
            assert null_count == 0, f"Column '{col}' contains {null_count} null values"
        
        # Validate age filter (age >= 60)
        if 'age' in df.columns:
            assert (df['age'] >= 60).all(), "All participants must be age >= 60"
    else:
        pytest.skip("Merged dataset not found. Run preprocessing pipeline first.")

def test_merge_log_structure():
    """
    Contract test for merge log JSON structure.
    """
    log_path = "data/processed/merge_log.json"
    
    if not os.path.exists(log_path):
        pytest.skip("Merge log not found.")
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    # Validate required keys in merge log
    required_keys = ['overlap_count', 'agp_count', 'hrs_count', 'validation_status']
    missing_keys = [key for key in required_keys if key not in log_data]
    assert not missing_keys, f"Merge log missing required keys: {missing_keys}"
    
    # Validate data types
    assert isinstance(log_data['overlap_count'], int), "overlap_count must be an integer"
    assert isinstance(log_data['validation_status'], str), "validation_status must be a string"
    
    # Validate validation status
    assert log_data['validation_status'] in ['passed', 'failed', 'skipped'], \
        "validation_status must be 'passed', 'failed', or 'skipped'"
