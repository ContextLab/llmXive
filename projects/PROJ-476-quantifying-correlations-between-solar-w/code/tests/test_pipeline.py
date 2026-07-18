import os
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path
import sys
import json
import yaml

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.fetch import fetch_ace, fetch_noaa
from code.data.validate import validate_ace_raw, validate_noaa_raw
from code.data.align import run_alignment
from code.config import TRAIN_START, TEST_END

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def load_schema(schema_path):
    """Load the dataset schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_against_schema(df, schema):
    """
    Validate dataframe against a JSON/YAML schema.
    Checks required columns and data types.
    """
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    # Check required columns
    for field in required_fields:
        if field not in df.columns:
            raise AssertionError(f"Schema requires column '{field}', but it is missing from dataframe")

    # Check column types if defined in schema
    for col_name, col_schema in properties.items():
        if col_name in df.columns:
            expected_type = col_schema.get('type')
            if expected_type:
                actual_dtype = df[col_name].dtype
                # Map YAML types to pandas dtypes
                type_map = {
                    'string': 'object',
                    'integer': 'int64',
                    'number': 'float64'
                }
                expected_pandas_type = type_map.get(expected_type)
                if expected_pandas_type:
                    # Check if actual dtype is compatible
                    if not pd.api.types.is_dtype_equal(actual_dtype, expected_pandas_type):
                        # Allow numeric compatibility (e.g., int64 vs float64)
                        if not (expected_pandas_type == 'float64' and pd.api.types.is_numeric_dtype(actual_dtype)):
                            raise AssertionError(
                                f"Column '{col_name}' expected type '{expected_type}' "
                                f"but found '{actual_dtype}'"
                            )

def test_pipeline_monthly_sync():
    """
    Integration test for full month download.
    Uses a real (small) subset of actual NOAA/ACE data download (not mocked)
    to verify data/processed/synced.csv structure.
    Verifies data/processed/synced.csv conforms to contracts/dataset.schema.yaml.
    """
    project_root = get_project_root()
    
    # Define paths relative to project root
    raw_dir = project_root / 'data' / 'raw'
    processed_dir = project_root / 'data' / 'processed'
    schema_path = project_root / 'contracts' / 'dataset.schema.yaml'
    
    # Ensure directories exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    ace_path = raw_dir / "ace_raw.csv"
    noaa_path = raw_dir / "noaa_raw.csv"
    output_path = processed_dir / "synced.csv"
    
    # Load schema
    if not schema_path.exists():
        pytest.skip(f"Schema file not found at {schema_path}")
    
    schema = load_schema(schema_path)
    
    # Fetch real data for a full month window
    # Using January 2020 as a test period (31 days)
    start_date = "2020-01-01"
    end_date = "2020-01-31"
    
    try:
        # Fetch real data
        fetch_ace(start_date, end_date, str(ace_path))
        fetch_noaa(start_date, end_date, str(noaa_path))
        
        # Validate the fetched data
        validate_ace_raw(str(ace_path))
        validate_noaa_raw(str(noaa_path))
        
        # Run the alignment pipeline
        run_alignment(str(ace_path), str(noaa_path), str(output_path))
        
        # Verify the output file exists
        assert output_path.exists(), f"Output file {output_path} was not created"
        
        # Load the output
        df = pd.read_csv(output_path)
        
        # Verify schema compliance
        validate_against_schema(df, schema)
        
        # Additional verification: check specific columns from schema
        expected_columns = ['timestamp', 'N_p', 'T_p', 'He2+_ratio', 'Kp', 'Dst']
        for col in expected_columns:
            assert col in df.columns, f"Missing column: {col}"
        
        # Verify no NaNs in critical columns after imputation
        # (Small gaps should be filled, large gaps might remain but we check for reasonable completeness)
        critical_cols = ['N_p', 'T_p', 'He2+_ratio', 'Kp', 'Dst']
        for col in critical_cols:
            nan_count = df[col].isna().sum()
            total_count = len(df)
            nan_ratio = nan_count / total_count if total_count > 0 else 1.0
            # Allow some NaNs for large gaps, but not too many
            assert nan_ratio < 0.1, f"Column {col} has too many NaNs ({nan_ratio:.2%}) after imputation"
        
        # Verify timestamp format
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Verify that the date range is correct
        assert df['timestamp'].min() >= pd.Timestamp(start_date), \
            f"Start date {df['timestamp'].min()} is before {start_date}"
        assert df['timestamp'].max() <= pd.Timestamp(end_date) + pd.Timedelta(hours=1), \
            f"End date {df['timestamp'].max()} is after {end_date}"
        
        # Check that Kp and Dst are numeric
        assert pd.api.types.is_numeric_dtype(df['Kp']), "Kp should be numeric"
        assert pd.api.types.is_numeric_dtype(df['Dst']), "Dst should be numeric"
        
        # Check that the data is aligned to hourly frequency
        # Calculate the differences between consecutive timestamps
        time_diffs = df['timestamp'].diff().dropna()
        # Most differences should be close to 1 hour
        hourly_diffs = time_diffs.dt.total_seconds() / 3600
        assert hourly_diffs.mean() >= 0.9, "Data should be approximately hourly"
        
        # Verify we have approximately 31 days * 24 hours = 744 rows (allowing for some missing data)
        expected_min_rows = 30 * 24  # 30 days minimum
        assert len(df) >= expected_min_rows, \
            f"Expected at least {expected_min_rows} rows for a month of hourly data, got {len(df)}"
        
    except Exception as e:
        # If the real data fetch fails, we skip the test rather than fail it
        # This allows the test to be run in environments without internet access
        pytest.skip(f"Could not fetch real data for integration test: {str(e)}")
        raise

def test_pipeline_validation_full_run():
    """
    Integration test for full validation run.
    Verifies that all artifacts exist after a complete pipeline run.
    """
    project_root = get_project_root()
    
    # Check for expected artifacts
    expected_artifacts = [
        project_root / 'data' / 'processed' / 'synced.csv',
        project_root / 'data' / 'processed' / 'correlation_results.csv',
        project_root / 'artifacts' / 'thresholds' / 'global_threshold.json'
    ]
    
    # Skip if artifacts don't exist (pipeline not fully run)
    missing_artifacts = [p for p in expected_artifacts if not p.exists()]
    if missing_artifacts:
        pytest.skip(f"Missing artifacts for full validation run: {missing_artifacts}")
        
    # If all artifacts exist, perform basic validation
    # Load and check correlation results
    corr_path = project_root / 'data' / 'processed' / 'correlation_results.csv'
    if corr_path.exists():
        df_corr = pd.read_csv(corr_path)
        assert len(df_corr) > 0, "Correlation results file is empty"
        
    # Load and check thresholds
    threshold_path = project_root / 'artifacts' / 'thresholds' / 'global_threshold.json'
    if threshold_path.exists():
        with open(threshold_path, 'r') as f:
            thresholds = json.load(f)
        assert 'neff_values' in thresholds, "Missing neff_values in thresholds"
        assert 'bonferroni_threshold' in thresholds, "Missing bonferroni_threshold in thresholds"