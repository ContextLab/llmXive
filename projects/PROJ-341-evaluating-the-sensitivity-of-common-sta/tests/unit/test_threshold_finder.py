"""Unit tests for threshold identification logic."""
import pytest
import json
import os
import tempfile
from code.analysis.threshold_finder import (
    wilson_score_interval,
    calculate_confidence_intervals,
    find_type_i_threshold,
    find_power_threshold,
    save_thresholds
)

class TestWilsonScoreInterval:
    """Tests for Wilson score interval calculation."""
    
    def test_wilson_interval_basic(self):
        """Test basic Wilson score interval calculation."""
        # With 5 successes out of 100 trials at 95% confidence
        lower, upper = wilson_score_interval(5, 100, confidence=0.95)
        
        # Should return valid probabilities
        assert 0.0 <= lower <= 1.0
        assert 0.0 <= upper <= 1.0
        assert lower <= upper
        
    def test_wilson_interval_zero_successes(self):
        """Test Wilson score with zero successes."""
        lower, upper = wilson_score_interval(0, 100, confidence=0.95)
        
        assert lower == 0.0
        assert 0.0 <= upper <= 1.0
        
    def test_wilson_interval_all_successes(self):
        """Test Wilson score with all successes."""
        lower, upper = wilson_score_interval(100, 100, confidence=0.95)
        
        assert 0.0 <= lower <= 1.0
        assert upper == 1.0
        
    def test_wilson_interval_empty_sample(self):
        """Test Wilson score with zero trials."""
        lower, upper = wilson_score_interval(0, 0, confidence=0.95)
        
        assert lower == 0.0
        assert upper == 0.0
        
    def test_wilson_interval_confidence_levels(self):
        """Test Wilson score with different confidence levels."""
        lower_95, upper_95 = wilson_score_interval(50, 100, confidence=0.95)
        lower_99, upper_99 = wilson_score_interval(50, 100, confidence=0.99)
        
        # Higher confidence should give wider interval
        assert (upper_99 - lower_99) > (upper_95 - lower_95)
        
class TestCalculateConfidenceIntervals:
    """Tests for confidence interval calculation on error rate data."""
    
    def test_calculate_ci_null_hypothesis(self):
        """Test CI calculation for null hypothesis (Type I error)."""
        data = [{
            'test_type': 't-test',
            'effect_size': 0.0,
            'sample_size': 30,
            'hypothesis': 'null',
            'type1_errors': 5,
            'type2_errors': 0,
            'iterations': 100
        }]
        
        results = calculate_confidence_intervals(data)
        
        assert len(results) == 1
        assert 'type1_ci_lower' in results[0]
        assert 'type1_ci_upper' in results[0]
        assert 'power_ci_lower' not in results[0]
        
    def test_calculate_ci_alternative_hypothesis(self):
        """Test CI calculation for alternative hypothesis (power)."""
        data = [{
            'test_type': 't-test',
            'effect_size': 0.5,
            'sample_size': 30,
            'hypothesis': 'alternative',
            'type1_errors': 0,
            'type2_errors': 20,
            'iterations': 100
        }]
        
        results = calculate_confidence_intervals(data)
        
        assert len(results) == 1
        assert 'power_ci_lower' in results[0]
        assert 'power_ci_upper' in results[0]
        assert 'type1_ci_lower' not in results[0]
        
    def test_calculate_ci_mixed_hypotheses(self):
        """Test CI calculation with mixed hypotheses."""
        data = [
            {
                'test_type': 't-test',
                'effect_size': 0.0,
                'sample_size': 30,
                'hypothesis': 'null',
                'type1_errors': 5,
                'type2_errors': 0,
                'iterations': 100
            },
            {
                'test_type': 't-test',
                'effect_size': 0.5,
                'sample_size': 30,
                'hypothesis': 'alternative',
                'type1_errors': 0,
                'type2_errors': 20,
                'iterations': 100
            }
        ]
        
        results = calculate_confidence_intervals(data)
        
        assert len(results) == 2
        assert 'type1_ci_lower' in results[0]
        assert 'power_ci_lower' in results[1]

