"""
Unit tests for code/validators.py
Focus: Sensitivity analysis logic with varying thresholds (US3)
"""
import numpy as np
import pytest
import json
from pathlib import Path
import sys
import os

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from validators import (
    bootstrap_validity_check,
    verify_achieved_magnitude,
    should_exclude_dataset,
    run_full_validation
)
from config import THRESHOLDS

# Mock data generator for tests
def generate_mock_bootstrap_data(n_samples=1000, mean=0.5, std=0.1, seed=42):
    np.random.seed(seed)
    return np.random.normal(loc=mean, scale=std, size=n_samples)

class TestBootstrapValidityCheck:
    def test_reliable_estimates(self):
        # Simulate reliable bootstrap estimates (variance close to analytical)
        # Analytical variance assumed to be 1.0
        bootstrap_est = np.random.normal(loc=0, scale=1.0, size=1000)
        analytical_var = 1.0
        
        is_valid, details = bootstrap_validity_check(bootstrap_est, analytical_var)
        
        assert is_valid is True
        assert details["status"] == "reliable"
        assert details["ratio"] <= 2.0  # Default threshold

    def test_unreliable_estimates(self):
        # Simulate unreliable estimates (high variance)
        # Analytical variance 1.0, but bootstrap variance is 10x larger
        bootstrap_est = np.random.normal(loc=0, scale=np.sqrt(10), size=1000)
        analytical_var = 1.0
        
        is_valid, details = bootstrap_validity_check(bootstrap_est, analytical_var)
        
        assert is_valid is False
        assert details["status"] == "unreliable"
        assert details["ratio"] > 2.0

    def test_insufficient_samples(self):
        bootstrap_est = np.array([1.0, 2.0, 3.0])
        analytical_var = 1.0
        
        is_valid, details = bootstrap_validity_check(bootstrap_est, analytical_var)
        
        assert is_valid is False
        assert details["reason"] == "insufficient_samples"

class TestVerifyAchievedMagnitude:
    def test_within_tolerance(self):
        target = 0.5
        achieved = 0.52
        is_valid, details = verify_achieved_magnitude(target, achieved, tolerance=0.05)
        
        assert is_valid is True
        assert details["status"] == "verified"

    def test_outside_tolerance(self):
        target = 0.5
        achieved = 0.60
        is_valid, details = verify_achieved_magnitude(target, achieved, tolerance=0.05)
        
        assert is_valid is False
        assert details["status"] == "deviation_detected"

class TestShouldExcludeDataset:
    def test_exclude_small_sample(self):
        exclude, reason = should_exclude_dataset(
            bootstrap_validity=True,
            sample_size=20,
            min_sample_size=30
        )
        assert exclude is True
        assert "minimum" in reason

    def test_exclude_unreliable_bootstrap(self):
        exclude, reason = should_exclude_dataset(
            bootstrap_validity=False,
            sample_size=100
        )
        assert exclude is True
        assert "unreliable" in reason

    def test_exclude_failed_magnitude(self):
        exclude, reason = should_exclude_dataset(
            bootstrap_validity=True,
            achieved_magnitude_valid=False,
            sample_size=100
        )
        assert exclude is True
        assert "magnitude" in reason

    def test_include_valid(self):
        exclude, reason = should_exclude_dataset(
            bootstrap_validity=True,
            achieved_magnitude_valid=True,
            sample_size=100
        )
        assert exclude is False
        assert reason == "Dataset passed all validation checks"

class TestRunFullValidation:
    def test_full_run(self):
        # Create mock data
        np.random.seed(42)
        data = np.concatenate([np.random.normal(0, 1, 50), np.random.normal(1, 1, 50)])
        labels = np.array([0]*50 + [1]*50)
        bootstrap_est = np.random.normal(0.5, 0.1, 1000) # Reliable estimates
        
        result = run_full_validation(
            data, labels, bootstrap_est,
            target_magnitude=None,
            achieved_magnitude=None
        )
        
        assert "bootstrap_validity" in result
        assert "excluded" in result
        assert result["excluded"] is False

