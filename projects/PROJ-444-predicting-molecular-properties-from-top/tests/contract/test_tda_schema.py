import os
import json
import pytest
import pandas as pd
import yaml
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Load YAML schema definition."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def test_tda_schema_compliance():
    """
    Contract test for data/processed/tda_features.csv.
    Validates against specs/001-predicting-molecular-properties-from-top/contracts/feature_matrix.schema.yaml.
    
    Verifies:
    1. File exists.
    2. Schema matches expected structure (molecule_id, features, feature_names, target_property, target_value).
    3. Data types match schema (string for ID, array of numbers for features, etc.).
    4. No NaN values in topological columns.
    """
    file_path = Path("data/processed/tda_features.csv")
    schema_path = Path("specs/001-predicting-molecular-properties-from-top/contracts/feature_matrix.schema.yaml")
    
    # 1. File existence
    assert file_path.exists(), f"File {file_path} does not exist."
    
    # 2. Load schema
    assert schema_path.exists(), f"Schema file {schema_path} not found."
    schema = load_schema(str(schema_path))
    
    # 3. Load data
    df = pd.read_csv(file_path)
    
    # 4. Validate required columns per schema
    required_cols = schema.get('required', [])
    for col in required_cols:
        assert col in df.columns, f"Missing required column '{col}' per schema."
    
    # 5. Validate data types
    # molecule_id must be string
    assert df['molecule_id'].dtype == 'object' or df['molecule_id'].dtype == str, \
        "Column 'molecule_id' must be of type string."
    
    # features must be a single column containing a list/array (stored as string in CSV usually)
    # We check if the column exists and if values are parseable as lists
    assert 'features' in df.columns, "Missing 'features' column."
    
    # feature_names must be a single column containing a list/array
    assert 'feature_names' in df.columns, "Missing 'feature_names' column."
    
    # target_property must be string
    assert df['target_property'].dtype == 'object' or df['target_property'].dtype == str, \
        "Column 'target_property' must be of type string."
        
    # target_value must be numeric
    assert pd.api.types.is_numeric_dtype(df['target_value']), \
        "Column 'target_value' must be numeric."
        
    # 6. Validate content of list columns (features and feature_names)
    # We assume these are stored as JSON strings or Python list representations in the CSV
    # Check that they are not NaN and are parseable
    for idx, row in df.iterrows():
        try:
            # Try parsing as JSON first
            features = json.loads(str(row['features']))
            feature_names = json.loads(str(row['feature_names']))
        except (json.JSONDecodeError, ValueError):
            # Fallback: try eval if JSON fails (risky but common for Python lists in CSVs)
            # Only do this if the string looks like a list
            try:
                features = eval(str(row['features']))
                feature_names = eval(str(row['feature_names']))
            except:
                raise AssertionError(f"Row {idx} has invalid format for 'features' or 'feature_names'")
        
        # Check that features is a list of numbers
        assert isinstance(features, list), f"Row {idx}: 'features' must be a list."
        if len(features) > 0:
            assert all(isinstance(x, (int, float)) for x in features), \
                f"Row {idx}: All elements in 'features' must be numbers."
        
        # Check that feature_names is a list of strings
        assert isinstance(feature_names, list), f"Row {idx}: 'feature_names' must be a list."
        if len(feature_names) > 0:
            assert all(isinstance(x, str) for x in feature_names), \
                f"Row {idx}: All elements in 'feature_names' must be strings."
        
        # Check lengths match
        assert len(features) == len(feature_names), \
            f"Row {idx}: Length of 'features' ({len(features)}) must match 'feature_names' ({len(feature_names)})."
    
    # 7. Check for NaN values in topological columns (if any specific columns are identified)
    # Since the schema stores features as a flattened array, we check the 'features' column for NaN
    assert not df['features'].isna().any(), "Column 'features' contains NaN values."
    
    # Verify row count is reasonable (not empty)
    assert len(df) > 0, "DataFrame is empty."

def test_traditional_descriptors_schema():
    """
    Contract test for data/processed/traditional_descriptors.csv.
    """
    file_path = Path("data/processed/traditional_descriptors.csv")
    
    assert file_path.exists(), f"File {file_path} does not exist."
    
    df = pd.read_csv(file_path)
    
    assert 'smiles' in df.columns, "Missing 'smiles' column."
    
    # Check for standard descriptors
    expected_cols = ['molecular_weight', 'logP', 'tpsa']
    for col in expected_cols:
        assert col in df.columns, f"Missing expected column '{col}'."
        assert not df[col].isna().any(), f"Column '{col}' contains NaN values."
    
    assert len(df) > 0, "DataFrame is empty."
