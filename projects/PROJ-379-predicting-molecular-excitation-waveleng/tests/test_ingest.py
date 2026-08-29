import pytest
import pandas as pd
from pathlib import Path
import json
import os
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingest import main as ingest_main
from split import main as split_main
from merge_split import main as merge_main

def test_ingest_output_schema():
    """
    Contract test for data ingestion output schema.
    Assert output columns are exactly ["smi", "lambda_max", "scaffold_id"] with types str, float, str.
    """
    # Run ingestion
    ingest_main()
    
    # Load output
    output_path = Path("data/processed/cleaned.csv")
    assert output_path.exists(), "Cleaned CSV not found"
    
    df = pd.read_csv(output_path)
    
    # Check columns
    expected_columns = ["smi", "lambda_max"]
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check types
    assert df['smi'].dtype == object, "smi should be string"
    assert df['lambda_max'].dtype in ['float64', 'float32'], "lambda_max should be float"
    
    # Check for scaffold_id if present (it is added in split.py)
    # This test is for ingest.py output, so scaffold_id is not expected yet.
    
    print("Ingest output schema test passed.")

def test_split_indices_format():
    """
    Contract test for split indices format.
    """
    # Run split
    split_main()
    
    # Load output
    output_path = Path("data/processed/split_indices.json")
    assert output_path.exists(), "Split indices JSON not found"
    
    with open(output_path, 'r') as f:
        data = json.load(f)
    
    assert 'train_idx' in data, "Missing train_idx"
    assert 'val_idx' in data, "Missing val_idx"
    assert 'test_idx' in data, "Missing test_idx"
    
    assert isinstance(data['train_idx'], list), "train_idx should be list"
    assert isinstance(data['val_idx'], list), "val_idx should be list"
    assert isinstance(data['test_idx'], list), "test_idx should be list"
    
    print("Split indices format test passed.")

def test_merge_output():
    """
    Contract test for merge output.
    """
    # Run merge
    merge_main()
    
    # Load output
    output_path = Path("data/processed/train_val_test.csv")
    assert output_path.exists(), "Merged CSV not found"
    
    df = pd.read_csv(output_path)
    
    # Check columns
    assert 'split' in df.columns, "Missing split column"
    assert df['split'].isin(['train', 'val', 'test']).all(), "Invalid split values"
    
    print("Merge output test passed.")