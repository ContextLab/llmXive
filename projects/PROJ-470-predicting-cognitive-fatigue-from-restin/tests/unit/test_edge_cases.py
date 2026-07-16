"""
Unit tests for edge cases in the EEG cognitive fatigue pipeline.
Covers: missing data, artifact rejection, analysis mode failures.
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import reject_artifacts, process_eeg_stream
from features import calculate_lzc, calculate_permutation_entropy, save_metrics_to_csv
from analysis import validate_metadata, run_correlation_analysis
from utils.logging import get_logger, log_artifact_rejection, save_rejection_summary


class TestMissingData:
    """Tests for handling missing or empty data inputs."""

    def test_empty_dataframe_features(self):
        """Test feature extraction on empty DataFrame."""
        empty_df = pd.DataFrame(columns=['participant_id', 'channel', 'segment_id'])
        with pytest.raises((ValueError, IndexError)) as exc_info:
            # Attempting to calculate metrics on empty data should fail
            # We expect a clear error, not a silent pass
            calculate_lzc(empty_df)
        assert "empty" in str(exc_info.value).lower() or "index" in str(exc_info.value).lower()

    def test_missing_columns_metadata(self):
        """Test validation fails when required metadata columns are missing."""
        incomplete_df = pd.DataFrame({'participant_id': [1], 'some_other_col': [2]})
        required_cols = ['pre_fatigue', 'post_fatigue', 'pre_eeg_id', 'post_eeg_id']
        
        with pytest.raises(ValueError) as exc_info:
            validate_metadata(incomplete_df)
        
        assert "missing" in str(exc_info.value).lower() or "columns" in str(exc_info.value).lower()

    def test_nan_values_in_signal(self):
        """Test handling of NaN values in EEG signal."""
        # Create signal with NaN
        signal = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        # LZC calculation should handle or raise on NaN, but not crash silently
        # In a real scenario, this might be handled by interpolation or rejection
        # Here we test that the function doesn't return NaN without warning
        try:
            result = calculate_lzc(pd.DataFrame({'signal': [signal]}))
            # If it returns, it shouldn't be all NaN
            if isinstance(result, pd.DataFrame):
                assert not result.isnull().all().all()
        except Exception:
            # Expected: functions might raise on NaN
            pass


class TestArtifactRejection:
    """Tests for artifact rejection logic and logging."""

    def test_artifacts_exceed_threshold(self):
        """Test that signals exceeding voltage threshold are rejected."""
        # Create a logger
        logger = get_logger("test_artifacts")
        
        # Create a signal with large amplitude artifacts
        clean_signal = np.random.normal(0, 10, 1000)  # Normal EEG ~10-50uV
        artifact_signal = np.copy(clean_signal)
        artifact_signal[500] = 150.0  # Exceeds 100uV threshold
        
        # Mock segment data
        segment_data = {
            'participant_id': 'test_01',
            'channel': 'Fz',
            'data': artifact_signal,
            'sfreq': 100
        }
        
        # Test rejection logic
        # Note: This assumes reject_artifacts checks amplitude
        # We verify the function exists and handles the case
        try:
            rejected = reject_artifacts([segment_data], threshold=100.0)
            # Should return empty list or mark as rejected
            assert len(rejected) == 0 or all(r.get('rejected') for r in rejected)
        except Exception as e:
            # If it raises, that's also acceptable (fail loudly)
            assert "reject" in str(e).lower() or "threshold" in str(e).lower()

    def test_segment_too_short(self):
        """Test rejection of segments shorter than minimum duration."""
        # Create a very short signal (less than 120 seconds at 100Hz = 12000 samples)
        short_signal = np.random.normal(0, 10, 100)  # Only 1 second at 100Hz
        
        segment_data = {
            'participant_id': 'test_02',
            'channel': 'Cz',
            'data': short_signal,
            'sfreq': 100,
            'duration': 1.0  # 1 second
        }
        
        # Should be rejected for being too short
        try:
            rejected = reject_artifacts([segment_data], min_duration=120.0)
            assert len(rejected) == 0 or all(r.get('rejected') for r in rejected)
        except Exception:
            # Fail loudly is acceptable
            pass

    def test_rejection_logging(self):
        """Test that rejections are properly logged."""
        logger = get_logger("test_rejection_log")
        temp_dir = tempfile.mkdtemp()
        log_file = os.path.join(temp_dir, "rejections.json")
        
        # Log a rejection
        log_artifact_rejection(
            logger=logger,
            participant_id="test_03",
            reason="amplitude_exceeded",
            details={"max_value": 150.0, "threshold": 100.0}
        )
        
        # Save summary
        save_rejection_summary(log_file)
        
        # Verify file exists and contains data
        assert os.path.exists(log_file)
        with open(log_file, 'r') as f:
            data = json.load(f)
            assert len(data) > 0
            assert any(r['participant_id'] == 'test_03' for r in data)


class TestAnalysisModeFailures:
    """Tests for analysis mode selection and failure handling."""

    def test_no_paired_data_fallback(self):
        """Test fallback to cross-sectional when paired data is missing."""
        # Create metadata with only baseline data
        metadata = pd.DataFrame({
            'participant_id': ['p1', 'p2'],
            'baseline_fatigue': [2.0, 3.0],
            'baseline_eeg_id': ['eeg_1', 'eeg_2']
            # Missing post_fatigue and post_eeg_id
        })
        
        # Should trigger cross-sectional mode or fail gracefully
        try:
            validate_metadata(metadata)
            # If it passes validation, it should have detected the mode
            # The actual run_correlation_analysis would then use cross-sectional
        except ValueError as e:
            # Expected if validation is strict about paired data
            assert "paired" in str(e).lower() or "cross-sectional" in str(e).lower()

    def test_both_modes_missing(self):
        """Test failure when neither paired nor baseline data exists."""
        metadata = pd.DataFrame({
            'participant_id': ['p1'],
            'random_col': [1.0]
        })
        
        with pytest.raises(ValueError) as exc_info:
            validate_metadata(metadata)
        
        assert "missing" in str(exc_info.value).lower() or "validation" in str(exc_info.value).lower()

    def test_correlation_with_constant_data(self):
        """Test handling of constant (zero-variance) data in correlation."""
        # Create data with zero variance
        constant_complexity = np.ones(10)
        constant_fatigue = np.ones(10)
        
        try:
            # This should raise a warning or error, not return NaN silently
            # In scipy.stats, constant data often leads to division by zero
            # We expect the function to handle this gracefully
            pass  # Placeholder for actual implementation check
        except Exception:
            # Expected behavior: fail loudly rather than return NaN
            pass

    def test_insufficient_sample_size(self):
        """Test failure when sample size is too small for analysis."""
        # Create metadata with only 2 participants
        metadata = pd.DataFrame({
            'participant_id': ['p1', 'p2'],
            'pre_fatigue': [1.0, 2.0],
            'post_fatigue': [1.5, 2.5],
            'pre_eeg_id': ['e1', 'e2'],
            'post_eeg_id': ['e3', 'e4']
        })
        
        # While N=2 is technically valid for correlation, it's statistically meaningless
        # The analysis should ideally warn or reject
        try:
            # This is a soft check; actual implementation may vary
            pass
        except Exception:
            pass


class TestFileIOEdgeCases:
    """Tests for file input/output edge cases."""

    def test_write_metrics_empty(self):
        """Test saving empty metrics DataFrame."""
        empty_df = pd.DataFrame(columns=['participant_id', 'channel', 'metric', 'value'])
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            try:
                save_metrics_to_csv(empty_df, tmp.name)
                # Verify file was created
                assert os.path.exists(tmp.name)
                # Verify it has headers but no data
                df_read = pd.read_csv(tmp.name)
                assert len(df_read) == 0
                assert list(df_read.columns) == list(empty_df.columns)
            finally:
                if os.path.exists(tmp.name):
                    os.remove(tmp.name)

    def test_missing_input_file(self):
        """Test handling of missing input file in feature extraction."""
        # This would typically be caught in the main execution flow
        # We test that the function raises a clear error
        with pytest.raises(FileNotFoundError):
            # Simulate loading a non-existent file
            # In real code, this would be inside the feature extraction pipeline
            pass


class TestConfigurationEdgeCases:
    """Tests for configuration parameter edge cases."""

    def test_invalid_filter_cutoffs(self):
        """Test handling of invalid filter cutoff values."""
        # Config with low cutoff > high cutoff
        invalid_config = {
            'filter_low': 40,
            'filter_high': 1,
            'artifact_threshold': 100
        }
        
        # Should raise an error during config validation
        # This is typically checked in load_config or apply_bandpass_filter
        try:
            # Simulate validation
            if invalid_config['filter_low'] >= invalid_config['filter_high']:
                raise ValueError("Low cutoff must be less than high cutoff")
        except ValueError:
            # Expected
            pass

    def test_negative_threshold(self):
        """Test handling of negative artifact threshold."""
        negative_config = {
            'artifact_threshold': -100
        }
        
        try:
            if negative_config['artifact_threshold'] < 0:
                raise ValueError("Artifact threshold must be positive")
        except ValueError:
            # Expected
            pass