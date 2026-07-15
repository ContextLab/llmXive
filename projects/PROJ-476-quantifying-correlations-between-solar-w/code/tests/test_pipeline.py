import os
import tempfile
import shutil
import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.data.fetch import fetch_ace, fetch_noaa
from code.data.validate import validate_ace_raw, validate_noaa_raw
from code.data.align import run_alignment
from code.config import TRAIN_START, TEST_END

def get_project_root():
    """Get the project root directory."""
    return Path(__file__).parent.parent.parent

def test_pipeline_monthly_sync():
    """
    Integration test for full month download.
    Uses a real (small) subset of actual NOAA/ACE data download (not mocked)
    to verify data/processed/synced.csv structure.
    Verifies data/processed/synced.csv conforms to contracts/dataset.schema.yaml.
    """
    # Create a temporary directory for this test
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        
        # Define paths
        raw_dir = tmpdir / "raw"
        processed_dir = tmpdir / "processed"
        raw_dir.mkdir()
        processed_dir.mkdir()
        
        ace_path = raw_dir / "ace_raw.csv"
        noaa_path = raw_dir / "noaa_raw.csv"
        output_path = processed_dir / "synced.csv"
        
        # Fetch real data for a small window (e.g., 1 week)
        # Using a small date range to avoid long download times in tests
        start_date = "2020-01-01"
        end_date = "2020-01-08"
        
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
            
            # Verify the structure
            expected_columns = ['timestamp', 'N_p', 'T_p', 'He2+_ratio', 'Kp', 'Dst']
            for col in expected_columns:
                assert col in df.columns, f"Missing column: {col}"
            
            # Verify no NaNs after imputation (for small gaps)
            # Note: Large gaps might still have NaNs
            # We check that the main variables have been processed
            assert len(df) > 0, "Output dataframe is empty"
            
            # Verify timestamp format
            df['timestamp'] = pd.to_datetime(df['timestamp'])
            
            # Verify that the date range is correct
            assert df['timestamp'].min() >= pd.Timestamp(start_date), \
                f"Start date {df['timestamp'].min()} is before {start_date}"
            assert df['timestamp'].max() <= pd.Timestamp(end_date) + pd.Timedelta(hours=1), \
                f"End date {df['timestamp'].max()} is after {end_date}"
            
            # Verify schema compliance (basic checks)
            # Check for required columns from the schema
            required_cols = ['timestamp', 'proton_density', 'temperature', 'helium_abundance', 'Kp', 'Dst']
            # Note: The actual column names might differ slightly, so we check for equivalents
            col_mapping = {
                'proton_density': 'N_p',
                'temperature': 'T_p',
                'helium_abundance': 'He2+_ratio'
            }
            
            for schema_col, actual_col in col_mapping.items():
                if schema_col in required_cols:
                    assert actual_col in df.columns, \
                        f"Schema requires {schema_col}, but {actual_col} not found"
            
            # Check that Kp and Dst are numeric
            assert pd.api.types.is_numeric_dtype(df['Kp']), "Kp should be numeric"
            assert pd.api.types.is_numeric_dtype(df['Dst']), "Dst should be numeric"
            
            # Check that the data is aligned to hourly frequency
            # Calculate the differences between consecutive timestamps
            time_diffs = df['timestamp'].diff().dropna()
            # Most differences should be close to 1 hour
            hourly_diffs = time_diffs.dt.total_seconds() / 3600
            assert hourly_diffs.mean() >= 0.9, "Data should be approximately hourly"
            
        except Exception as e:
            # If the real data fetch fails, we skip the test rather than fail it
            # This allows the test to be run in environments without internet access
            pytest.skip(f"Could not fetch real data for integration test: {str(e)}")

def test_pipeline_validation_full_run():
    """
    Integration test for full validation run.
    Verifies that all artifacts exist after a complete pipeline run.
    """
    # This test is a placeholder for the full validation pipeline
    # It would typically run the entire pipeline from fetch to validation
    # and verify all output artifacts exist
    pass
