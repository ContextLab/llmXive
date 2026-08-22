"""
Unit tests for code/processing/missing_fixation_handler.py
Task: T023
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import os

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from processing.missing_fixation_handler import identify_missing_trials, filter_and_log_missing_fixations

class TestIdentifyMissingTrials:
    """Tests for the identify_missing_trials function."""

    def test_all_valid_data(self):
        """Test that all rows are kept when no data is missing."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3],
            'first_fixation_prob': [0.5, 0.6, 0.7],
            'dwell_time_ms': [100.0, 200.0, 300.0],
            'latency_ms': [50.0, 60.0, 70.0],
            'fixation_count': [1, 2, 3]
        })
        
        valid_df, invalid_df, log = identify_missing_trials(df)
        
        assert len(valid_df) == 3
        assert len(invalid_df) == 0
        assert len(log) == 0

    def test_nan_in_critical_column(self):
        """Test that rows with NaN in critical columns are excluded."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3],
            'first_fixation_prob': [0.5, np.nan, 0.7],
            'dwell_time_ms': [100.0, 200.0, 300.0],
            'latency_ms': [50.0, 60.0, 70.0],
            'fixation_count': [1, 2, 3]
        })
        
        valid_df, invalid_df, log = identify_missing_trials(df)
        
        assert len(valid_df) == 2
        assert len(invalid_df) == 1
        assert invalid_df.iloc[0]['trial_id'] == 2
        assert len(log) == 1
        assert "Missing data in columns" in log[0]

    def test_none_in_critical_column(self):
        """Test that rows with None in critical columns are excluded."""
        df = pd.DataFrame({
            'trial_id': [1, 2, 3],
            'first_fixation_prob': [0.5, None, 0.7],
            'dwell_time_ms': [100.0, 200.0, 300.0],
            'latency_ms': [50.0, 60.0, 70.0],
            'fixation_count': [1, 2, 3]
        })
        
        valid_df, invalid_df, log = identify_missing_trials(df)
        
        assert len(valid_df) == 2
        assert len(invalid_df) == 1
        assert invalid_df.iloc[0]['trial_id'] == 2

    def test_multiple_missing_columns(self):
        """Test exclusion when multiple critical columns are missing."""
        df = pd.DataFrame({
            'trial_id': [1, 2],
            'first_fixation_prob': [np.nan, 0.6],
            'dwell_time_ms': [np.nan, 200.0],
            'latency_ms': [50.0, 60.0],
            'fixation_count': [1, 2]
        })
        
        valid_df, invalid_df, log = identify_missing_trials(df)
        
        assert len(valid_df) == 1
        assert len(invalid_df) == 1
        assert "first_fixation_prob" in log[0]
        assert "dwell_time_ms" in log[0]

    def test_missing_column_in_dataframe(self):
        """Test behavior when a critical column is missing from the dataframe."""
        df = pd.DataFrame({
            'trial_id': [1, 2],
            'first_fixation_prob': [0.5, 0.6],
            # dwell_time_ms is missing
            'latency_ms': [50.0, 60.0],
            'fixation_count': [1, 2]
        })
        
        # Should return all as invalid and log a warning about missing columns
        valid_df, invalid_df, log = identify_missing_trials(df)
        
        assert len(valid_df) == 0
        assert len(invalid_df) == 2
        assert len(log) == 1
        assert "Missing critical columns" in log[0]

class TestFilterAndLogMissingFixations:
    """Tests for the file I/O function filter_and_log_missing_fixations."""

    def test_filter_and_write(self, tmp_path):
        """Test reading a file, filtering, and writing the result."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        log_file = tmp_path / "log.txt"

        # Create input with missing data
        df_input = pd.DataFrame({
            'trial_id': [1, 2, 3, 4],
            'first_fixation_prob': [0.5, np.nan, 0.7, 0.8],
            'dwell_time_ms': [100.0, 200.0, np.nan, 400.0],
            'latency_ms': [50.0, 60.0, 70.0, 80.0],
            'fixation_count': [1, 2, 3, 4]
        })
        df_input.to_csv(input_file, index=False)

        count = filter_and_log_missing_fixations(input_file, output_file, log_file)

        # Check exclusion count (rows 2 and 3 have NaN)
        assert count == 2

        # Check output file
        assert output_file.exists()
        df_output = pd.read_csv(output_file)
        assert len(df_output) == 2
        # Should contain trials 1 and 4
        assert set(df_output['trial_id']) == {1, 4}

        # Check log file
        assert log_file.exists()
        log_content = log_file.read_text()
        assert "Excluded" in log_content
        assert "2" in log_content

    def test_no_missing_data(self, tmp_path):
        """Test behavior when input has no missing data."""
        input_file = tmp_path / "input.csv"
        output_file = tmp_path / "output.csv"
        log_file = tmp_path / "log.txt"

        df_input = pd.DataFrame({
            'trial_id': [1, 2],
            'first_fixation_prob': [0.5, 0.6],
            'dwell_time_ms': [100.0, 200.0],
            'latency_ms': [50.0, 60.0],
            'fixation_count': [1, 2]
        })
        df_input.to_csv(input_file, index=False)

        count = filter_and_log_missing_fixations(input_file, output_file, log_file)

        assert count == 0
        assert output_file.exists()
        df_output = pd.read_csv(output_file)
        assert len(df_output) == 2

    def test_input_file_not_found(self, tmp_path):
        """Test that FileNotFoundError is raised if input doesn't exist."""
        input_file = tmp_path / "nonexistent.csv"
        output_file = tmp_path / "output.csv"

        with pytest.raises(FileNotFoundError):
            filter_and_log_missing_fixations(input_file, output_file)