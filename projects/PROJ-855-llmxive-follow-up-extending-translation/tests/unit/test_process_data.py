"""
Unit tests for the data processing pipeline (T016b).

Tests:
1. Geometry-disjoint split logic.
2. Minimum row count validation.
3. Data integrity (no column loss).
"""
import os
import sys
import tempfile
import pandas as pd
import pytest
from pathlib import Path
import pyarrow.parquet as pq

# Add code directory to path
code_dir = Path(__file__).parent.parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from process_data import split_geometry_disjoint, validate_splits

def create_mock_data(num_rows=100, num_geoms=20):
    """Helper to create a mock dataframe with geometry IDs."""
    geoms = [f"geo_{i}" for i in range(num_geoms)]
    data = {
        "geometry_id": [random.choice(geoms) for _ in range(num_rows)],
        "translation_x": [1.0] * num_rows,
        "translation_y": [2.0] * num_rows,
        "label": [1] * num_rows
    }
    return pd.DataFrame(data)

def test_geometry_disjoint_split():
    """Test that the split ensures no geometry IDs overlap."""
    import random
    random.seed(42) # Deterministic for test
    
    df = create_mock_data(num_rows=1000, num_geoms=50)
    train_df, test_df = split_geometry_disjoint(df)
    
    train_geoms = set(train_df["geometry_id"].unique())
    test_geoms = set(test_df["geometry_id"].unique())
    
    # Assert disjointness
    assert train_geoms.intersection(test_geoms) == set(), "Geometry leak detected!"
    
    # Assert all original geometries are present
    all_geoms = set(df["geometry_id"].unique())
    assert train_geoms.union(test_geoms) == all_geoms, "Missing geometries in split"

def test_validate_splits_pass():
    """Test validation passes when requirements are met."""
    train_df = pd.DataFrame({"geometry_id": ["g1"] * 3000})
    test_df = pd.DataFrame({"geometry_id": ["g2"] * 1000})
    
    # Should not raise
    validate_splits(train_df, test_df)

def test_validate_splits_fail_test_count():
    """Test validation fails when test rows are too low."""
    train_df = pd.DataFrame({"geometry_id": ["g1"] * 4000})
    test_df = pd.DataFrame({"geometry_id": ["g2"] * 999}) # Below 1000
    
    with pytest.raises(ValueError, match="Test rows"):
        validate_splits(train_df, test_df)

def test_validate_splits_fail_total_count():
    """Test validation fails when total rows are too low."""
    train_df = pd.DataFrame({"geometry_id": ["g1"] * 2000})
    test_df = pd.DataFrame({"geometry_id": ["g2"] * 1000}) # Total 3000 < 5000
    
    with pytest.raises(ValueError, match="Total rows"):
        validate_splits(train_df, test_df)

def test_columns_preserved():
    """Test that all columns from raw data are preserved in splits."""
    import random
    random.seed(42)
    
    df = create_mock_data(num_rows=100, num_geoms=10)
    original_cols = set(df.columns)
    
    train_df, test_df = split_geometry_disjoint(df)
    
    assert set(train_df.columns) == original_cols, "Train columns changed"
    assert set(test_df.columns) == original_cols, "Test columns changed"