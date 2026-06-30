"""
Unit tests for the threshold_finder module.

Tests Wilson score interval calculation and threshold identification logic.
"""
import pytest
import os
import json
import tempfile
from unittest.mock import patch, MagicMock
import numpy as np

from code.analysis.threshold_finder import (
    wilson_score_interval,
    calculate_confidence_intervals,
    find_type_i_threshold,
    find_power_threshold,
    save_thresholds
)


class TestWilsonScoreInterval:
    """Tests for the Wilson score interval calculation."""

    def test_trivial_cases(self):
        """Test cases with 0 or 100% success rates."""
        # 0 successes
        lower, upper, point = wilson_score_interval(0, 100)
        assert point == 0.0
        assert lower == 0.0
        assert upper > 0.0  # Upper bound should be > 0 due to uncertainty
        
        # 100% successes
        lower, upper, point = wilson_score_interval(100, 100)
        assert point == 1.0
        assert upper == 1.0
        assert lower < 1.0

    def test_symmetric_confidence(self):
        """Test that confidence interval is symmetric around point estimate for large N."""
        # For large N, Wilson should approximate normal approximation
        successes = 50
        total = 100
        lower, upper, point = wilson_score_interval(successes, total)
        
        assert abs(point - 0.5) < 1e-6
        # Check that the interval contains the point estimate
        assert lower <= point <= upper

    def test_confidence_level(self):
        """Test that higher confidence gives wider intervals."""
        lower95, upper95, _ = wilson_score_interval(30, 100, confidence=0.95)
        lower99, upper99, _ = wilson_score_interval(30, 100, confidence=0.99)
        
        # 99% CI should be wider than 95% CI
        width95 = upper95 - lower95
        width99 = upper99 - lower99
        
        assert width99 > width95

    def test_small_sample_size(self):
        """Test behavior with very small sample sizes."""
        lower, upper, point = wilson_score_interval(1, 2)
        assert point == 0.5
        # With n=2, uncertainty should be very high
        assert upper - lower > 0.5

    def test_zero_total(self):
        """Test edge case with zero total trials."""
        lower, upper, point = wilson_score_interval(0, 0)
        assert point == 0.0
        assert lower == 0.0
        assert upper == 0.0


class TestCalculateConfidenceIntervals:
    """Tests for adding confidence intervals to data."""

    def test_adds_ci_columns(self):
        """Test that CI columns are added to each row."""
        data = [
            {
                'sample_size': 50,
                'error_rate': 0.05,
                'n_iterations': 1000,
                'test_type': 't-test',
                'hypothesis': 'null'
            }
        ]
        
        result = calculate_confidence_intervals(data)
        
        assert len(result) == 1
        assert 'ci_lower' in result[0]
        assert 'ci_upper' in result[0]
        assert 'ci_point' in result[0]

    def test_preserves_original_data(self):
        """Test that original data is preserved."""
        original_data = [
            {
                'sample_size': 50,
                'effect_size': 0.5,
                'error_rate': 0.05,
                'n_iterations': 1000,
                'test_type': 't-test',
                'hypothesis': 'null',
                'extra_field': 'keep_me'
            }
        ]
        
        result = calculate_confidence_intervals(original_data)
        
        assert result[0]['sample_size'] == 50
        assert result[0]['extra_field'] == 'keep_me'
        assert result[0]['ci_point'] == pytest.approx(0.05, rel=0.01)


