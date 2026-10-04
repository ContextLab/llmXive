"""
tests/test_metrics.py - Unit tests for code/analysis/metrics.py

Tests T016a:
- load_processed_data: Validates file existence and column checks.
- extract_pupil_metrics: Validates metric calculation logic.
- save_metrics: Validates file writing.
- Integration: Full pipeline execution.
"""
import os
import sys
import tempfile
import shutil
import numpy as np
import pandas as pd
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add code directory to path
code_path = Path(__file__).parent.parent
sys.path.insert(0, str(code_path))

from analysis.metrics import (
    load_processed_data,
    extract_pupil_metrics,
    save_metrics,
    run_metrics_pipeline,
    FEATURES_FILE
)

class TestLoadProcessedData:
    def test_file_not_found(self):
        """Test that FileNotFoundError is raised if file doesn't exist."""
        with patch('analysis.metrics.FEATURES_FILE', Path('/nonexistent/file.csv')):
            with pytest.raises(FileNotFoundError):
                load_processed_data()

    def test_missing_required_columns(self, tmp_path):
        """Test that ValueError is raised if required columns are missing."""
        # Create a temp file with missing columns
        df = pd.DataFrame({'subject_id': [1], 'other_col': [2]})
        temp_file = tmp_path / 'features.csv'
        df.to_csv(temp_file, index=False)

        with patch('analysis.metrics.FEATURES_FILE', temp_file):
            with pytest.raises(ValueError, match="Missing required columns"):
                load_processed_data()

    def test_load_success(self, tmp_path):
        """Test successful loading of valid data."""
        df = pd.DataFrame({
            'subject_id': [1, 2],
            'trial_id': [10, 20],
            'pupil_diameter': [3.5, 4.0]
        })
        temp_file = tmp_path / 'features.csv'
        df.to_csv(temp_file, index=False)

        with patch('analysis.metrics.FEATURES_FILE', temp_file):
            loaded_df = load_processed_data()
            assert len(loaded_df) == 2
            assert 'pupil_diameter' in loaded_df.columns

class TestExtractPupilMetrics:
    def test_basic_metric_calculation(self):
        """Test basic calculation of peak, mean, and quantiles."""
        data = {
            'subject_id': [1, 1, 1, 2, 2],
            'trial_id': [10, 10, 10, 20, 20],
            'pupil_diameter': [3.0, 4.0, 5.0, 2.0, 6.0]
        }
        df = pd.DataFrame(data)

        result = extract_pupil_metrics(df)

        # Check metrics for trial 10: [3, 4, 5] -> peak=5, mean=4, q25=3.5, q50=4, q75=4.5
        trial_10 = result[result['trial_id'] == 10].iloc[0]
        assert trial_10['pupil_peak'] == 5.0
        assert trial_10['pupil_mean'] == 4.0
        assert abs(trial_10['pupil_q25'] - 3.5) < 0.01
        assert trial_10['pupil_q50'] == 4.0
        assert abs(trial_10['pupil_q75'] - 4.5) < 0.01

    def test_missing_values_handling(self):
        """Test handling of NaN values in pupil_diameter."""
        data = {
            'subject_id': [1, 1, 1],
            'trial_id': [10, 10, 10],
            'pupil_diameter': [3.0, np.nan, 5.0]
        }
        df = pd.DataFrame(data)

        result = extract_pupil_metrics(df)

        # Should ignore NaN
        trial_10 = result[result['trial_id'] == 10].iloc[0]
        assert trial_10['pupil_peak'] == 5.0
        assert trial_10['pupil_mean'] == 4.0

    def test_single_value_per_trial(self):
        """Test metrics calculation when there's only one value per trial."""
        data = {
            'subject_id': [1, 2],
            'trial_id': [10, 20],
            'pupil_diameter': [3.5, 4.5]
        }
        df = pd.DataFrame(data)

        result = extract_pupil_metrics(df)

        assert result['pupil_peak'].iloc[0] == 3.5
        assert result['pupil_mean'].iloc[0] == 3.5
        assert result['pupil_q25'].iloc[0] == 3.5
        assert result['pupil_q50'].iloc[0] == 3.5
        assert result['pupil_q75'].iloc[0] == 3.5

    def test_time_series_collapse(self):
        """Test that time-series data is correctly collapsed to trial-level."""
        # Simulate time-series: multiple rows per trial
        data = {
            'subject_id': [1, 1, 1, 1],
            'trial_id': [10, 10, 10, 10],
            'pupil_diameter': [3.0, 4.0, 5.0, 6.0],
            'timestamp': [1, 2, 3, 4] # Extra column
        }
        df = pd.DataFrame(data)

        result = extract_pupil_metrics(df)

        # Should result in one row per trial
        assert len(result) == 1
        assert result['trial_id'].iloc[0] == 10
        assert result['pupil_peak'].iloc[0] == 6.0
        assert result['pupil_mean'].iloc[0] == 4.5

class TestSaveMetrics:
    def test_save_to_default_path(self, tmp_path):
        """Test saving to the default FEATURES_FILE path."""
        df = pd.DataFrame({
            'subject_id': [1],
            'trial_id': [10],
            'pupil_peak': [5.0]
        })
        
        # Temporarily override FEATURES_FILE
        temp_file = tmp_path / 'features.csv'
        with patch('analysis.metrics.FEATURES_FILE', temp_file):
            save_metrics(df)
            assert temp_file.exists()
            saved_df = pd.read_csv(temp_file)
            assert 'pupil_peak' in saved_df.columns

    def test_save_to_custom_path(self, tmp_path):
        """Test saving to a custom path."""
        df = pd.DataFrame({'col': [1]})
        custom_path = tmp_path / 'custom.csv'
        
        save_metrics(df, output_path=custom_path)
        assert custom_path.exists()

class TestRunMetricsPipeline:
    def test_full_pipeline(self, tmp_path):
        """Test the full pipeline execution."""
        # Prepare input data
        input_df = pd.DataFrame({
            'subject_id': [1, 1, 2],
            'trial_id': [10, 10, 20],
            'pupil_diameter': [3.0, 4.0, 5.0]
        })
        input_file = tmp_path / 'features.csv'
        input_df.to_csv(input_file, index=False)

        # Mock FEATURES_FILE
        with patch('analysis.metrics.FEATURES_FILE', input_file):
            result_df = run_metrics_pipeline()

            # Verify output
            assert 'pupil_peak' in result_df.columns
            assert 'pupil_mean' in result_df.columns
            assert len(result_df) == 2 # Two unique trials

    def test_pipeline_with_missing_file(self):
        """Test pipeline fails gracefully when input is missing."""
        with patch('analysis.metrics.FEATURES_FILE', Path('/nonexistent.csv')):
            with pytest.raises(FileNotFoundError):
                run_metrics_pipeline()

if __name__ == '__main__':
    pytest.main([__file__, '-v'])