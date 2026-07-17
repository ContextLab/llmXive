"""
Contract test for dataset schema.
"""
import pytest
import pandas as pd
from code.utils import get_logger

def test_merged_dataset_schema():
    # Simulate loading merged data
    df = pd.DataFrame({
        "participant_id": ["sub_001"],
        "reaction_time": [500.0],
        "accuracy": [0.9],
        "visual_complexity": [0.5]
    })
    
    required_cols = ["participant_id", "reaction_time", "accuracy", "visual_complexity"]
    assert all(col in df.columns for col in required_cols)
    assert len(df) >= 1
