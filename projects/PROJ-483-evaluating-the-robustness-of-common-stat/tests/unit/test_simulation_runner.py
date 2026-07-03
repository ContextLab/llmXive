"""
Unit tests for simulation runner logic.
"""
import numpy as np
import pytest
import sys
import os
from scipy import stats

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

# Import the dependency injector to verify the null hypothesis construction
# We use ar1_inject with r=0 to simulate the true null condition
from dependency_injector import ar1_inject

def test_null_hypothesis_uniformity():
    """
    Test that p-values are uniform under true null (r=0).
    
    This test verifies the "Generate-then-Inject" paradigm for the null hypothesis:
    1. Generate data from Normal(0, 1) (True Null)
    2. Inject AR(1) dependency with r=0 (no dependency)
    3. Perform independent t-test
    4. Verify p-values follow Uniform(0, 1) distribution via Kolmogorov-Smirnov test
    """
    np.random.seed(42)  # Reproducibility
    
    n_replications = 5000
    n_per_group = 100
    alpha = 0.05
    
    p_values = []
    
    for _ in range(n_replications):
        # Step 1: Generate synthetic data under true null (Normal(0,1))
        group_a = np.random.normal(loc=0.0, scale=1.0, size=n_per_group)
        group_b = np.random.normal(loc=0.0, scale=1.0, size=n_per_group)
        
        # Step 2: Inject dependency with r=0 (should be identity/no-op)
        # We reshape to 2D for the injector (n_samples, n_features) logic if needed, 
        # but for simple 1D groups, we treat them as single series or apply to concatenated.
        # For t-test independence check, we inject on each group separately.
        injected_a = ar1_inject(group_a.reshape(-1, 1), r=0.0).flatten()
        injected_b = ar1_inject(group_b.reshape(-1, 1), r=0.0).flatten()
        
        # Step 3: Apply independent two-sample t-test
        # Since r=0, data remains independent and identically distributed
        t_stat, p_val = stats.ttest_ind(injected_a, injected_b)
        p_values.append(p_val)
    
    p_values = np.array(p_values)
    
    # Step 4: Verify uniformity using Kolmogorov-Smirnov test against Uniform(0,1)
    # The null hypothesis of KS test is that the sample comes from the specified distribution.
    # We expect a high p-value (fail to reject) if the p-values are uniform.
    ks_stat, ks_p_value = stats.kstest(p_values, 'uniform')
    
    # Assert that the p-values from KS test are significant (i.e., we cannot reject uniformity)
    # Typically we require p > 0.05 for the KS test to confirm uniformity
    assert ks_p_value > 0.05, (
        f"p-values are not uniform under r=0. KS p-value: {ks_p_value:.4f}, "
        f"KS statistic: {ks_stat:.4f}. This suggests the null hypothesis construction is flawed."
    )
    
    # Additional check: Type I error rate should be close to alpha (0.05)
    observed_error_rate = np.mean(p_values < alpha)
    expected_error_rate = alpha
    tolerance = 0.01  # Allow 1% deviation due to sampling noise
    
    assert abs(observed_error_rate - expected_error_rate) < tolerance, (
        f"Observed Type I error rate ({observed_error_rate:.4f}) deviates "
        f"too much from expected ({expected_error_rate}) under true null."
    )
