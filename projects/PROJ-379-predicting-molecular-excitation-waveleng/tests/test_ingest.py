"""
Contract test for data ingestion output schema (T007).
Asserts output columns are exactly ["smi", "lambda_max", "scaffold_id"] with types str, float, str.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Add parent to path for imports if needed, though we test file existence/content
project_root = Path(__file__).resolve().parent.parent
data_processed = project_root / "data" / "processed"
cleaned_csv = data_processed / "cleaned.csv"
split_indices_json = data_processed / "split_indices.json"
train_val_test_csv = data_processed / "train_val_test.csv"

def test_ingest_output_schema_exists():
    """Verify that ingest.py produced the cleaned.csv file."""
    assert cleaned_csv.exists(), f"cleaned.csv not found at {cleaned_csv}. Did you run code/ingest.py?"

def test_cleaned_csv_columns_and_types():
    """Assert output columns are exactly ["smi", "lambda_max", "scaffold_id"] with types str, float, str."""
    if not cleaned_csv.exists():
        pytest.skip("cleaned.csv does not exist yet.")
    
    import pandas as pd
    df = pd.read_csv(cleaned_csv)
    
    expected_columns = ["smi", "lambda_max", "scaffold_id"]
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    # Check types
    assert df['smi'].dtype == 'object' or df['smi'].dtype.name == 'string', "smi column must be string"
    assert df['lambda_max'].dtype in ['float64', 'float32', 'int64'], "lambda_max must be numeric (float)"
    assert df['scaffold_id'].dtype == 'object' or df['scaffold_id'].dtype.name == 'string', "scaffold_id must be string"

def test_split_indices_structure():
    """Assert split_indices.json structure."""
    if not split_indices_json.exists():
        pytest.skip("split_indices.json does not exist yet.")
    
    with open(split_indices_json, 'r') as f:
        data = json.load(f)
    
    assert "train" in data, "Missing 'train' key in split_indices.json"
    assert "val" in data, "Missing 'val' key in split_indices.json"
    assert "test" in data, "Missing 'test' key in split_indices.json"
    
    assert isinstance(data["train"], list), "train must be a list"
    assert isinstance(data["val"], list), "val must be a list"
    assert isinstance(data["test"], list), "test must be a list"

def test_train_val_test_csv_schema():
    """Verify merged split file schema."""
    if not train_val_test_csv.exists():
        pytest.skip("train_val_test.csv does not exist yet.")
    
    import pandas as pd
    df = pd.read_csv(train_val_test_csv)
    
    expected_columns = ["smi", "lambda_max", "scaffold_id", "split"]
    assert list(df.columns) == expected_columns, f"Expected columns {expected_columns}, got {list(df.columns)}"
    
    assert df['split'].isin(['train', 'val', 'test']).all(), "All split values must be 'train', 'val', or 'test'"
