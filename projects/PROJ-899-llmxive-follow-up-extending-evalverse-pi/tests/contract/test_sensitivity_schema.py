"""
Contract test for sensitivity analysis output schema.

This test verifies that the sensitivity analysis output files
adhere to the expected schema defined in the feature specification.

Validates:
- data/sensitivity_sweep_raw.csv columns: [dimension, threshold, status]
- data/sensitivity_analysis.csv columns: [dimension, threshold, status, flip_rate]
- data/sensitivity_matrix_full.csv structure
"""

import pytest
import pandas as pd
import os
from pathlib import Path
from src.config import get_data_root


# Expected schema definitions
SENSITIVITY_SWEEP_RAW_COLUMNS = ['dimension', 'threshold', 'status']
SENSITIVITY_ANALYSIS_COLUMNS = ['dimension', 'threshold', 'status', 'flip_rate']
SENSITIVITY_MATRIX_COLUMNS = ['dimension', 'threshold_0.80', 'threshold_0.85', 'threshold_0.90']

# Expected thresholds
EXPECTED_THRESHOLDS = [0.80, 0.85, 0.90]

# Expected status values
EXPECTED_STATUSES = ['feature-sufficient', 'VLM-required']

def get_data_path(filename: str) -> Path:
    """Get the full path to a data file."""
    return Path(get_data_root()) / filename


