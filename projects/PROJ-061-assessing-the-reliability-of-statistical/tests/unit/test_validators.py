"""
Unit tests for code/validators.py
"""
import numpy as np
import pytest

from validators import (
    bootstrap_validity_check,
    verify_achieved_magnitude,
    should_exclude_dataset,
    run_full_validation
)


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