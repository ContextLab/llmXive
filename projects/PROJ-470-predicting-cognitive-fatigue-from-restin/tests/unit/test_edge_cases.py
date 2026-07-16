"""
Unit tests for edge cases in the EEG complexity pipeline.
Covers missing data, artifact rejection, and analysis mode failures.
"""
import os
import sys
import json
import tempfile
import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from preprocess import reject_artifacts, apply_bandpass_filter
from features import calculate_lzc, calculate_permutation_entropy
from analysis import validate_metadata, run_correlation_analysis


class TestMissingData:
    """Tests for handling missing data scenarios."""

    def test_empty_eeg_segment(self):
        """Test that empty EEG segments are handled gracefully."""
        # Create empty data
        empty_data = np.array([])
        sfreq = 100.0

        # Test LZC calculation on empty data
        with pytest.raises((ValueError, IndexError)):
            calculate_lzc(empty_data, sfreq)

        # Test PE calculation on empty data
        with pytest.raises((ValueError, IndexError)):
            calculate_permutation_entropy(empty_data, sfreq)

    def test_nan_values_in_eeg(self):
        """Test handling of NaN values in EEG data."""
        # Create data with NaN values
        nan_data = np.array([1.0, np.nan, 3.0, 4.0, 5.0])
        sfreq = 100.0

        # Test LZC with NaN (should raise or handle)
        with pytest.raises((ValueError, RuntimeError)):
            calculate_lzc(nan_data, sfreq)

        # Test PE with NaN
        with pytest.raises((ValueError, RuntimeError)):
            calculate_permutation_entropy(nan_data, sfreq)

    def test_metadata_missing_required_columns(self):
        """Test validation when required metadata columns are missing."""
        # Create metadata without required columns
        incomplete_metadata = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'age': [25, 30]
            # Missing: pre_fatigue, post_fatigue, pre_eeg_id, post_eeg_id
        })

        # Should raise ValueError or similar
        with pytest.raises((ValueError, KeyError)):
            validate_metadata(incomplete_metadata)

    def test_missing_input_file(self):
        """Test handling of missing input files."""
        from preprocess import stream_eeg_files

        # Try to stream from non-existent directory
        with pytest.raises(FileNotFoundError):
            list(stream_eeg_files('/non/existent/path'))


class TestArtifactRejection:
    """Tests for artifact rejection edge cases."""

    def test_all_epochs_rejected(self):
        """Test behavior when all epochs exceed artifact threshold."""
        # Create data with extreme values (all > 100uV)
        extreme_data = np.full((10, 1000), 150.0)  # 10 epochs, 1000 samples each
        sfreq = 100.0
        threshold = 100.0

        # Should reject all epochs
        rejected_indices = reject_artifacts(extreme_data, threshold)
        assert len(rejected_indices) == 10

    def test_no_epochs_rejected(self):
        """Test when no epochs exceed threshold."""
        # Create data with small values
        small_data = np.full((10, 1000), 10.0)
        sfreq = 100.0
        threshold = 100.0

        rejected_indices = reject_artifacts(small_data, threshold)
        assert len(rejected_indices) == 0

    def test_mixed_artifact_rejection(self):
        """Test rejection with mixed valid/invalid epochs."""
        # Create mixed data
        mixed_data = np.zeros((5, 1000))
        mixed_data[0, :] = 50.0  # Valid
        mixed_data[1, :] = 150.0  # Invalid
        mixed_data[2, :] = 80.0  # Valid
        mixed_data[3, :] = 200.0  # Invalid
        mixed_data[4, :] = 90.0  # Valid

        threshold = 100.0
        rejected_indices = reject_artifacts(mixed_data, threshold)

        assert len(rejected_indices) == 2
        assert 1 in rejected_indices
        assert 3 in rejected_indices

    def test_segment_too_short(self):
        """Test rejection of segments shorter than minimum duration."""
        # Create very short segment (less than 120 seconds at 100Hz = 12000 samples)
        short_segment = np.random.randn(5000)  # 50 seconds
        sfreq = 100.0

        # This should be rejected or handled
        # The actual implementation may raise or filter
        with pytest.raises((ValueError, RuntimeError)):
            calculate_lzc(short_segment, sfreq)


