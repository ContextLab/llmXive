"""
Contract test for static baseline schema compliance.

Enforces CSV schema compliance (columns, types) for data/static_baseline.csv.
Satisfies SC-005 requirement for data integrity validation.
"""
import os
import pandas as pd
import pytest
from pathlib import Path

# Import project configuration
from config import get_data_path, setup_logging

# Setup logging for test output
logger = setup_logging("test_static_baseline_schema")

# Expected schema definition
REQUIRED_COLUMNS = {
    'code': str,
    'loc': (int, float),
    'cyclomatic_complexity': (int, float),
    'nesting_depth': (int, float),
    'static_smell_labels': str
}

def get_baseline_path():
    """Get the path to the static baseline CSV file."""
    return Path(get_data_path()) / "static_baseline.csv"

def load_baseline_data():
    """Load the static baseline CSV file."""
    path = get_baseline_path()
    if not path.exists():
        raise FileNotFoundError(f"Baseline file not found: {path}")
    return pd.read_csv(path)

def test_file_exists():
    """Verify that the static_baseline.csv file exists."""
    path = get_baseline_path()
    assert path.exists(), f"Static baseline file does not exist at {path}"

def test_required_columns_present():
    """Verify all required columns are present in the CSV."""
    df = load_baseline_data()
    missing_columns = set(REQUIRED_COLUMNS.keys()) - set(df.columns)
    assert not missing_columns, f"Missing required columns: {missing_columns}"

def test_column_data_types():
    """Verify data types for each column match expectations."""
    df = load_baseline_data()
    
    for col, expected_type in REQUIRED_COLUMNS.items():
        if col not in df.columns:
            continue  # Already tested in test_required_columns_present
        
        # Check if values are of expected type or can be coerced
        if isinstance(expected_type, tuple):
            # Allow multiple types (e.g., int or float for numeric columns)
            valid = True
            for val in df[col]:
                if pd.isna(val):
                    continue
                if not isinstance(val, expected_type):
                    # Check if it's a numeric string that can be converted
                    try:
                        float(val)
                    except (ValueError, TypeError):
                        valid = False
                        break
            assert valid, f"Column '{col}' contains values not matching types {expected_type}"
        else:
            # Single type check
            valid = True
            for val in df[col]:
                if pd.isna(val):
                    continue
                if not isinstance(val, expected_type):
                    valid = False
                    break
            assert valid, f"Column '{col}' contains values not matching type {expected_type}"

def test_no_null_critical_fields():
    """Verify that critical fields do not contain null values."""
    df = load_baseline_data()
    
    # 'code' and 'static_smell_labels' should not be null
    critical_fields = ['code', 'static_smell_labels']
    for field in critical_fields:
        if field in df.columns:
            null_count = df[field].isnull().sum()
            assert null_count == 0, f"Critical field '{field}' contains {null_count} null values"

def test_numeric_fields_are_valid():
    """Verify numeric fields contain valid numbers."""
    df = load_baseline_data()
    numeric_fields = ['loc', 'cyclomatic_complexity', 'nesting_depth']
    
    for field in numeric_fields:
        if field in df.columns:
            # Check for non-numeric values
            try:
                pd.to_numeric(df[field], errors='raise')
            except (ValueError, TypeError) as e:
                pytest.fail(f"Numeric field '{field}' contains invalid values: {e}")

def test_smell_labels_format():
    """Verify that static_smell_labels column contains valid label formats."""
    df = load_baseline_data()
    
    if 'static_smell_labels' not in df.columns:
        pytest.skip("static_smell_labels column not found")
    
    # Labels should be strings, potentially comma-separated or JSON-like
    for idx, row in df.iterrows():
        labels = row['static_smell_labels']
        if pd.isna(labels):
            continue
        
        assert isinstance(labels, str), f"Row {idx}: static_smell_labels is not a string"
        # Basic validation: should not be empty if present
        assert len(labels.strip()) > 0 or labels == "[]", f"Row {idx}: empty smell labels"

def test_row_count_minimum():
    """Verify that the dataset has a minimum number of rows for statistical validity."""
    df = load_baseline_data()
    # SC-005 requires sufficient data for analysis (e.g., McNemar's test needs >100)
    min_rows = 100
    assert len(df) >= min_rows, f"Dataset has {len(df)} rows, minimum required is {min_rows}"

def test_schema_compliance_summary():
    """Run all schema checks and provide a summary."""
    try:
        test_file_exists()
        test_required_columns_present()
        test_column_data_types()
        test_no_null_critical_fields()
        test_numeric_fields_are_valid()
        test_smell_labels_format()
        test_row_count_minimum()
        logger.info("Schema compliance: PASSED - All checks successful")
        return True
    except AssertionError as e:
        logger.error(f"Schema compliance: FAILED - {str(e)}")
        raise

if __name__ == "__main__":
    # Run tests directly if executed as a script
    pytest.main([__file__, "-v"])