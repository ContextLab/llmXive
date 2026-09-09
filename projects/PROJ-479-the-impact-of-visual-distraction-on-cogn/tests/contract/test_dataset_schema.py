import os
import json
import pytest
import pandas as pd
from typing import Dict, Any

# Import schema validation if available, otherwise implement inline
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PROCESSED_DIR = os.path.join(PROJECT_ROOT, "data", "processed")
MERGED_DATA_PATH = os.path.join(DATA_PROCESSED_DIR, "merged_data.csv")

REQUIRED_COLUMNS = [
    'participant_id',
    'reaction_time',
    'accuracy',
    'visual_complexity',
    'image_id'
]

def test_merged_dataset_schema():
    """Contract test for merged dataset schema (T013)."""
    # Check file exists
    assert os.path.exists(MERGED_DATA_PATH), f"File not found: {MERGED_DATA_PATH}"
    
    # Load data
    df = pd.read_csv(MERGED_DATA_PATH)
    
    # Check required columns
    missing_cols = set(REQUIRED_COLUMNS) - set(df.columns)
    assert not missing_cols, f"Missing columns: {missing_cols}"
    
    # Check N >= 100
    assert len(df) >= 100, f"Sample size too small: N={len(df)}"
    
    # Check non-null critical columns
    for col in ['reaction_time', 'accuracy', 'visual_complexity']:
        null_count = df[col].isna().sum()
        null_pct = null_count / len(df)
        assert null_pct <= 0.05, f"Missing values > 5% in {col}: {null_pct:.2%}"
    
    # Check image metadata exists
    assert df['image_id'].notna().all(), "Missing image metadata"
    
    # Check data types
    assert df['reaction_time'].dtype in ['float64', 'int64'], "reaction_time must be numeric"
    assert df['accuracy'].dtype in ['float64', 'int64'], "accuracy must be numeric"
    assert df['visual_complexity'].dtype in ['float64', 'int64'], "visual_complexity must be numeric"
    
    # Check ranges
    assert df['accuracy'].between(0, 1).all(), "Accuracy must be between 0 and 1"
    assert df['reaction_time'] > 0, "Reaction time must be positive"
    assert df['visual_complexity'].between(0, 10).all(), "Visual complexity should be 0-10"
    
    print("Dataset schema validation passed.")

if __name__ == "__main__":
    test_merged_dataset_schema()
