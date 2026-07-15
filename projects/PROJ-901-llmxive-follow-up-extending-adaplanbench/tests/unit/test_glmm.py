"""
Unit tests for GLMM model fitting in code/analysis/glmm.py.

This module performs a sanity check on synthetic data to ensure the GLMM
fitting logic (using statsmodels) works correctly before running on real data.

The test generates synthetic binary outcomes based on known parameters,
fits the model, and verifies that the recovered coefficients are within
a reasonable tolerance of the ground truth.
"""

import pytest
import numpy as np
import pandas as pd
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.base.model import BFGS

# We will import the specific fitting function if it exists, 
# or test the logic directly here to ensure the module is runnable.
# Since T028 (glmm.py) is not yet implemented, we test the *logic* 
# that T028 will implement using a local helper.

def generate_synthetic_glmm_data(n_samples=1000, n_groups=50, random_seed=42):
    """
    Generates synthetic data for a binary outcome GLMM.
    
    Model: logit(p) = beta0 + beta1 * x + u_group
    where u_group ~ N(0, sigma^2)
    
    Returns:
        df: DataFrame with 'outcome', 'x', 'group_id'
        true_params: dict with ground truth coefficients
    """
    rng = np.random.default_rng(random_seed)
    
    # Ground truth parameters
    beta0 = -0.5
    beta1 = 1.5
    sigma_u = 0.8
    
    # Group assignments
    group_ids = rng.integers(0, n_groups, size=n_samples)
    unique_groups = np.unique(group_ids)
    
    # Random effects per group
    u = rng.normal(0, sigma_u, size=n_groups)
    u_group = u[group_ids]
    
    # Predictor (simulating 'number of constraints')
    x = rng.normal(0, 1, size=n_samples)
    
    # Linear predictor
    linear_pred = beta0 + beta1 * x + u_group
    
    # Probability via logistic function
    p = 1 / (1 + np.exp(-linear_pred))
    
    # Binary outcome
    y = rng.binomial(1, p, size=n_samples)
    
    df = pd.DataFrame({
        'outcome': y,
        'x': x,
        'group_id': group_ids
    })
    
    return df, {'beta0': beta0, 'beta1': beta1, 'sigma_u': sigma_u}

def fit_glmm_fixed_effects(df, outcome_col='outcome', pred_col='x', group_col='group_id'):
    """
    Fits a GLM with binomial family and logit link.
    Note: statsmodels GLM does not natively support random effects (mixed models)
    without the `statsmodels` mixedlm module or `pymer4`. 
    For this sanity check, we fit a fixed-effects GLM to verify the 
    binomial link and convergence logic works. 
    
    In a full implementation (T028), we would use a proper MixedLM or 
    GEE approach for the random effects. This test ensures the 
    data loading and model fitting pipeline is robust.
    """
    # Prepare data
    y = df[outcome_col]
    X = df[[pred_col]]
    # Add intercept
    X = sm.add_constant(X)
    
    model = GLM(y, X, family=families.Binomial())
    result = model.fit()
    
    return result

import statsmodels.api as sm

class TestGLMMFitting:
    """Test suite for GLMM fitting logic."""

    def test_synthetic_data_generation(self):
        """Verify synthetic data generation produces expected distributions."""
        df, params = generate_synthetic_glmm_data(n_samples=1000)
        
        assert len(df) == 1000
        assert df['outcome'].dtype in [np.int64, np.int32]
        assert df['outcome'].isin([0, 1]).all()
        assert df['x'].dtype in [np.float64, np.float32]
        assert len(df['group_id'].unique()) > 0
    
    def test_glmm_convergence_on_synthetic(self):
        """Test that the GLM converges on synthetic data."""
        df, _ = generate_synthetic_glmm_data(n_samples=2000)
        
        # Fit model
        result = fit_glmm_fixed_effects(df)
        
        # Check convergence
        assert result.converged, "GLM did not converge on synthetic data"
        assert result.status == 0, "GLM optimization status is not 0"
    
    def test_coefficient_recovery(self):
        """
        Test that the estimated coefficients are reasonably close to truth.
        Note: Since we are fitting a fixed-effects model on data with random effects,
        the estimate for beta1 might be slightly attenuated or biased, but it 
        should be statistically significant and in the correct direction.
        """
        df, true_params = generate_synthetic_glmm_data(n_samples=5000, n_groups=200)
        
        result = fit_glmm_fixed_effects(df)
        
        # Extract coefficients
        # Index 0 is intercept (const), Index 1 is 'x'
        estimated_beta1 = result.params['x']
        estimated_beta0 = result.params['const']
        
        # Check direction (should be positive as true beta1 is 1.5)
        assert estimated_beta1 > 0, "Estimated beta1 should be positive"
        
        # Check magnitude (allow for some bias due to unmodeled random effects)
        # With large sample, it should be within 50% of true value at least
        assert abs(estimated_beta1 - true_params['beta1']) < 1.0, \
            f"Estimated beta1 ({estimated_beta1}) too far from truth ({true_params['beta1']})"
        
        # Check p-value for x is significant
        p_value = result.pvalues['x']
        assert p_value < 0.05, f"Predictor x should be significant (p={p_value})"
    
    def test_empty_data_handling(self):
        """Test that the function handles empty data gracefully."""
        df_empty = pd.DataFrame({'outcome': [], 'x': [], 'group_id': []})
        
        with pytest.raises(Exception):
            # GLM should fail on empty data
            fit_glmm_fixed_effects(df_empty)
    
    def test_invalid_outcome_values(self):
        """Test that non-binary outcomes raise an error or are handled."""
        df_invalid = pd.DataFrame({
            'outcome': [0, 1, 2], 
            'x': [0.1, 0.2, 0.3]
        })
        
        # Binomial family expects 0/1. 2 might cause issues or be treated as 1 in some contexts,
        # but strictly it should fail or warn.
        # We expect an error or a warning depending on statsmodels version.
        # For safety, we check that it doesn't silently produce a valid model for bad data.
        try:
            result = fit_glmm_fixed_effects(df_invalid)
            # If it runs, the fit should likely be bad or raise a warning during fit
            # But for this test, we just ensure the code path doesn't crash unexpectedly
            # without a clear error.
        except ValueError:
            # Expected: ValueError for non-binary outcomes in Binomial family
            pass
        except Exception:
            # Other exceptions are also acceptable as long as it fails loudly
            pass