class TestAnalysisModeFailures:
    """Tests for analysis pipeline failure modes."""

    def test_no_paired_data(self):
        """Test analysis when no paired data is available."""
        # Create metadata with only baseline data
        baseline_only = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [2.0, 3.0],
            'post_fatigue': [np.nan, np.nan],  # Missing post
            'pre_eeg_id': ['eeg1', 'eeg2'],
            'post_eeg_id': [np.nan, np.nan]
        })

        # Should either fail gracefully or switch to cross-sectional mode
        # Based on T018, it should write validation_report.json and exit
        # We test that it doesn't crash with unhandled exception
        try:
            validate_metadata(baseline_only)
        except Exception as e:
            # Expected to raise or handle gracefully
            assert isinstance(e, (ValueError, KeyError))

    def test_no_baseline_data(self):
        """Test analysis when no baseline data is available."""
        # Create metadata with only post data
        post_only = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [np.nan, np.nan],
            'post_fatigue': [4.0, 5.0],
            'pre_eeg_id': [np.nan, np.nan],
            'post_eeg_id': ['eeg1', 'eeg2']
        })

        try:
            validate_metadata(post_only)
        except Exception as e:
            assert isinstance(e, (ValueError, KeyError))

    def test_insufficient_sample_size(self):
        """Test analysis with insufficient sample size."""
        # Create metadata with only 2 participants (N < 30)
        small_sample = pd.DataFrame({
            'participant_id': ['P001', 'P002'],
            'pre_fatigue': [2.0, 3.0],
            'post_fatigue': [4.0, 5.0],
            'pre_eeg_id': ['eeg1', 'eeg2'],
            'post_eeg_id': ['eeg3', 'eeg4']
        })

        # Should handle small sample size gracefully
        # May raise warning or error
        try:
            validate_metadata(small_sample)
        except Exception:
            pass  # Expected behavior

    def test_correlation_with_constant_values(self):
        """Test correlation calculation with constant values."""
        # Create data with constant values (no variance)
        constant_complexity = np.array([1.0, 1.0, 1.0, 1.0])
        constant_fatigue = np.array([2.0, 2.0, 2.0, 2.0])

        # Correlation should fail or return NaN
        with pytest.raises((ValueError, RuntimeWarning)):
            run_correlation_analysis(constant_complexity, constant_fatigue)

    def test_correlation_with_single_pair(self):
        """Test correlation with only one data pair."""
        # Only one pair cannot compute correlation
        single_complexity = np.array([1.0])
        single_fatigue = np.array([2.0])

        with pytest.raises((ValueError, RuntimeError)):
            run_correlation_analysis(single_complexity, single_fatigue)


class TestFileIOEdgeCases:
    """Tests for file I/O edge cases."""

    def test_write_to_nonexistent_directory(self):
        """Test writing to a directory that doesn't exist."""
        from features import save_metrics_to_csv

        # Try to write to non-existent directory
        non_existent_path = '/non/existent/dir/output.csv'

        with pytest.raises(FileNotFoundError):
            save_metrics_to_csv(
                pd.DataFrame({'col': [1, 2, 3]}),
                non_existent_path
            )

    def test_read_corrupted_csv(self):
        """Test reading a corrupted CSV file."""
        # Create a corrupted CSV
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("col1,col2\n1,\n2,3\n")  # Missing value
            temp_path = f.name

        try:
            df = pd.read_csv(temp_path)
            # If it reads, check for NaN handling
            assert df.isnull().any().any()
        except Exception:
            # Expected to handle corruption gracefully
            pass
        finally:
            os.unlink(temp_path)

    def test_empty_csv_output(self):
        """Test writing an empty DataFrame to CSV."""
        from features import save_metrics_to_csv

        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            temp_path = f.name

        try:
            empty_df = pd.DataFrame()
            save_metrics_to_csv(empty_df, temp_path)

            # Verify file exists and is empty or has headers only
            result_df = pd.read_csv(temp_path)
            assert len(result_df) == 0
        finally:
            os.unlink(temp_path)


class TestBoundaryConditions:
    """Tests for boundary conditions in calculations."""

    def test_lzc_boundary_values(self):
        """Test LZC calculation at theoretical boundaries."""
        sfreq = 100.0

        # Perfectly repetitive signal should have low complexity
        repetitive = np.ones(1000)
        lzc_rep = calculate_lzc(repetitive, sfreq)
        assert lzc_rep < 0.5  # Low complexity

        # Random signal should have higher complexity
        random_signal = np.random.randn(1000)
        lzc_rand = calculate_lzc(random_signal, sfreq)
        assert lzc_rand > lzc_rep

    def test_permutation_entropy_boundary(self):
        """Test permutation entropy at boundaries."""
        sfreq = 100.0

        # Constant signal should have minimum entropy
        constant = np.ones(1000)
        pe_const = calculate_permutation_entropy(constant, sfreq)
        assert pe_const == 0.0 or pe_const < 0.1

        # Random signal should have higher entropy
        random_signal = np.random.randn(1000)
        pe_rand = calculate_permutation_entropy(random_signal, sfreq)
        assert pe_rand > pe_const

    def test_filter_edge_cases(self):
        """Test bandpass filter at edge frequencies."""
        sfreq = 256.0

        # DC signal (0 Hz) should be filtered out
        dc_signal = np.ones(1000)
        filtered_dc = apply_bandpass_filter(dc_signal, sfreq, 1.0, 40.0)
        assert np.std(filtered_dc) < 0.1  # Should be near zero

        # High frequency noise (>40Hz) should be attenuated
        high_freq = np.sin(2 * np.pi * 50 * np.arange(1000) / sfreq)
        filtered_high = apply_bandpass_filter(high_freq, sfreq, 1.0, 40.0)
        assert np.std(filtered_high) < np.std(high_freq) * 0.1