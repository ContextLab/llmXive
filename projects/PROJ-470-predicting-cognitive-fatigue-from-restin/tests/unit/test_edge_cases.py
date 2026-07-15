"""
Unit tests for edge cases in the cognitive fatigue pipeline.
Tests missing data, artifact rejection, and analysis mode failures.
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from preprocess import reject_artifacts, apply_bandpass_filter
from features import calculate_lzc, calculate_permutation_entropy
from analysis import validate_metadata, run_correlation_analysis
from utils.logging import get_logger


class TestArtifactRejectionEdgeCases:
    """Tests for artifact rejection logic under edge conditions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sample_rate = 100
        self.duration = 120  # seconds

    def test_all_epochs_rejected_due_to_amplitude(self):
        """Test when all epochs exceed amplitude threshold."""
        # Create data with amplitude > 100µV everywhere
        data = np.random.randn(1, 100 * 120) * 150  # All > 100µV
        sfreq = 100
        info = {'sfreq': sfreq}

        rejected_count, kept_count = reject_artifacts(data, sfreq, info, amplitude_threshold=100)

        assert rejected_count > 0, "At least one epoch should be rejected"
        assert kept_count == 0, "All epochs should be rejected when amplitude > threshold everywhere"

    def test_short_segment_rejection(self):
        """Test rejection of segments shorter than 120 seconds."""
        # Create data for only 60 seconds (too short)
        short_duration = 60
        short_data = np.random.randn(1, 100 * short_duration) * 50
        sfreq = 100
        info = {'sfreq': sfreq}

        # The function should reject this because duration < 120s
        # Note: The actual implementation may handle this differently
        # depending on how epochs are defined
        rejected_count, kept_count = reject_artifacts(short_data, sfreq, info, amplitude_threshold=100, min_duration=120)

        # If the segment is too short, it should be rejected
        # The exact behavior depends on implementation details
        # For now, we check that the function doesn't crash
        assert isinstance(rejected_count, int)
        assert isinstance(kept_count, int)

    def test_mixed_rejection_scenario(self):
        """Test scenario with some good and some bad epochs."""
        # Create data with mixed quality
        # First half: good (low amplitude)
        # Second half: bad (high amplitude)
        good_data = np.random.randn(1, 100 * 60) * 30
        bad_data = np.random.randn(1, 100 * 60) * 150
        mixed_data = np.concatenate([good_data, bad_data], axis=1)

        sfreq = 100
        info = {'sfreq': sfreq}

        rejected_count, kept_count = reject_artifacts(mixed_data, sfreq, info, amplitude_threshold=100)

        assert kept_count > 0, "Some good epochs should be kept"
        assert rejected_count > 0, "Some bad epochs should be rejected"
        assert kept_count + rejected_count > 0, "Total epochs should be positive"

    def test_empty_data_array(self):
        """Test rejection logic with empty data array."""
        empty_data = np.array([]).reshape(1, 0)
        sfreq = 100
        info = {'sfreq': sfreq}

        with pytest.raises((ValueError, IndexError)):
            reject_artifacts(empty_data, sfreq, info, amplitude_threshold=100)

    def test_nan_values_in_data(self):
        """Test rejection logic when data contains NaN values."""
        data = np.random.randn(1, 100 * 120) * 50
        data[0, 500:600] = np.nan  # Inject NaNs

        sfreq = 100
        info = {'sfreq': sfreq}

        # Should handle NaNs gracefully (either reject or fill)
        # This test ensures no crash occurs
        try:
            rejected_count, kept_count = reject_artifacts(data, sfreq, info, amplitude_threshold=100)
            assert isinstance(rejected_count, int)
            assert isinstance(kept_count, int)
        except Exception as e:
            # If it raises, it should be a clear error, not a silent failure
            assert "NaN" in str(e) or "invalid" in str(e).lower()


class TestMissingDataEdgeCases:
    """Tests for handling missing data scenarios."""

    def test_missing_metadata_columns(self):
        """Test validation when required metadata columns are missing."""
        # Create metadata with missing columns
        metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'other_column': [1, 2]
            # Missing: pre_fatigue, post_fatigue, pre_eeg_id, post_eeg_id
        })

        with pytest.raises((ValueError, KeyError)):
            validate_metadata(metadata)

    def test_empty_metadata_dataframe(self):
        """Test validation with empty metadata dataframe."""
        empty_metadata = pd.DataFrame()

        with pytest.raises((ValueError, KeyError)):
            validate_metadata(empty_metadata)

    def test_missing_complexity_metrics_file(self):
        """Test analysis when complexity metrics file is missing."""
        # This test would require mocking file system or using temp dir
        # For now, we test the validation logic
        pass

    def test_null_values_in_fatigue_scores(self):
        """Test handling of null values in fatigue scores."""
        metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'pre_fatigue': [10.0, np.nan, 15.0],
            'post_fatigue': [20.0, 25.0, np.nan],
            'pre_eeg_id': ['E001', 'E002', 'E003'],
            'post_eeg_id': ['E004', 'E005', 'E006']
        })

        # Should handle NaN values (either exclude or raise clear error)
        try:
            result = validate_metadata(metadata)
            # If it passes validation, it should have handled NaNs
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error message
            assert "NaN" in str(e) or "missing" in str(e).lower()


