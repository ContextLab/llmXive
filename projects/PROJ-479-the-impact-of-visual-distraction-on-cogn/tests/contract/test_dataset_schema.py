import os
import json
import pytest
import pandas as pd
import yaml

def test_merged_dataset_schema():
    """
    Contract test: Verify merged dataset schema matches spec.
    """
    # Load schema
    schema_path = "specs/001-visual-distraction-on-cogn/contracts/dataset.schema.yaml"
    if not os.path.exists(schema_path):
        pytest.skip("Schema file not found")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    # Expected columns
    expected_cols = ['participant_id', 'reaction_time', 'accuracy', 'image_path']
    
    # Check if merged_data.csv exists
    merged_path = "data/processed/merged_data.csv"
    if not os.path.exists(merged_path):
        pytest.skip("Merged data file not found (T015b not run yet)")
    
    df = pd.read_csv(merged_path)
    
    # Verify columns
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Verify types
    assert df['reaction_time'].dtype in ['float64', 'int64']
    assert df['accuracy'].dtype in ['float64', 'int64']
    
    # Verify N >= 100
    assert len(df) >= 100, f"N={len(df)} is less than 100"
    
    # Verify no nulls in critical columns
    assert df['reaction_time'].isnull().sum() == 0, "Null values in reaction_time"
    assert df['accuracy'].isnull().sum() == 0, "Null values in accuracy"
    assert df['image_path'].isnull().sum() == 0, "Null values in image_path"
    
    print("Schema validation passed.")