class TestFindTypeIThreshold:
    """Tests for Type I error threshold identification."""
    
    def test_find_type_i_threshold_exceeded(self):
        """Test finding threshold when Type I error exceeds alpha."""
        data = [
            {
                'test_type': 't-test',
                'effect_size': 0.0,
                'sample_size': 10,
                'hypothesis': 'null',
                'type1_errors': 2,
                'type2_errors': 0,
                'iterations': 100,
                'type1_ci_lower': 0.02,
                'type1_ci_upper': 0.15
            },
            {
                'test_type': 't-test',
                'effect_size': 0.0,
                'sample_size': 20,
                'hypothesis': 'null',
                'type1_errors': 10,
                'type2_errors': 0,
                'iterations': 100,
                'type1_ci_lower': 0.08,
                'type1_ci_upper': 0.22
            }
        ]
        
        thresholds = find_type_i_threshold(data, alpha=0.05)
        
        assert len(thresholds) == 1
        assert thresholds[0]['threshold_n'] == 20
        assert thresholds[0]['test_type'] == 't-test'
        
    def test_find_type_i_threshold_not_exceeded(self):
        """Test when Type I error never exceeds alpha."""
        data = [
            {
                'test_type': 't-test',
                'effect_size': 0.0,
                'sample_size': 10,
                'hypothesis': 'null',
                'type1_errors': 1,
                'type2_errors': 0,
                'iterations': 100,
                'type1_ci_lower': 0.005,
                'type1_ci_upper': 0.05
            }
        ]
        
        thresholds = find_type_i_threshold(data, alpha=0.05)
        
        assert len(thresholds) == 0
        
class TestFindPowerThreshold:
    """Tests for power threshold identification."""
    
    def test_find_power_threshold_below_target(self):
        """Test finding threshold when power stays below target."""
        data = [
            {
                'test_type': 't-test',
                'effect_size': 0.2,
                'sample_size': 10,
                'hypothesis': 'alternative',
                'type1_errors': 0,
                'type2_errors': 80,
                'iterations': 100,
                'power_ci_lower': 0.10,
                'power_ci_upper': 0.30
            },
            {
                'test_type': 't-test',
                'effect_size': 0.2,
                'sample_size': 20,
                'hypothesis': 'alternative',
                'type1_errors': 0,
                'type2_errors': 70,
                'iterations': 100,
                'power_ci_lower': 0.20,
                'power_ci_upper': 0.45
            },
            {
                'test_type': 't-test',
                'effect_size': 0.2,
                'sample_size': 30,
                'hypothesis': 'alternative',
                'type1_errors': 0,
                'type2_errors': 60,
                'iterations': 100,
                'power_ci_lower': 0.30,
                'power_ci_upper': 0.55
            }
        ]
        
        thresholds = find_power_threshold(data, power_target=0.80, consecutive_increments=3)
        
        assert len(thresholds) == 1
        assert thresholds[0]['threshold_n'] == 30
        
    def test_find_power_threshold_above_target(self):
        """Test when power exceeds target."""
        data = [
            {
                'test_type': 't-test',
                'effect_size': 0.5,
                'sample_size': 50,
                'hypothesis': 'alternative',
                'type1_errors': 0,
                'type2_errors': 10,
                'iterations': 100,
                'power_ci_lower': 0.85,
                'power_ci_upper': 0.95
            }
        ]
        
        thresholds = find_power_threshold(data, power_target=0.80, consecutive_increments=3)
        
        assert len(thresholds) == 0

class TestSaveThresholds:
    """Tests for threshold saving functionality."""
    
    def test_save_thresholds_creates_file(self):
        """Test that save_thresholds creates the output file."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            type_i_thresholds = [
                {
                    'test_type': 't-test',
                    'effect_size': 0.0,
                    'threshold_n': 20,
                    'ci_lower_at_threshold': 0.08,
                    'alpha': 0.05
                }
            ]
            power_thresholds = []
            
            save_thresholds(type_i_thresholds, power_thresholds, tmp_path)
            
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                data = json.load(f)
                
            assert 'type_i_thresholds' in data
            assert 'power_thresholds' in data
            assert 'metadata' in data
            assert len(data['type_i_thresholds']) == 1
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
                
    def test_save_thresholds_empty_lists(self):
        """Test saving with empty threshold lists."""
        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as tmp:
            tmp_path = tmp.name
        
        try:
            save_thresholds([], [], tmp_path)
            
            assert os.path.exists(tmp_path)
            
            with open(tmp_path, 'r') as f:
                data = json.load(f)
                
            assert len(data['type_i_thresholds']) == 0
            assert len(data['power_thresholds']) == 0
            
        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)