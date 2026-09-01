"""
Unit tests for detection threshold validation module.
"""

import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import json

# Import the module under test
from analysis.detection_threshold import (
    calculate_signal_to_noise_ratio,
    validate_detection_thresholds,
    generate_summary_statistics,
    DEFAULT_DETECTION_LIMIT,
    DEFAULT_MIN_SNR
)


class TestCalculateSNR:
    """Tests for SNR calculation function."""

    def test_valid_snr_above_limit(self):
        """Test SNR calculation for a valid measurement above detection limit."""
        lifetime = 50.0e-9  # 50 ns
        uncertainty = 5.0e-9  # 5 ns
        detection_limit = 1.0e-9  # 1 ns

        snr, is_valid = calculate_signal_to_noise_ratio(
            lifetime, uncertainty, detection_limit
        )

        # Signal = 50ns - 1ns = 49ns
        # SNR = 49ns / 5ns = 9.8
        expected_snr = 49.0e-9 / 5.0e-9
        assert is_valid is True
        assert abs(snr - expected_snr) < 1e-6

    def test_lifetime_at_detection_limit(self):
        """Test when lifetime equals detection limit."""
        lifetime = 1.0e-9
        uncertainty = 1.0e-9
        detection_limit = 1.0e-9

        snr, is_valid = calculate_signal_to_noise_ratio(
            lifetime, uncertainty, detection_limit
        )

        assert is_valid is False
        assert snr == 0.0

    def test_lifetime_below_detection_limit(self):
        """Test when lifetime is below detection limit."""
        lifetime = 0.5e-9
        uncertainty = 1.0e-9
        detection_limit = 1.0e-9

        snr, is_valid = calculate_signal_to_noise_ratio(
            lifetime, uncertainty, detection_limit
        )

        assert is_valid is False
        assert snr == 0.0

    def test_zero_uncertainty_handling(self):
        """Test that zero uncertainty is handled gracefully."""
        lifetime = 50.0e-9
        uncertainty = 0.0
        detection_limit = 1.0e-9

        # Should use default small uncertainty
        snr, is_valid = calculate_signal_to_noise_ratio(
            lifetime, uncertainty, detection_limit
        )

        assert is_valid is True
        assert snr > 0

    def test_negative_uncertainty_handling(self):
        """Test that negative uncertainty is handled gracefully."""
        lifetime = 50.0e-9
        uncertainty = -5.0e-9
        detection_limit = 1.0e-9

        snr, is_valid = calculate_signal_to_noise_ratio(
            lifetime, uncertainty, detection_limit
        )

        assert is_valid is True
        assert snr > 0


class TestValidateDetectionThresholds:
    """Tests for the main validation function."""

    def test_mixed_results_dataframe(self):
        """Test validation with a mix of valid, warning, and failed cases."""
        # Create test data
        data = {
            'solvent': ['cyclohexane', 'methanol', 'acetonitrile', 'invalid'],
            'lifetime_s': [50.0e-9, 1.5e-9, 0.5e-9, np.nan],
            'uncertainty_s': [5.0e-9, 1.0e-9, 1.0e-9, 1.0e-9]
        }
        df = pd.DataFrame(data)

        config = {
            'detection_limit_seconds': 1.0e-9,
            'minimum_snr': 3.0
        }

        result_df = validate_detection_thresholds(df, config)

        # Check that all rows are processed
        assert len(result_df) == 4

        # Check cyclohexane: 50ns, 5ns uncertainty -> SNR = 9.8 (PASS)
        cyclo_row = result_df[result_df['solvent'] == 'cyclohexane'].iloc[0]
        assert cyclo_row['flag'] == 'PASS'
        assert cyclo_row['snr'] > 3.0

        # Check methanol: 1.5ns, 1ns uncertainty -> SNR = 0.5 (WARN - above limit but low SNR)
        methanol_row = result_df[result_df['solvent'] == 'methanol'].iloc[0]
        assert methanol_row['flag'] == 'WARN'
        assert methanol_row['above_detection_limit'] is True
        assert methanol_row['meets_snr_threshold'] is False

        # Check acetonitrile: 0.5ns (below 1ns limit) -> FAIL
        acn_row = result_df[result_df['solvent'] == 'acetonitrile'].iloc[0]
        assert acn_row['flag'] == 'FAIL'
        assert acn_row['above_detection_limit'] is False

        # Check invalid: NaN lifetime -> FAIL
        invalid_row = result_df[result_df['solvent'] == 'invalid'].iloc[0]
        assert invalid_row['flag'] == 'FAIL'

    def test_all_passing(self):
        """Test when all measurements pass."""
        data = {
            'solvent': ['solvent_a', 'solvent_b'],
            'lifetime_s': [100.0e-9, 200.0e-9],
            'uncertainty_s': [10.0e-9, 20.0e-9]
        }
        df = pd.DataFrame(data)

        config = {
            'detection_limit_seconds': 1.0e-9,
            'minimum_snr': 3.0
        }

        result_df = validate_detection_thresholds(df, config)

        assert all(result_df['flag'] == 'PASS')

    def test_all_failing(self):
        """Test when all measurements fail."""
        data = {
            'solvent': ['solvent_a', 'solvent_b'],
            'lifetime_s': [0.5e-9, 0.8e-9],
            'uncertainty_s': [0.1e-9, 0.1e-9]
        }
        df = pd.DataFrame(data)

        config = {
            'detection_limit_seconds': 1.0e-9,
            'minimum_snr': 3.0
        }

        result_df = validate_detection_thresholds(df, config)

        assert all(result_df['flag'] == 'FAIL')


class TestGenerateSummaryStatistics:
    """Tests for summary statistics generation."""

    def test_summary_calculation(self):
        """Test that summary statistics are correctly calculated."""
        # Create a mock validation dataframe
        data = {
            'solvent': ['a', 'b', 'c', 'd'],
            'snr': [10.0, 5.0, 2.0, 0.0],
            'flag': ['PASS', 'PASS', 'WARN', 'FAIL'],
            'detection_limit_s': [1.0e-9, 1.0e-9, 1.0e-9, 1.0e-9],
            'min_snr_threshold': [3.0, 3.0, 3.0, 3.0]
        }
        df = pd.DataFrame(data)

        stats = generate_summary_statistics(df)

        assert stats['total_runs'] == 4
        assert stats['passed_count'] == 2
        assert stats['warned_count'] == 1
        assert stats['failed_count'] == 1
        assert abs(stats['pass_rate'] - 0.5) < 1e-6
        assert abs(stats['average_snr'] - 4.25) < 1e-6
        assert stats['min_snr_observed'] == 0.0
        assert stats['max_snr_observed'] == 10.0

    def test_empty_dataframe(self):
        """Test handling of empty dataframe."""
        df = pd.DataFrame(columns=['solvent', 'snr', 'flag', 'detection_limit_s', 'min_snr_threshold'])

        stats = generate_summary_statistics(df)

        assert stats['total_runs'] == 0
        assert stats['pass_rate'] == 0.0
        assert stats['average_snr'] is None