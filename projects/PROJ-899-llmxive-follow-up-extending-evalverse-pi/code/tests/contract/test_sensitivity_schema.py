"""
Contract test for T026: Sensitivity Analysis Output Schema.
Validates that the output CSV has the required columns and structure.
"""
import os
import sys
import pytest
import pandas as pd
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

OUTPUT_PATH = Path(project_root) / "data" / "sensitivity_sweep_raw.csv"

REQUIRED_COLUMNS = ["dimension", "threshold", "status"]
VALID_STATUSES = ["feature_sufficient", "vlm_required", "ambiguous"]
VALID_THRESHOLDS = [0.80, 0.85, 0.90]

def test_sensitivity_schema_exists():
    """Test that the output file exists."""
    assert OUTPUT_PATH.exists(), f"Output file not found: {OUTPUT_PATH}"

def test_sensitivity_schema_columns():
    """Test that the output file has the required columns."""
    df = pd.read_csv(OUTPUT_PATH)
    assert set(REQUIRED_COLUMNS).issubset(set(df.columns)), \
        f"Missing columns. Expected {REQUIRED_COLUMNS}, got {list(df.columns)}"

def test_sensitivity_schema_thresholds():
    """Test that only valid thresholds are present."""
    df = pd.read_csv(OUTPUT_PATH)
    df_thresholds = set(df['threshold'].unique())
    valid_threshold_set = set(VALID_THRESHOLDS)
    
    # Check that all found thresholds are in the valid set
    assert df_thresholds.issubset(valid_threshold_set), \
        f"Invalid thresholds found: {df_thresholds - valid_threshold_set}"

def test_sensitivity_schema_statuses():
    """Test that only valid status values are present."""
    df = pd.read_csv(OUTPUT_PATH)
    df_statuses = set(df['status'].unique())
    valid_status_set = set(VALID_STATUSES)
    
    # Check that all found statuses are in the valid set
    assert df_statuses.issubset(valid_status_set), \
        f"Invalid statuses found: {df_statuses - valid_status_set}"

def test_sensitivity_schema_data_types():
    """Test that columns have appropriate data types."""
    df = pd.read_csv(OUTPUT_PATH)
    
    assert df['dimension'].dtype == 'object', "dimension column should be string"
    assert df['threshold'].dtype in ['float64', 'int64', 'float32'], "threshold should be numeric"
    assert df['status'].dtype == 'object', "status column should be string"

def test_sensitivity_schema_completeness():
    """Test that every dimension has an entry for every threshold."""
    df = pd.read_csv(OUTPUT_PATH)
    
    dimensions = df['dimension'].unique()
    thresholds = df['threshold'].unique()
    
    expected_rows = len(dimensions) * len(thresholds)
    actual_rows = len(df)
    
    assert actual_rows == expected_rows, \
        f"Expected {expected_rows} rows (all dim x threshold combos), got {actual_rows}"

def test_sensitivity_schema_no_duplicates():
    """Test that there are no duplicate (dimension, threshold) pairs."""
    df = pd.read_csv(OUTPUT_PATH)
    
    duplicates = df.duplicated(subset=['dimension', 'threshold'], keep=False)
    assert not duplicates.any(), "Duplicate (dimension, threshold) pairs found"