class TestFindTypeIThreshold:
    """Tests for Type I error threshold identification."""

    def test_finds_threshold_when_lower_ci_exceeds_alpha(self):
        """Test detection when lower CI bound > alpha."""
        data = [
            {'sample_size': 10, 'test_type': 't-test', 'hypothesis': 'null', 
             'ci_lower': 0.02, 'ci_upper': 0.08, 'ci_point': 0.05},
            {'sample_size': 20, 'test_type': 't-test', 'hypothesis': 'null', 
             'ci_lower': 0.06, 'ci_upper': 0.12, 'ci_point': 0.09},  # Lower > 0.05
            {'sample_size': 30, 'test_type': 't-test', 'hypothesis': 'null', 
             'ci_lower': 0.04, 'ci_upper': 0.10, 'ci_point': 0.07}
        ]
        
        threshold = find_type_i_threshold(data, alpha=0.05)
        
        assert threshold is not None
        assert threshold['sample_size'] == 20
        assert threshold['test_type'] == 't-test'

    def test_returns_none_when_no_threshold(self):
        """Test when no sample size exceeds alpha."""
        data = [
            {'sample_size': 10, 'test_type': 't-test', 'hypothesis': 'null', 
             'ci_lower': 0.02, 'ci_upper': 0.08, 'ci_point': 0.05},
            {'sample_size': 20, 'test_type': 't-test', 'hypothesis': 'null', 
             'ci_lower': 0.03, 'ci_upper': 0.09, 'ci_point': 0.06}
        ]
        
        threshold = find_type_i_threshold(data, alpha=0.05)
        
        assert threshold is None

    def test_ignores_alternative_hypothesis(self):
        """Test that alternative hypothesis data is ignored."""
        data = [
            {'sample_size': 10, 'test_type': 't-test', 'hypothesis': 'alt', 
             'ci_lower': 0.80, 'ci_upper': 0.95, 'ci_point': 0.87}
        ]
        
        threshold = find_type_i_threshold(data, alpha=0.05)
        
        assert threshold is None


class TestFindPowerThreshold:
    """Tests for power threshold identification."""

    def test_finds_threshold_when_power_below_target_consecutively(self):
        """Test detection of insufficient power over consecutive samples."""
        # Create data where power upper bound is below 0.80 for 3 consecutive sizes
        data = [
            {'sample_size': 10, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.60, 'ci_lower': 0.40, 'ci_point': 0.50},
            {'sample_size': 20, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.65, 'ci_lower': 0.45, 'ci_point': 0.55},
            {'sample_size': 30, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.70, 'ci_lower': 0.50, 'ci_point': 0.60},
            {'sample_size': 40, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.85, 'ci_lower': 0.70, 'ci_point': 0.77}  # Recovers
        ]
        
        threshold = find_power_threshold(data, power_target=0.80, consecutive_count=3)
        
        assert threshold is not None
        assert threshold['sample_size'] == 30
        assert threshold['test_type'] == 't-test'

    def test_returns_none_when_power_sufficient(self):
        """Test when power is always above target."""
        data = [
            {'sample_size': 10, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.90, 'ci_lower': 0.80, 'ci_point': 0.85}
        ]
        
        threshold = find_power_threshold(data, power_target=0.80)
        
        assert threshold is None

    def test_requires_consecutive_failures(self):
        """Test that non-consecutive low power doesn't trigger threshold."""
        data = [
            {'sample_size': 10, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.60, 'ci_lower': 0.40, 'ci_point': 0.50},
            {'sample_size': 20, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.85, 'ci_lower': 0.75, 'ci_point': 0.80},  # Recovers
            {'sample_size': 30, 'test_type': 't-test', 'effect_size': 0.5, 
             'hypothesis': 'alt', 'ci_upper': 0.60, 'ci_lower': 0.40, 'ci_point': 0.50}
        ]
        
        threshold = find_power_threshold(data, power_target=0.80, consecutive_count=3)
        
        assert threshold is None


class TestSaveThresholds:
    """Tests for saving thresholds to JSON."""

    def test_saves_to_json(self):
        """Test that thresholds are saved correctly to JSON file."""
        thresholds = [
            {
                'threshold_type': 'type_i_deviation',
                'test_type': 't-test',
                'sample_size': 25,
                'observed_rate': 0.06
            }
        ]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            save_thresholds(thresholds, temp_path)
            
            with open(temp_path, 'r') as f:
                loaded = json.load(f)
            
            assert len(loaded) == 1
            assert loaded[0]['test_type'] == 't-test'
            assert loaded[0]['sample_size'] == 25
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

    def test_creates_directory_if_needed(self):
        """Test that output directory is created if it doesn't exist."""
        thresholds = [{'test_type': 't-test', 'sample_size': 10}]
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = os.path.join(temp_dir, 'subdir', 'thresholds.json')
            
            save_thresholds(thresholds, nested_path)
            
            assert os.path.exists(nested_path)