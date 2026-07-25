"""
Integration test for T015: us1_main.py orchestration.

This test verifies that the full US1 pipeline runs end-to-end on a small
subset of data (or mock data if real data is unavailable in the test env)
and produces the expected output file.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pandas as pd
import numpy as np

# Import the main function to test
# We need to mock the config and data paths for the test
import sys
from unittest.mock import patch, MagicMock

# Add code directory to path if not already
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from us1_main import run_pipeline, load_raw_pupil_data
from config import get_config, reset_config, set_random_seed

def create_mock_raw_data(temp_dir: Path):
    """Creates a minimal valid CSV file in the temp directory to simulate raw data."""
    # Generate synthetic time series for pupil data (valid for testing logic, not real data)
    # Note: This is ONLY for the integration test to verify the pipeline flow.
    # In the real execution, T004 provides real data.
    np.random.seed(42)
    n_points = 1000
    time = np.arange(n_points) * 1.0  # 1ms steps
    # Simulate some pupil data with a trend
    pupil_left = 4.0 + 0.5 * np.sin(time / 100.0) + np.random.normal(0, 0.1, n_points)
    pupil_right = 4.1 + 0.5 * np.sin(time / 100.0) + np.random.normal(0, 0.1, n_points)
    
    df = pd.DataFrame({
        'time': time,
        'pupil_left': pupil_left,
        'pupil_right': pupil_right,
        'trial': np.repeat(1, n_points) # Fake trial column
    })
    
    csv_path = temp_dir / "raw_pupil_data.csv"
    df.to_csv(csv_path, index=False)
    return csv_path

def test_us1_main_orchestration():
    """
    Tests that us1_main.py can:
    1. Load data (mocked for test).
    2. Run preprocessing steps.
    3. Compute CLI.
    4. Write output to parquet.
    """
    # Setup temp directories
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        raw_dir = tmpdir / "data" / "raw"
        derived_dir = tmpdir / "data" / "derived"
        raw_dir.mkdir(parents=True)
        derived_dir.mkdir(parents=True)
        
        # Create mock data
        create_mock_raw_data(raw_dir)
        
        # Mock the config to use our temp directories
        mock_config = {
            'data_raw_dir': str(raw_dir),
            'data_derived_dir': str(derived_dir),
            'cli_window_size': 10,
            'cli_threshold_std': 0.5,
            'outlier_threshold': 3.0,
            'seed': 42
        }
        
        # Patch the config getter
        with patch('us1_main.get_config', return_value=MagicMock(**mock_config)):
            # Also patch the logger to avoid file writes during test
            with patch('us1_main.setup_pipeline_logger') as mock_logger:
                mock_logger.return_value = MagicMock()
                
                # Run the pipeline
                try:
                    run_pipeline()
                except Exception as e:
                    # If it fails, we check if it's a data issue or logic issue
                    # For this test, we expect it to succeed with mock data
                    raise e
        
        # Verify output exists
        output_file = derived_dir / "cli_time_series.parquet"
        assert output_file.exists(), f"Output file {output_file} was not created."
        
        # Verify content
        result_df = pd.read_parquet(output_file)
        assert 'cli_zscore' in result_df.columns, "cli_zscore column missing."
        assert 'window_id' in result_df.columns, "window_id column missing."
        assert len(result_df) > 0, "Result dataframe is empty."
        
        print(f"Integration test passed. Output: {result_df.head()}")

if __name__ == "__main__":
    test_us1_main_orchestration()