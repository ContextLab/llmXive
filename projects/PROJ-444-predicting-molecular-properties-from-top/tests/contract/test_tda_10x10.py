import os
import sys
import json
import pytest
from pathlib import Path
import pandas as pd
import numpy as np

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "processed"

def test_persistence_images_10x10_exists():
    """Verify that the 10x10 persistence images file exists."""
    path = DATA_DIR / "persistence_images_10x10.csv"
    assert path.exists(), f"File {path} does not exist. Run code/02_tda_computation.py first."
    assert path.stat().st_size > 0, f"File {path} is empty."

def test_persistence_images_10x10_schema():
    """Verify the schema of the 10x10 persistence images file."""
    path = DATA_DIR / "persistence_images_10x10.csv"
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")
    
    df = pd.read_csv(path)
    
    # Check required columns
    assert "molecule_id" in df.columns, "Missing 'molecule_id' column."
    
    # Check for 10x10 image columns (100 features)
    expected_cols = [f"img_10_{i}" for i in range(100)]
    for col in expected_cols:
        assert col in df.columns, f"Missing column: {col}"
    
    # Check no extra unexpected columns (optional, but good for strict schema)
    # The task doesn't forbid extra columns, but we check the expected ones exist.

def test_persistence_images_10x10_no_nan():
    """Verify no NaN values in topological columns."""
    path = DATA_DIR / "persistence_images_10x10.csv"
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")
    
    df = pd.read_csv(path)
    
    # Select only image columns
    image_cols = [col for col in df.columns if col.startswith("img_10_")]
    
    if len(image_cols) == 0:
        pytest.fail("No image columns found in the dataset.")
    
    subset = df[image_cols]
    
    assert not subset.isnull().any().any(), "NaN values found in topological columns."

def test_persistence_images_10x10_non_negative():
    """Verify that persistence image values are non-negative (Gaussian weights)."""
    path = DATA_DIR / "persistence_images_10x10.csv"
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")
    
    df = pd.read_csv(path)
    image_cols = [col for col in df.columns if col.startswith("img_10_")]
    
    if len(image_cols) == 0:
        pytest.fail("No image columns found.")
    
    subset = df[image_cols]
    
    # Allow small floating point errors, but generally should be >= 0
    # We check that min is not significantly negative
    min_val = subset.min().min()
    assert min_val >= -1e-6, f"Found negative values in persistence images: {min_val}"

def test_persistence_images_10x10_has_data():
    """Verify the file contains data rows (not just headers)."""
    path = DATA_DIR / "persistence_images_10x10.csv"
    if not path.exists():
        pytest.skip(f"File {path} does not exist yet.")
    
    df = pd.read_csv(path)
    assert len(df) > 0, "DataFrame is empty."

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
