"""Unit tests for power analysis functionality."""
import pytest
import numpy as np
from scipy.stats import f

# Import the module under test
try:
    from code.modeling.power_analysis import calculate_power_f_test, run_power_analysis
except ImportError:
    # Adjust path for test execution context
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from code.modeling.power_analysis import calculate_power_f_test, run_power_analysis


def test_calculate_power_f_test_basic():
    """Test basic power calculation."""
    # Known parameters: N=100, p=50, R2=0.05, alpha=0.05
    # Expected power should be > 0.8 for a valid study
    power = calculate_power_f_test(
        n_samples=100,
        n_predictors=50,
        r_squared=0.05,
        alpha=0.05
    )
    assert 0.0 <= power <= 1.0
    # With N=100 and R2=0.05, power might be low, but it must be a valid probability
    assert isinstance(power, float)


def test_calculate_power_f_test_high_effect():
    """Test power calculation with a high effect size."""
    power = calculate_power_f_test(
        n_samples=100,
        n_predictors=10,
        r_squared=0.20,
        alpha=0.05
    )
    # High effect size should yield high power
    assert power > 0.8


def test_calculate_power_f_test_low_samples():
    """Test that low sample size raises an error."""
    with pytest.raises(ValueError):
        calculate_power_f_test(
            n_samples=5,
            n_predictors=10,
            r_squared=0.05,
            alpha=0.05
        )


def test_run_power_analysis():
    """Test the full run_power_analysis function."""
    results = run_power_analysis(
        n_samples=100,
        n_predictors=50,
        expected_r_squared=0.05,
        alpha=0.05,
        power_threshold=0.8
    )

    assert "status" in results
    assert "parameters" in results
    assert "results" in results
    assert "conclusion" in results
    assert "calculated_power" in results["results"]


def test_run_power_analysis_insufficient_power():
    """Test scenario where power is insufficient."""
    results = run_power_analysis(
        n_samples=20,  # Very small sample
        n_predictors=50,
        expected_r_squared=0.05,
        alpha=0.05,
        power_threshold=0.8
    )
    assert results["status"] == "insufficient_power"
    assert results["results"]["is_valid"] is False
