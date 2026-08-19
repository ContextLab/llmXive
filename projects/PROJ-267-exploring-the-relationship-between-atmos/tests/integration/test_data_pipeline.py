"""
Integration test for data ingestion completeness verification (T019).

This test verifies that the full data pipeline (ingestion -> preprocessing -> merge)
produces a valid merged CSV with expected completeness and data quality.

Requirements:
- Validates that merged_monthly.csv exists after pipeline execution
- Checks completeness threshold (>= 90% of expected monthly rows)
- Verifies absence of NaN values in primary columns
- Validates schema compliance against dataset.schema.yaml
"""
import os
import sys
import pytest
import subprocess
from pathlib import Path
import pandas as pd
import yaml

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

# Expected output file
MERGED_CSV_PATH = PROCESSED_DIR / "merged_monthly.csv"
SCHEMA_PATH = CONTRACTS_DIR / "dataset.schema.yaml"

# Expected columns based on data-model.md and schema
EXPECTED_COLUMNS = {
    'month',
    'grace_gravity_anomaly',
    'ar_intensity',
    'ar_event_count'
}

# Completeness threshold (90% of expected months)
COMPLETENESS_THRESHOLD = 0.90

def run_pipeline():
    """Execute the full data pipeline scripts in order."""
    scripts = [
        "01_data_ingestion.py",
        "02_preprocessing.py",
        "03_merge_output.py"
    ]
    
    for script_name in scripts:
        script_path = CODE_DIR / script_name
        if not script_path.exists():
            pytest.fail(f"Script not found: {script_path}")
        
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(CODE_DIR),
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            pytest.fail(
                f"Pipeline script failed: {script_name}\n"
                f"stdout: {result.stdout}\n"
                f"stderr: {result.stderr}"
            )

def load_schema():
    """Load the dataset schema definition."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}")
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def test_pipeline_execution():
    """Test that the full pipeline executes without errors."""
    # Clean up any existing output
    if MERGED_CSV_PATH.exists():
        MERGED_CSV_PATH.unlink()
    
    # Run the pipeline
    run_pipeline()
    
    # Verify output file was created
    assert MERGED_CSV_PATH.exists(), "Merged CSV output file was not created"

def test_output_completeness():
    """Test that the merged dataset meets completeness threshold."""
    # Ensure pipeline has run
    if not MERGED_CSV_PATH.exists():
        run_pipeline()
    
    # Load the merged data
    df = pd.read_csv(MERGED_CSV_PATH)
    
    # Calculate expected months (e.g., from 2002 to present)
    # Assuming at least 10 years of data (120 months) as minimum
    min_expected_months = 120
    actual_rows = len(df)
    
    # Check completeness
    completeness_ratio = actual_rows / min_expected_months
    assert completeness_ratio >= COMPLETENESS_THRESHOLD, (
        f"Dataset completeness {completeness_ratio:.2%} is below "
        f"threshold {COMPLETENESS_THRESHOLD:.2%}. "
        f"Expected >= {int(min_expected_months * COMPLETENESS_THRESHOLD)} rows, "
        f"got {actual_rows}"
    )

def test_no_nan_in_primary_columns():
    """Test that primary columns have no NaN values."""
    if not MERGED_CSV_PATH.exists():
        run_pipeline()
    
    df = pd.read_csv(MERGED_CSV_PATH)
    
    # Check primary columns for NaN
    primary_columns = ['grace_gravity_anomaly', 'ar_intensity', 'ar_event_count']
    
    for col in primary_columns:
        if col not in df.columns:
            pytest.fail(f"Primary column '{col}' missing from dataset")
        
        nan_count = df[col].isna().sum()
        assert nan_count == 0, (
            f"Column '{col}' contains {nan_count} NaN values. "
            "Primary columns must have no missing values."
        )

def test_schema_compliance():
    """Test that the output matches the defined schema."""
    if not MERGED_CSV_PATH.exists():
        run_pipeline()
    
    schema = load_schema()
    df = pd.read_csv(MERGED_CSV_PATH)
    
    # Check required columns
    required_columns = schema.get('required_columns', [])
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' missing from output"
    
    # Check column types if specified
    if 'column_types' in schema:
        for col_name, expected_type in schema['column_types'].items():
            if col_name in df.columns:
                actual_type = str(df[col_name].dtype)
                # Basic type checking (simplified)
                if 'int' in expected_type and 'int' not in actual_type:
                    if 'float' not in expected_type:  # int can be float64 in pandas
                        pytest.fail(f"Column '{col_name}' type mismatch: expected {expected_type}, got {actual_type}")

def test_column_presence():
    """Test that all expected columns are present."""
    if not MERGED_CSV_PATH.exists():
        run_pipeline()
    
    df = pd.read_csv(MERGED_CSV_PATH)
    actual_columns = set(df.columns)
    
    missing_columns = EXPECTED_COLUMNS - actual_columns
    assert not missing_columns, (
        f"Missing expected columns: {missing_columns}. "
        f"Available: {actual_columns}"
    )

def test_data_range_validity():
    """Test that data values are within reasonable ranges."""
    if not MERGED_CSV_PATH.exists():
        run_pipeline()
    
    df = pd.read_csv(MERGED_CSV_PATH)
    
    # AR intensity should be positive (Integrated Water Vapor Transport in kg/m/s)
    assert (df['ar_intensity'] >= 0).all(), "AR intensity contains negative values"
    
    # AR event count should be non-negative integer
    assert (df['ar_event_count'] >= 0).all(), "AR event count contains negative values"
    
    # Gravity anomaly should be reasonable (typically small values in mm or m)
    # Allow for a wide range but check for extreme outliers
    anomaly_std = df['grace_gravity_anomaly'].std()
    anomaly_mean = df['grace_gravity_anomaly'].mean()
    
    # Check for extreme outliers (> 100 standard deviations from mean)
    if anomaly_std > 0:
        z_scores = (df['grace_gravity_anomaly'] - anomaly_mean) / anomaly_std
        assert (abs(z_scores) < 100).all(), "Gravity anomaly contains extreme outliers"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])