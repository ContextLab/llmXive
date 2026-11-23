import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import sys
import os
import logging
from io import StringIO

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "code"))

from ingestion import (
    check_zero_variance_subjects,
    apply_motion_exclusion,
    validate_schema,
    compute_global_signal_sd_per_run,
    compute_subject_average_global_signal_sd,
    compute_global_signal_mean_time_series,
    join_fmri_mwq_data
)

class TestZeroVarianceCheck:
    """Tests for T015: Zero-variance check implementation."""

    def test_no_zero_variance(self, caplog):
        """Test that subjects with non-zero variance are kept."""
        data = {
            'Subject_ID': ['S1', 'S2', 'S3'],
            'global_signal_sd': [0.5, 1.2, 0.8]
        }
        df = pd.DataFrame(data)
        
        filtered_df, log_msg = check_zero_variance_subjects(df, column='global_signal_sd')
        
        assert len(filtered_df) == 3
        assert "No subjects with zero variance found" in log_msg

    def test_with_zero_variance(self, caplog):
        """Test that subjects with zero variance are excluded and logged."""
        data = {
            'Subject_ID': ['S1', 'S2', 'S3', 'S4'],
            'global_signal_sd': [0.5, 0.0, 1.2, 0.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, log_msg = check_zero_variance_subjects(df, column='global_signal_sd')
        
        # S2 and S4 should be excluded
        assert len(filtered_df) == 2
        assert filtered_df['Subject_ID'].tolist() == ['S1', 'S3']
        
        # Check logging
        assert "Excluded 2 subjects with global_signal_sd == 0" in log_msg
        assert "Excluded Subject IDs: ['S2', 'S4']" in log_msg

    def test_missing_column(self, caplog):
        """Test behavior when the specified column is missing."""
        data = {
            'Subject_ID': ['S1', 'S2'],
            'other_col': [1.0, 2.0]
        }
        df = pd.DataFrame(data)
        
        filtered_df, log_msg = check_zero_variance_subjects(df, column='global_signal_sd')
        
        assert len(filtered_df) == 2 # No filtering happened
        assert "Column 'global_signal_sd' not found" in log_msg

class TestMotionExclusion:
    """Tests for T014: Motion exclusion implementation."""

    def test_motion_exclusion_threshold(self, caplog):
        """Test that subjects with high FD are excluded."""
        data = {
            'Subject_ID': ['S1', 'S2', 'S3'],
            'Mean_FD': [0.2, 0.6, 0.4]
        }
        df = pd.DataFrame(data)
        
        filtered_df = apply_motion_exclusion(df, threshold=0.5)
        
        assert len(filtered_df) == 2
        assert filtered_df['Subject_ID'].tolist() == ['S1', 'S3']
        assert "Excluded 1 subjects (FD > 0.5mm)" in caplog.text

class TestSchemaValidation:
    """Tests for T010: Schema validation."""

    def test_valid_schema(self):
        """Test that valid data passes validation."""
        data = {
            'Subject_ID': ['S1'],
            'global_signal': [1.0],
            'global_signal_sd': [0.5],
            'MWQ_Score': [10],
            'Age': [25],
            'Sex': ['M'],
            'Mean_FD': [0.2],
            'Mean_DVARS': [0.1]
        }
        df = pd.DataFrame(data)
        # Should not raise
        validate_schema(df)

    def test_invalid_schema(self):
        """Test that missing columns raise an error."""
        data = {
            'Subject_ID': ['S1'],
            'global_signal': [1.0]
        }
        df = pd.DataFrame(data)
        with pytest.raises(ValueError, match="FATAL: Dataset Mismatch"):
            validate_schema(df)

class TestGlobalSignalSDCalculation:
    """Tests for T012/T017: Verify global signal SD calculation matches manual calculation."""

    def test_compute_global_signal_mean_time_series_manual(self):
        """
        Verify compute_global_signal_mean_time_series matches manual mean across voxels.
        Input: Simulated 4D array (x, y, z, t) -> Output: 1D time series (t).
        """
        # Create deterministic dummy data
        # Shape: (10, 10, 10, 20) -> 1000 voxels, 20 timepoints
        np.random.seed(42)
        data_4d = np.random.rand(10, 10, 10, 20)
        
        # Manual calculation: mean across first 3 axes (spatial dimensions)
        expected_ts = np.mean(data_4d, axis=(0, 1, 2))
        
        # Function under test
        result_ts = compute_global_signal_mean_time_series(data_4d)
        
        assert result_ts.shape == expected_ts.shape
        np.testing.assert_array_almost_equal(result_ts, expected_ts)

    def test_compute_global_signal_sd_per_run_manual(self):
        """
        Verify compute_global_signal_sd_per_run matches manual std calculation.
        """
        # Create deterministic dummy data
        # Shape: (10, 10, 10, 20)
        np.random.seed(123)
        data_4d = np.random.rand(10, 10, 10, 20)
        
        # Step 1: Get global signal time series (manual)
        gs_ts = np.mean(data_4d, axis=(0, 1, 2))
        
        # Step 2: Calculate SD (manual) - using ddof=0 to match typical numpy default unless specified
        expected_sd = np.std(gs_ts)
        
        # Function under test
        result_sd = compute_global_signal_sd_per_run(data_4d)
        
        np.testing.assert_almost_equal(result_sd, expected_sd)

    def test_compute_subject_average_global_signal_sd_manual(self):
        """
        Verify compute_subject_average_global_signal_sd matches manual averaging.
        Input: List of SDs from multiple runs -> Output: Mean SD.
        """
        run_sds = [0.5, 1.0, 1.5]
        
        expected_avg = np.mean(run_sds)
        
        result_avg = compute_subject_average_global_signal_sd(run_sds)
        
        np.testing.assert_almost_equal(result_avg, expected_avg)

class TestExclusionLogic:
    """Tests for T018: Verify exclusion logic for missing pairs and high motion subjects."""

    def test_missing_pair_exclusion(self, caplog):
        """Test that subjects present in fMRI but missing MWQ are excluded."""
        fmri_data = pd.DataFrame({
            'Subject_ID': ['100307', '100408', '100509'],
            'global_signal_sd': [0.5, 0.6, 0.7],
            'Mean_FD': [0.2, 0.3, 0.4]
        })
        
        mwq_data = pd.DataFrame({
            'Subject_ID': ['100307', '100509'],  # 100408 is missing
            'MWQ_Score': [15, 20],
            'Age': [22, 25],
            'Sex': ['M', 'F']
        })
        
        # Capture log output
        log_stream = StringIO()
        handler = logging.StreamHandler(log_stream)
        logger = logging.getLogger('ingestion')
        logger.addHandler(handler)
        
        joined_df = join_fmri_mwq_data(fmri_data, mwq_data)
        
        # 100408 should be excluded due to missing MWQ
        assert len(joined_df) == 2
        assert '100408' not in joined_df['Subject_ID'].values
        
        log_output = log_stream.getvalue()
        assert "Excluded" in log_output or "missing" in log_output.lower() or "100408" in log_output
        
        logger.removeHandler(handler)

    def test_high_motion_exclusion_integration(self, caplog):
        """Test the integration of motion exclusion after joining data."""
        fmri_data = pd.DataFrame({
            'Subject_ID': ['100307', '100408', '100509'],
            'global_signal_sd': [0.5, 0.6, 0.7],
            'Mean_FD': [0.2, 0.6, 0.4]  # 100408 has high motion
        })
        
        mwq_data = pd.DataFrame({
            'Subject_ID': ['100307', '100408', '100509'],
            'MWQ_Score': [15, 20, 25],
            'Age': [22, 24, 25],
            'Sex': ['M', 'F', 'M']
        })
        
        # First join
        joined_df = join_fmri_mwq_data(fmri_data, mwq_data)
        assert len(joined_df) == 3
        
        # Then apply motion exclusion
        filtered_df = apply_motion_exclusion(joined_df, threshold=0.5)
        
        # 100408 should be excluded due to high motion (0.6 > 0.5)
        assert len(filtered_df) == 2
        assert '100408' not in filtered_df['Subject_ID'].values
        assert filtered_df['Subject_ID'].tolist() == ['100307', '100509']
        
        assert "Excluded" in caplog.text or "high motion" in caplog.text.lower()

    def test_combined_exclusion_logic(self, caplog):
        """Test combined exclusion: missing pair AND high motion."""
        fmri_data = pd.DataFrame({
            'Subject_ID': ['100307', '100408', '100509', '100610'],
            'global_signal_sd': [0.5, 0.6, 0.7, 0.8],
            'Mean_FD': [0.2, 0.6, 0.4, 0.3]  # 100408 high motion
        })
        
        mwq_data = pd.DataFrame({
            'Subject_ID': ['100307', '100509'],  # 100408 and 100610 missing MWQ
            'MWQ_Score': [15, 25],
            'Age': [22, 25],
            'Sex': ['M', 'M']
        })
        
        # Join (excludes 100408 and 100610 due to missing MWQ)
        joined_df = join_fmri_mwq_data(fmri_data, mwq_data)
        assert len(joined_df) == 2
        assert set(joined_df['Subject_ID']) == {'100307', '100509'}
        
        # Apply motion exclusion (no high motion in remaining)
        filtered_df = apply_motion_exclusion(joined_df, threshold=0.5)
        assert len(filtered_df) == 2
        
        # Verify 100408 (high motion) and 100610 (missing MWQ) are both gone
        assert '100408' not in filtered_df['Subject_ID'].values
        assert '100610' not in filtered_df['Subject_ID'].values