def test_sensitivity_sweep_raw_schema():
    """
    Contract test for data/sensitivity_sweep_raw.csv schema.
    
    Validates that the raw sensitivity sweep output contains:
    - Required columns: dimension, threshold, status
    - Correct data types
    - Valid status values
    """
    output_path = get_data_path('sensitivity_sweep_raw.csv')
    
    if not output_path.exists():
        pytest.skip("Sensitivity sweep raw file not generated yet (expected before T026 implementation)")
    
    df = pd.read_csv(output_path)
    
    # Check required columns exist
    assert set(SENSITIVITY_SWEEP_RAW_COLUMNS).issubset(
        set(df.columns)
    ), f"Missing required columns. Expected {SENSITIVITY_SWEEP_RAW_COLUMNS}, got {list(df.columns)}"
    
    # Check column types
    assert df['dimension'].dtype == 'object', "dimension column must be string/object"
    assert df['threshold'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "threshold column must be numeric"
    assert df['status'].dtype == 'object', "status column must be string/object"
    
    # Check threshold values are in expected set
    actual_thresholds = set(df['threshold'].unique())
    expected_thresholds_set = set(EXPECTED_THRESHOLDS)
    assert actual_thresholds.issubset(expected_thresholds_set), \
        f"Unexpected threshold values. Expected subset of {expected_thresholds_set}, got {actual_thresholds}"
    
    # Check status values are valid
    actual_statuses = set(df['status'].unique())
    assert actual_statuses.issubset(set(EXPECTED_STATUSES)), \
        f"Invalid status values. Expected subset of {EXPECTED_STATUSES}, got {actual_statuses}"
    
    # Check for duplicate entries (same dimension, same threshold)
    duplicates = df.duplicated(subset=['dimension', 'threshold'], keep=False)
    assert not duplicates.any(), \
        "Duplicate entries found: each (dimension, threshold) pair should be unique"
    
    # Check that all thresholds are present for each dimension
    dimensions = df['dimension'].unique()
    for dim in dimensions:
        dim_df = df[df['dimension'] == dim]
        dim_thresholds = set(dim_df['threshold'].unique())
        assert dim_thresholds == expected_thresholds_set, \
            f"Dimension '{dim}' missing thresholds. Expected {expected_thresholds_set}, got {dim_thresholds}"
    
    # Verify row count
    expected_rows = len(dimensions) * len(EXPECTED_THRESHOLDS)
    assert len(df) == expected_rows, \
        f"Expected {expected_rows} rows, got {len(df)}"

def test_sensitivity_analysis_schema():
    """
    Contract test for data/sensitivity_analysis.csv schema.
    
    Validates that the sensitivity analysis output contains:
    - Required columns: dimension, threshold, status, flip_rate
    - Correct data types
    - Valid flip_rate values (0.0 to 1.0)
    """
    output_path = get_data_path('sensitivity_analysis.csv')
    
    if not output_path.exists():
        pytest.skip("Sensitivity analysis file not generated yet (expected after T027 implementation)")
    
    df = pd.read_csv(output_path)
    
    # Check required columns exist
    assert set(SENSITIVITY_ANALYSIS_COLUMNS).issubset(
        set(df.columns)
    ), f"Missing required columns. Expected {SENSITIVITY_ANALYSIS_COLUMNS}, got {list(df.columns)}"
    
    # Check column types
    assert df['dimension'].dtype == 'object', "dimension column must be string/object"
    assert df['threshold'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "threshold column must be numeric"
    assert df['status'].dtype == 'object', "status column must be string/object"
    assert df['flip_rate'].dtype in ['float64', 'float32', 'int64', 'int32'], \
        "flip_rate column must be numeric"
    
    # Check threshold values
    actual_thresholds = set(df['threshold'].unique())
    expected_thresholds_set = set(EXPECTED_THRESHOLDS)
    assert actual_thresholds.issubset(expected_thresholds_set), \
        f"Unexpected threshold values. Expected subset of {expected_thresholds_set}, got {actual_thresholds}"
    
    # Check status values
    actual_statuses = set(df['status'].unique())
    assert actual_statuses.issubset(set(EXPECTED_STATUSES)), \
        f"Invalid status values. Expected subset of {EXPECTED_STATUSES}, got {actual_statuses}"
    
    # Check flip_rate is between 0.0 and 1.0
    assert df['flip_rate'].min() >= 0.0, "flip_rate cannot be negative"
    assert df['flip_rate'].max() <= 1.0, "flip_rate cannot exceed 1.0"
    
    # Check for duplicate entries
    duplicates = df.duplicated(subset=['dimension', 'threshold'], keep=False)
    assert not duplicates.any(), \
        "Duplicate entries found: each (dimension, threshold) pair should be unique"

def test_sensitivity_matrix_full_schema():
    """
    Contract test for data/sensitivity_matrix_full.csv schema.
    
    Validates that the full sensitivity matrix contains:
    - Required columns: dimension, threshold_0.80, threshold_0.85, threshold_0.90
    - Correct data types
    - Valid status values in each threshold column
    """
    output_path = get_data_path('sensitivity_matrix_full.csv')
    
    if not output_path.exists():
        pytest.skip("Sensitivity matrix file not generated yet (expected after T028 implementation)")
    
    df = pd.read_csv(output_path)
    
    # Check required columns exist
    assert set(SENSITIVITY_MATRIX_COLUMNS).issubset(
        set(df.columns)
    ), f"Missing required columns. Expected {SENSITIVITY_MATRIX_COLUMNS}, got {list(df.columns)}"
    
    # Check dimension column type
    assert df['dimension'].dtype == 'object', "dimension column must be string/object"
    
    # Check threshold columns exist and are object type (status strings)
    for col in ['threshold_0.80', 'threshold_0.85', 'threshold_0.90']:
        assert col in df.columns, f"Column {col} is missing"
        assert df[col].dtype == 'object', f"Column {col} must be string/object"
    
    # Check status values in each threshold column
    for col in ['threshold_0.80', 'threshold_0.85', 'threshold_0.90']:
        actual_statuses = set(df[col].unique())
        assert actual_statuses.issubset(set(EXPECTED_STATUSES)), \
            f"Invalid status values in {col}. Expected subset of {EXPECTED_STATUSES}, got {actual_statuses}"
    
    # Check for duplicate dimensions
    duplicates = df.duplicated(subset=['dimension'], keep=False)
    assert not duplicates.any(), \
        "Duplicate entries found: each dimension should appear exactly once"

def test_consistency_between_outputs():
    """
    Cross-validation test to ensure consistency between sensitivity outputs.
    
    Validates that:
    - sensitivity_analysis.csv flip_rate values are derived from sensitivity_sweep_raw.csv
    - sensitivity_matrix_full.csv values match sensitivity_sweep_raw.csv
    """
    raw_path = get_data_path('sensitivity_sweep_raw.csv')
    analysis_path = get_data_path('sensitivity_analysis.csv')
    matrix_path = get_data_path('sensitivity_matrix_full.csv')
    
    if not all(p.exists() for p in [raw_path, analysis_path, matrix_path]):
        pytest.skip("Not all sensitivity files are generated yet")
    
    raw_df = pd.read_csv(raw_path)
    analysis_df = pd.read_csv(analysis_path)
    matrix_df = pd.read_csv(matrix_path)
    
    # Verify dimensions match across all files
    raw_dims = set(raw_df['dimension'].unique())
    analysis_dims = set(analysis_df['dimension'].unique())
    matrix_dims = set(matrix_df['dimension'].unique())
    
    assert raw_dims == analysis_dims == matrix_dims, \
        f"Dimension mismatch across files. Raw: {raw_dims}, Analysis: {analysis_dims}, Matrix: {matrix_dims}"
    
    # Verify flip_rate calculation is consistent
    # For each dimension, count status changes across thresholds
    for dim in raw_dims:
        dim_raw = raw_df[raw_df['dimension'] == dim]
        dim_analysis = analysis_df[analysis_df['dimension'] == dim]
        
        statuses = dim_raw.sort_values('threshold')['status'].tolist()
        expected_flips = sum(1 for i in range(len(statuses)-1) if statuses[i] != statuses[i+1])
        max_flips = len(statuses) - 1  # 2 possible transitions for 3 thresholds
        
        if max_flips > 0:
            expected_flip_rate = expected_flips / max_flips
            actual_flip_rate = dim_analysis[dim_analysis['threshold'] == 0.85]['flip_rate'].values[0]
            
            # Allow small floating point differences
            assert abs(expected_flip_rate - actual_flip_rate) < 0.001, \
                f"Flip rate mismatch for dimension {dim}: expected {expected_flip_rate}, got {actual_flip_rate}"