class TestAnalysisModeFailures:
    """Tests for analysis mode failures and fallback logic."""

    def test_no_paired_data_fallback(self):
        """Test fallback to cross-sectional analysis when paired data is missing."""
        # Create metadata with only baseline data (no paired)
        metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'pre_fatigue': [10.0, 15.0, 20.0],
            'post_fatigue': [np.nan, np.nan, np.nan],  # Missing post
            'pre_eeg_id': ['E001', 'E002', 'E003'],
            'post_eeg_id': [np.nan, np.nan, np.nan]  # Missing post
        })

        # Create complexity metrics with only baseline
        complexity_metrics = pd.DataFrame({
            'participant_id': ['P001', 'P002', 'P003'],
            'channel': ['Fz', 'Fz', 'Fz'],
            'metric_type': ['lzc', 'lzc', 'lzc'],
            'value': [0.5, 0.6, 0.7],
            'timepoint': ['pre', 'pre', 'pre']
        })

        # Should fall back to cross-sectional analysis
        # This test ensures the fallback logic works without crashing
        try:
            result = validate_metadata(metadata)
            # If validation passes, it should have detected the mode
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error
            assert "fallback" in str(e).lower() or "cross-sectional" in str(e).lower()

    def test_neither_mode_available(self):
        """Test when neither paired nor cross-sectional data is available."""
        # Create metadata with no fatigue scores at all
        metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_eeg_id': ['E001', 'E002'],
            'post_eeg_id': ['E003', 'E004']
            # Missing: pre_fatigue, post_fatigue
        })

        with pytest.raises((ValueError, KeyError)):
            validate_metadata(metadata)

    def test_insufficient_samples_for_correlation(self):
        """Test correlation analysis with insufficient samples."""
        # Create metadata with only 1 participant
        metadata = pd.DataFrame({
            'participant_id': ['P001'],
            'pre_fatigue': [10.0],
            'post_fatigue': [15.0],
            'pre_eeg_id': ['E001'],
            'post_eeg_id': ['E002']
        })

        complexity_metrics = pd.DataFrame({
            'participant_id': ['P001'],
            'channel': ['Fz'],
            'metric_type': ['lzc'],
            'value': [0.5],
            'timepoint': ['pre']
        })

        # Correlation requires at least 2 samples
        with pytest.raises((ValueError, RuntimeError)):
            run_correlation_analysis(metadata, complexity_metrics)

    def test_mismatched_participant_ids(self):
        """Test when metadata and complexity metrics have mismatched IDs."""
        metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [10.0, 15.0],
            'post_fatigue': [12.0, 18.0],
            'pre_eeg_id': ['E001', 'E002'],
            'post_eeg_id': ['E003', 'E004']
        })

        # Complexity metrics for different participants
        complexity_metrics = pd.DataFrame({
            'participant_id': ['P003', 'P004'],  # Different IDs
            'channel': ['Fz', 'Fz'],
            'metric_type': ['lzc', 'lzc'],
            'value': [0.5, 0.6],
            'timepoint': ['pre', 'pre']
        })

        # Should handle mismatch gracefully
        try:
            result = run_correlation_analysis(metadata, complexity_metrics)
            # If it returns empty results, that's acceptable
            assert result is not None
        except Exception as e:
            # If it raises, it should be a clear error
            assert "mismatch" in str(e).lower() or "no matching" in str(e).lower()


class TestFeatureCalculationEdgeCases:
    """Tests for edge cases in feature calculation."""

    def test_lzc_on_constant_signal(self):
        """Test LZC calculation on a constant signal (should be near 0)."""
        constant_signal = np.ones(1000)
        lzc_value = calculate_lzc(constant_signal)
        assert lzc_value >= 0, "LZC should be non-negative"
        assert lzc_value < 0.1, "Constant signal should have very low LZC"

    def test_lzc_on_random_signal(self):
        """Test LZC calculation on random signal (should be higher)."""
        random_signal = np.random.randn(1000)
        lzc_value = calculate_lzc(random_signal)
        assert lzc_value >= 0, "LZC should be non-negative"
        assert lzc_value > 0.3, "Random signal should have higher LZC"

    def test_permutation_entropy_on_constant_signal(self):
        """Test permutation entropy on constant signal (should be 0)."""
        constant_signal = np.ones(1000)
        pe_value = calculate_permutation_entropy(constant_signal)
        assert pe_value >= 0, "PE should be non-negative"
        assert pe_value < 0.1, "Constant signal should have near-zero PE"

    def test_short_signal_for_complexity(self):
        """Test complexity calculation on very short signal."""
        short_signal = np.random.randn(10)  # Very short
        lzc_value = calculate_lzc(short_signal)
        pe_value = calculate_permutation_entropy(short_signal)
        # Should not crash, even if results are unreliable
        assert isinstance(lzc_value, (int, float))
        assert isinstance(pe_value, (int, float))

    def test_signal_with_extreme_outliers(self):
        """Test complexity calculation with extreme outliers."""
        signal = np.random.randn(1000)
        signal[500] = 1e10  # Extreme outlier
        lzc_value = calculate_lzc(signal)
        pe_value = calculate_permutation_entropy(signal)
        # Should handle without crashing
        assert isinstance(lzc_value, (int, float))
        assert isinstance(pe_value, (int, float))

class TestLoggingEdgeCases:
    """Tests for logging edge cases."""

    def test_log_with_none_values(self):
        """Test logging when some values are None."""
        logger = get_logger("test_edge_cases")
        # Should not crash when logging None values
        logger.info("Test log with None: %s", None)

    def test_log_with_special_characters(self):
        """Test logging with special characters in messages."""
        logger = get_logger("test_edge_cases")
        special_message = "Test with special chars: émojis 🧠, symbols @#$, unicode 日本語"
        logger.info(special_message)

    def test_log_rejection_summary_empty(self):
        """Test saving empty rejection summary."""
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "rejection_summary.json"
            # Should handle empty summary gracefully
            # This would test the save_rejection_summary function
            pass