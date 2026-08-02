"""
Unit tests for calculate_sample_size.py functionality.

Tests the dynamic sample size calculation logic for T013c.
"""
import pytest
import os
import sys
import json
import tempfile
import shutil

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from metrics import calculate_dynamic_sample_size


class TestDynamicSampleSize:
    """Tests for the calculate_dynamic_sample_size function."""

    def test_minimum_threshold_when_small_flagged(self):
        """Test that minimum threshold is used when 5% is smaller."""
        # 5% of 100 = 5, but minimum is 10
        result = calculate_dynamic_sample_size(
            total_flagged_count=100,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 10

    def test_percentage_when_large_flagged(self):
        """Test that percentage is used when it exceeds minimum."""
        # 5% of 1000 = 50, minimum is 10, so 50 wins
        result = calculate_dynamic_sample_size(
            total_flagged_count=1000,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 50

    def test_max_limit_capping(self):
        """Test that max limit caps the sample size."""
        # 5% of 50000 = 2500, but max is 1000
        result = calculate_dynamic_sample_size(
            total_flagged_count=50000,
            minimum_threshold=10,
            percentage=0.05,
            max_limit=1000
        )
        assert result == 1000

    def test_zero_flagged_count(self):
        """Test behavior with zero flagged count."""
        result = calculate_dynamic_sample_size(
            total_flagged_count=0,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 10

    def test_negative_flagged_count(self):
        """Test behavior with negative flagged count (edge case)."""
        result = calculate_dynamic_sample_size(
            total_flagged_count=-100,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 10

    def test_custom_percentage(self):
        """Test with custom percentage value."""
        # 10% of 200 = 20
        result = calculate_dynamic_sample_size(
            total_flagged_count=200,
            minimum_threshold=5,
            percentage=0.10
        )
        assert result == 20

    def test_boundary_exact_match(self):
        """Test when percentage exactly equals minimum."""
        # 5% of 200 = 10, minimum = 10, so result is 10
        result = calculate_dynamic_sample_size(
            total_flagged_count=200,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 10

    def test_fractional_rounding(self):
        """Test that fractional results are truncated (int)."""
        # 5% of 11 = 0.55, int(0.55) = 0, so minimum wins (10)
        result = calculate_dynamic_sample_size(
            total_flagged_count=11,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 10

        # 5% of 300 = 15, minimum = 10, so 15 wins
        result = calculate_dynamic_sample_size(
            total_flagged_count=300,
            minimum_threshold=10,
            percentage=0.05
        )
        assert result == 15
