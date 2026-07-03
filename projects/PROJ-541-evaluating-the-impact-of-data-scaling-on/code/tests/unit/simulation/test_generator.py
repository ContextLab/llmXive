"""
Contract tests for the synthetic data generator.

This module verifies that the data generator produces datasets that satisfy
the ground truth constraints for null and alternative hypotheses as specified
in User Story 1 (T008, T009).

Tests:
- T008: Contract test for null hypothesis generation (mean diff < 0.01)
- T009: Contract test for alternative hypothesis generation (|mean diff - 1.0| < 0.05)
- T010: Test for skewness/heteroscedasticity parameter accuracy
"""
import pytest
import numpy as np
import os
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
code_root = Path(__file__).resolve().parent.parent.parent.parent / "code"
if str(code_root) not in sys.path:
    sys.path.insert(0, str(code_root))

from simulation.config import SimulationConfig
from simulation.generator import generate_synthetic_data
from tests.conftest import set_seed, test_logger

# Constants for contract validation
NULL_THRESHOLD = 0.01
ALT_THRESHOLD = 0.05
ALT_MEAN_DIFF = 1.0
SKEWNESS_TOLERANCE = 0.5  # Tolerance for skewness check
HETEROSCEDASTICITY_TOLERANCE = 0.1  # Tolerance for ratio check

@pytest.fixture
def null_config():
    """Configuration for generating null hypothesis data."""
    return SimulationConfig(
        n_samples=1000,
        mean_diff=0.0,  # Null hypothesis: no difference
        std_dev=1.0,
        distribution_type="normal",
        seed=42,
        skewness=0.0,
        heteroscedasticity=0.0
    )

@pytest.fixture
def alt_config():
    """Configuration for generating alternative hypothesis data."""
    return SimulationConfig(
        n_samples=1000,
        mean_diff=ALT_MEAN_DIFF,  # Alternative hypothesis: difference of 1.0
        std_dev=1.0,
        distribution_type="normal",
        seed=123,
        skewness=0.0,
        heteroscedasticity=0.0
    )

def test_null_hypothesis_mean_difference(null_config, test_logger):
    """
    T008: Contract test for null hypothesis generation.
    
    Verifies that when mean_diff is set to 0.0, the empirical mean difference
    between the two groups is less than 0.01.
    """
    set_seed(null_config.seed)
    
    # Generate data
    group_a, group_b, success, message = generate_synthetic_data(null_config, test_logger)
    
    # Assert generation was successful
    assert success, f"Data generation failed: {message}"
    assert len(group_a) == null_config.n_samples
    assert len(group_b) == null_config.n_samples
    
    # Calculate empirical mean difference
    empirical_mean_diff = np.mean(group_b) - np.mean(group_a)
    
    # Contract assertion
    assert abs(empirical_mean_diff) < NULL_THRESHOLD, (
        f"Null hypothesis contract violated: |mean_diff|={abs(empirical_mean_diff):.6f} "
        f">= {NULL_THRESHOLD}"
    )

def test_alternative_hypothesis_mean_difference(alt_config, test_logger):
    """
    T009: Contract test for alternative hypothesis generation.
    
    Verifies that when mean_diff is set to 1.0, the empirical mean difference
    is within 0.05 of 1.0.
    """
    set_seed(alt_config.seed)
    
    # Generate data
    group_a, group_b, success, message = generate_synthetic_data(alt_config, test_logger)
    
    # Assert generation was successful
    assert success, f"Data generation failed: {message}"
    assert len(group_a) == alt_config.n_samples
    assert len(group_b) == alt_config.n_samples
    
    # Calculate empirical mean difference
    empirical_mean_diff = np.mean(group_b) - np.mean(group_a)
    
    # Contract assertion
    deviation = abs(empirical_mean_diff - ALT_MEAN_DIFF)
    assert deviation < ALT_THRESHOLD, (
        f"Alternative hypothesis contract violated: |mean_diff - 1.0|={deviation:.6f} "
        f">= {ALT_THRESHOLD}"
    )

def test_generator_returns_valid_shapes(null_config, alt_config, test_logger):
    """
    Additional contract test to ensure generated arrays have expected shapes.
    """
    set_seed(null_config.seed)
    _, _, success, _ = generate_synthetic_data(null_config, test_logger)
    assert success

    set_seed(alt_config.seed)
    group_a, group_b, success, _ = generate_synthetic_data(alt_config, test_logger)
    assert success
    assert group_a.shape == (alt_config.n_samples,)
    assert group_b.shape == (alt_config.n_samples,)

