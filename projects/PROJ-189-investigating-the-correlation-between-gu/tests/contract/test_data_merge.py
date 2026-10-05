import pytest
import pandas as pd
import os
import json

def test_merged_dataframe_schema():
    """
    Contract test for merged dataframe schema.
    """
    log_path = "data/processed/merge_log.json"
    merged_path = "data/processed/merged_dataset.csv"
    
    if not os.path.exists(log_path):
        pytest.skip("Merge log not found. Run code/01_data_ingestion.py first.")
    
    with open(log_path, 'r') as f:
        log_data = json.load(f)
    
    assert log_data['overlap_count'] >= 500, "Overlap count must be >= 500"
    
    if os.path.exists(merged_path):
        df = pd.read_csv(merged_path)
        assert 'sample_id' in df.columns or 'participant_id' in df.columns
        assert 'age' in df.columns
