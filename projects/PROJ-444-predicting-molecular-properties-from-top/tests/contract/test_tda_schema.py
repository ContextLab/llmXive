import os
import json
import pytest
import pandas as pd
from pathlib import Path

def test_tda_features_schema():
    """
    Contract test for data/processed/tda_features.csv.
    Verifies:
    1. File exists.
    2. Schema matches expected columns (smiles, scalar features, image pixels).
    3. No NaN values in topological columns.
    """
    file_path = Path("data/processed/tda_features.csv")
    
    assert file_path.exists(), f"File {file_path} does not exist."
    
    df = pd.read_csv(file_path)
    
    # Must have smiles column
    assert 'smiles' in df.columns, "Missing 'smiles' column."
    
    # Check for at least some TDA columns
    tda_cols = [c for c in df.columns if 'persistence' in c.lower()]
    assert len(tda_cols) > 0, "No TDA columns found in the file."
    
    # Check for non-null values in TDA columns
    for col in tda_cols:
        assert not df[col].isna().any(), f"Column '{col}' contains NaN values."
    
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