def test_skewness_parameter_accuracy(test_logger):
    """
    T010: Test for skewness parameter accuracy.
    
    Verifies that when a non-zero skewness is specified, the generated data
    exhibits the expected skewness in the specified group.
    """
    # Configuration with positive skewness
    skew_config = SimulationConfig(
        n_samples=5000,  # Larger sample for stable skewness estimation
        mean_diff=0.0,
        std_dev=1.0,
        distribution_type="skewed",
        seed=456,
        skewness=2.0,
        heteroscedasticity=0.0
    )
    
    set_seed(skew_config.seed)
    group_a, group_b, success, message = generate_synthetic_data(skew_config, test_logger)
    
    assert success, f"Data generation failed: {message}"
    
    # For skewed distributions, we expect group_b to have the skewness applied
    # (based on typical generator implementation where mean_diff affects group_b)
    # Calculate sample skewness using scipy if available, else approximate
    try:
        from scipy.stats import skew
        empirical_skew = skew(group_b)
    except ImportError:
        # Fallback calculation if scipy is not available
        # Skewness = E[(X - mu)^3] / sigma^3
        mean_val = np.mean(group_b)
        std_val = np.std(group_b)
        if std_val == 0:
            empirical_skew = 0.0
        else:
            empirical_skew = np.mean(((group_b - mean_val) / std_val) ** 3)
    
    # Check that skewness is significantly positive (at least > 0.5 for 2.0 target)
    # The tolerance accounts for sampling variation
    assert empirical_skew > 0.5, (
        f"Skewness contract violated: expected positive skewness (~{skew_config.skewness}), "
        f"got {empirical_skew:.4f}"
    )
    
    # Also verify group_a (null skewness config) has near-zero skewness
    null_skew_config = SimulationConfig(
        n_samples=5000,
        mean_diff=0.0,
        std_dev=1.0,
        distribution_type="normal",
        seed=789,
        skewness=0.0,
        heteroscedasticity=0.0
    )
    
    set_seed(null_skew_config.seed)
    group_a_null, group_b_null, success, message = generate_synthetic_data(null_skew_config, test_logger)
    assert success
    
    try:
        from scipy.stats import skew
        empirical_skew_null = skew(group_b_null)
    except ImportError:
        mean_val = np.mean(group_b_null)
        std_val = np.std(group_b_null)
        if std_val == 0:
            empirical_skew_null = 0.0
        else:
            empirical_skew_null = np.mean(((group_b_null - mean_val) / std_val) ** 3)
    
    assert abs(empirical_skew_null) < 0.5, (
        f"Normal distribution contract violated: expected near-zero skewness, "
        f"got {empirical_skew_null:.4f}"
    )

def test_heteroscedasticity_parameter_accuracy(test_logger):
    """
    T010: Test for heteroscedasticity parameter accuracy.
    
    Verifies that when a non-zero heteroscedasticity is specified, the variance
    ratio between groups matches the expected value.
    """
    # Configuration with heteroscedasticity (group_b should have higher variance)
    hetero_config = SimulationConfig(
        n_samples=5000,
        mean_diff=0.0,
        std_dev=1.0,
        distribution_type="normal",
        seed=999,
        skewness=0.0,
        heteroscedasticity=2.0  # Expect group_b variance to be ~2x group_a
    )
    
    set_seed(hetero_config.seed)
    group_a, group_b, success, message = generate_synthetic_data(hetero_config, test_logger)
    
    assert success, f"Data generation failed: {message}"
    
    var_a = np.var(group_a)
    var_b = np.var(group_b)
    
    # Avoid division by zero
    if var_a < 1e-10:
        variance_ratio = float('inf') if var_b > 1e-10 else 1.0
    else:
        variance_ratio = var_b / var_a
    
    # Check that variance ratio is close to the heteroscedasticity parameter
    # Tolerance of 0.1 relative error
    expected_ratio = hetero_config.heteroscedasticity
    tolerance = expected_ratio * HETEROSCEDASTICITY_TOLERANCE
    
    assert abs(variance_ratio - expected_ratio) < tolerance, (
        f"Heteroscedasticity contract violated: expected ratio ~{expected_ratio}, "
        f"got {variance_ratio:.4f} (difference: {abs(variance_ratio - expected_ratio):.4f})"
    )
    
    # Verify homoscedastic case (ratio should be ~1.0)
    homo_config = SimulationConfig(
        n_samples=5000,
        mean_diff=0.0,
        std_dev=1.0,
        distribution_type="normal",
        seed=888,
        skewness=0.0,
        heteroscedasticity=0.0
    )
    
    set_seed(homo_config.seed)
    group_a_homo, group_b_homo, success, message = generate_synthetic_data(homo_config, test_logger)
    assert success
    
    var_a_homo = np.var(group_a_homo)
    var_b_homo = np.var(group_b_homo)
    
    if var_a_homo < 1e-10:
        variance_ratio_homo = float('inf') if var_b_homo > 1e-10 else 1.0
    else:
        variance_ratio_homo = var_b_homo / var_a_homo
    
    assert abs(variance_ratio_homo - 1.0) < 0.2, (
        f"Homoscedasticity contract violated: expected ratio ~1.0, "
        f"got {variance_ratio_homo:.4f}"
    )