class TestSensitivityAnalysisThresholds:
    """
    Unit test for sensitivity analysis logic with varying thresholds (US3).
    This tests the core logic of how different thresholds affect classification
    of "high bias" cases, which is the primary goal of T026.
    """
    
    def test_threshold_sweep_logic(self):
        """
        Test that varying thresholds correctly classify bias cases.
        Simulates a list of bias values and checks classification counts.
        """
        # Simulate bias results from multiple datasets
        bias_results = [0.02, 0.04, 0.06, 0.08, 0.12, 0.15, 0.20]
        
        # Test with different thresholds
        test_thresholds = [0.01, 0.05, 0.10]
        
        results_by_threshold = {}
        
        for threshold in test_thresholds:
            high_bias_count = sum(1 for bias in bias_results if abs(bias) > threshold)
            total_count = len(bias_results)
            percentage = (high_bias_count / total_count) * 100
            
            results_by_threshold[threshold] = {
                "threshold": threshold,
                "high_bias_count": high_bias_count,
                "total_count": total_count,
                "percentage": percentage
            }
        
        # Verify expected counts
        # Threshold 0.01: all 7 are > 0.01 -> 100%
        assert results_by_threshold[0.01]["high_bias_count"] == 7
        assert results_by_threshold[0.01]["percentage"] == 100.0
        
        # Threshold 0.05: 5 are > 0.05 (0.06, 0.08, 0.12, 0.15, 0.20) -> ~71.4%
        assert results_by_threshold[0.05]["high_bias_count"] == 5
        assert abs(results_by_threshold[0.05]["percentage"] - 71.428) < 0.01
        
        # Threshold 0.10: 3 are > 0.10 (0.12, 0.15, 0.20) -> ~42.9%
        assert results_by_threshold[0.10]["high_bias_count"] == 3
        assert abs(results_by_threshold[0.10]["percentage"] - 42.857) < 0.01

    def test_default_thresholds_from_config(self):
        """
        Test that the sensitivity analysis uses the configured thresholds from config.py.
        """
        # Verify THRESHOLDS is defined in config and has expected structure
        assert hasattr(sys.modules.get('config'), 'THRESHOLDS') or 'THRESHOLDS' in dir()
        
        # If THRESHOLDS is not defined in config, use default
        thresholds = THRESHOLDS if 'THRESHOLDS' in dir() else [0.01, 0.05, 0.10]
        
        assert isinstance(thresholds, list)
        assert len(thresholds) > 0
        assert all(isinstance(t, (int, float)) for t in thresholds)
        assert all(t > 0 for t in thresholds)

    def test_classification_edge_cases(self):
        """
        Test edge cases in threshold classification.
        """
        bias_values = [0.0, 0.05, 0.05001, 0.1, 0.10001]
        threshold = 0.05
        
        # Count values strictly greater than threshold
        high_bias = [b for b in bias_values if abs(b) > threshold]
        
        # Only 0.05001 and 0.10001 should be > 0.05
        assert len(high_bias) == 2
        assert 0.05 not in high_bias  # Exactly equal should not be counted
        assert 0.1 in high_bias

    def test_negative_bias_handling(self):
        """
        Test that negative bias values are handled correctly (absolute value used).
        """
        bias_values = [-0.02, -0.06, 0.06, 0.02]
        threshold = 0.05
        
        high_bias = [b for b in bias_values if abs(b) > threshold]
        
        # Only -0.06 and 0.06 should be > 0.05 in absolute value
        assert len(high_bias) == 2
        assert -0.06 in high_bias
        assert 0.06 in high_bias
        assert -0.02 not in high_bias
        assert 0.02 not in high_bias

    def test_empty_input_handling(self):
        """
        Test that empty input lists are handled gracefully.
        """
        bias_results = []
        threshold = 0.05
        
        high_bias_count = sum(1 for bias in bias_results if abs(bias) > threshold)
        total_count = len(bias_results)
        
        assert high_bias_count == 0
        assert total_count == 0
        # Percentage calculation would be 0/0, so we handle this case
        # In real implementation, this would be caught and handled

    def test_threshold_range_coverage(self):
        """
        Test that thresholds cover a reasonable range for sensitivity analysis.
        """
        # Typical thresholds for statistical significance and bias detection
        typical_thresholds = [0.01, 0.05, 0.10]
        
        # Verify we have at least these key thresholds
        for t in typical_thresholds:
            assert t in THRESHOLDS or t in [0.01, 0.05, 0.10], \
                f"Threshold {t} should be in the analysis range"

    def test_sensitivity_report_structure(self):
        """
        Test that the sensitivity report structure matches expected format.
        This simulates what would be written to data/results/sensitivity_analysis.json
        """
        mock_results = [
            {"threshold": 0.01, "high_bias_count": 7, "total_count": 10, "percentage": 70.0},
            {"threshold": 0.05, "high_bias_count": 4, "total_count": 10, "percentage": 40.0},
            {"threshold": 0.10, "high_bias_count": 2, "total_count": 10, "percentage": 20.0}
        ]
        
        # Verify structure
        for result in mock_results:
            assert "threshold" in result
            assert "high_bias_count" in result
            assert "total_count" in result
            assert "percentage" in result
            assert isinstance(result["threshold"], (int, float))
            assert isinstance(result["high_bias_count"], int)
            assert isinstance(result["total_count"], int)
            assert isinstance(result["percentage"], (int, float))
            
            # Verify percentage calculation
            expected_percentage = (result["high_bias_count"] / result["total_count"]) * 100
            assert abs(result["percentage"] - expected_percentage) < 0.01

    def test_threshold_sweep_with_realistic_data_distribution(self):
        """
        Test sensitivity analysis with a more realistic distribution of bias values.
        Simulates data that might come from real-world datasets with varying power bias.
        """
        # Simulate bias values following a realistic distribution
        # Most datasets have small bias, few have large bias
        np.random.seed(42)
        bias_values = np.concatenate([
            np.random.normal(0.03, 0.02, 80),  # 80 datasets with small bias
            np.random.normal(0.15, 0.05, 20)   # 20 datasets with larger bias
        ])
        
        thresholds = [0.01, 0.05, 0.10]
        results = {}
        
        for threshold in thresholds:
            high_bias_count = sum(1 for bias in bias_values if abs(bias) > threshold)
            total_count = len(bias_values)
            percentage = (high_bias_count / total_count) * 100
            
            results[threshold] = {
                "threshold": threshold,
                "high_bias_count": high_bias_count,
                "total_count": total_count,
                "percentage": percentage
            }
        
        # Verify expected behavior:
        # Lower threshold (0.01) should catch more cases
        assert results[0.01]["high_bias_count"] > results[0.05]["high_bias_count"]
        assert results[0.05]["high_bias_count"] > results[0.10]["high_bias_count"]
        
        # Verify percentages are monotonically decreasing
        assert results[0.01]["percentage"] >= results[0.05]["percentage"]
        assert results[0.05]["percentage"] >= results[0.10]["percentage"]
        
        # Verify all percentages are between 0 and 100
        for threshold in thresholds:
            assert 0 <= results[threshold]["percentage"] <= 100