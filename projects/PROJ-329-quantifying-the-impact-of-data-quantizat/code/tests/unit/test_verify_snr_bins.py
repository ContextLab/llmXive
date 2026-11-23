"""
Unit tests for SNR bin coverage and tolerance verification (T013a).
"""

import pytest
import numpy as np
import sys
from pathlib import Path
from src.verify_snr_bins import verify_bin_coverage, verify_snr_tolerance, SNR_BINS, TARGET_SNR_RANGE, SNR_TOLERANCE


class TestBinCoverage:
    """Tests for verify_bin_coverage function."""

    def test_full_range_covered(self):
        """Test that a set covering the full range returns True."""
        # Construct a set that spans 8 to 50
        values = [8.0, 14.0, 20.0, 30.0, 50.0]
        result = verify_bin_coverage(values)
        assert result['full_range_covered'] is True
        assert all(v == 'covered' for v in result['bin_coverage'].values())

    def test_range_not_covered_low(self):
        """Test that a set missing the lower bound returns False."""
        values = [10.0, 15.0, 25.0, 35.0, 45.0] # Missing < 8
        result = verify_bin_coverage(values)
        assert result['full_range_covered'] is False

    def test_range_not_covered_high(self):
        """Test that a set missing the upper bound returns False."""
        values = [8.0, 14.0, 20.0, 30.0, 40.0] # Missing > 40 (up to 50)
        result = verify_bin_coverage(values)
        assert result['full_range_covered'] is False

    def test_empty_bin_detection(self):
        """Test that an empty bin is detected."""
        # All values in first bin
        values = [9.0, 10.0, 11.0, 12.0, 13.0]
        result = verify_bin_coverage(values)
        assert result['bin_coverage'][0] == 'covered'
        assert result['bin_coverage'][1] == 'empty'
        assert result['bin_coverage'][2] == 'empty'
        assert result['bin_coverage'][3] == 'empty'

    def test_empty_input(self):
        """Test handling of empty input list."""
        result = verify_bin_coverage([])
        assert result['full_range_covered'] is False
        assert all(v == 'empty' for v in result['bin_coverage'].values())

    def test_edge_case_exact_bounds(self):
        """Test values exactly at bin boundaries."""
        # Include exact boundaries: 8, 14, 20, 30, 50
        values = [8.0, 14.0, 20.0, 30.0, 50.0]
        result = verify_bin_coverage(values)
        # 8 is in bin 0, 14 is in bin 1 (since bin 0 is [8, 14)), etc.
        # Wait, the logic in verify_bin_coverage:
        # if i == len-1: include upper bound
        # else: exclude upper bound
        # Bin 0: [8, 14) -> 8 is in, 14 is NOT in.
        # Bin 1: [14, 20) -> 14 is in.
        # Bin 3: [30, 50] -> 50 is in.
        # So 8, 14, 20, 30, 50 should cover all bins.
        assert result['full_range_covered'] is True


class TestSNRToleranceConstants:
    """Tests to verify the constants match the specification."""

    def test_target_range(self):
        assert TARGET_SNR_RANGE == (8.0, 50.0)

    def test_tolerance(self):
        assert SNR_TOLERANCE == 0.5

    def test_bin_definitions(self):
        # Check that bins collectively cover the range and have correct boundaries
        expected_bins = [(8.0, 14.0), (14.0, 20.0), (20.0, 30.0), (30.0, 50.0)]
        assert SNR_BINS == expected_bins
        # Check continuity
        for i in range(len(SNR_BINS) - 1):
            assert SNR_BINS[i][1] == SNR_BINS[i+1][0]


class TestSNRToleranceVerification:
    """Tests for verify_snr_tolerance function."""

    def test_all_within_tolerance(self):
        """Test when all signals are within tolerance."""
        targets = [10.0, 20.0, 30.0]
        actuals = [10.1, 19.9, 30.4] # All diff < 0.5
        result = verify_snr_tolerance(targets, actuals)
        assert result['all_within_tolerance'] is True
        assert len(result['violations']) == 0

    def test_violation_detected(self):
        """Test when a signal exceeds tolerance."""
        targets = [10.0]
        actuals = [10.6] # Diff 0.6 > 0.5
        result = verify_snr_tolerance(targets, actuals)
        assert result['all_within_tolerance'] is False
        assert len(result['violations']) == 1
        assert result['violations'][0]['diff'] == 0.6

    def test_length_mismatch_raises(self):
        """Test that mismatched lengths raise ValueError."""
        targets = [10.0, 20.0]
        actuals = [10.0]
        with pytest.raises(ValueError):
            verify_snr_tolerance(targets, actuals)

    def test_statistics(self):
        """Test that max and mean diff are calculated correctly."""
        targets = [10.0, 20.0]
        actuals = [10.2, 20.8] # Diffs: 0.2, 0.8
        result = verify_snr_tolerance(targets, actuals)
        assert result['max_diff'] == 0.8
        assert result['mean_diff'] == 0.5