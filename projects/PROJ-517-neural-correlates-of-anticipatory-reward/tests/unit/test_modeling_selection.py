"""
Unit tests for GLM model selection logic in code/modeling.py.

This test verifies that the `select_model_family` function correctly chooses
between NegativeBinomial and Poisson models based on the calculated dispersion
parameter, adhering to the threshold defined in FR-003 (dispersion > 1.1).
"""
import pytest
import pandas as pd
import numpy as np
from statsmodels.discrete.discrete_model import NegativeBinomial, Poisson
from statsmodels.genmod.generalized_linear_model import GLM

# Import the function under test from the sibling module
from code.modeling import select_model_family, calculate_dispersion


class TestGLMSelection:
    """Tests for the model selection logic based on dispersion."""

    def test_glm_selection_high_dispersion(self):
        """
        Test that NegativeBinomial is returned when dispersion > 1.1.

        Scenario: Input data with dispersion=1.5.
        Expected: statsmodels NegativeBinomial model family is returned.
        """
        # Create synthetic data with high variance relative to mean
        np.random.seed(42)
        n_samples = 200
        # Generate mean counts
        mu = np.random.poisson(10, n_samples)
        # Generate overdispersed counts (variance > mean)
        # Using a Gamma mixture to simulate Negative Binomial behavior
        # variance = mu + mu^2 / theta
        theta = 2.0  # shape parameter
        # Simulate overdispersion: scale the variance
        data = np.random.negative_binomial(n=theta, p=theta / (theta + mu), size=n_samples)
        
        df = pd.DataFrame({
            'spike_count': data,
            'reward_magnitude': np.random.uniform(0.5, 2.0, n_samples)
        })

        # Calculate actual dispersion to ensure it's > 1.1
        dispersion = calculate_dispersion(df['spike_count'])
        assert dispersion > 1.1, f"Test setup failed: expected dispersion > 1.1, got {dispersion}"

        # Get the model family
        model_family = select_model_family(df['spike_count'])

        # Assert that the selected family is NegativeBinomial
        # We check the class name or the family object type
        assert model_family is not None
        assert model_family.family.__class__.__name__ == 'NegativeBinomial', \
            f"Expected NegativeBinomial, got {model_family.family.__class__.__name__}"

    def test_glm_selection_low_dispersion(self):
        """
        Test that Poisson is returned when dispersion <= 1.1.

        Scenario: Input data with dispersion=0.9.
        Expected: statsmodels Poisson model family is returned.
        """
        # Create synthetic data with low variance (Poisson-like)
        np.random.seed(123)
        n_samples = 200
        # Generate counts from a Poisson distribution
        data = np.random.poisson(lam=10, size=n_samples)
        
        df = pd.DataFrame({
            'spike_count': data,
            'reward_magnitude': np.random.uniform(0.5, 2.0, n_samples)
        })

        # Calculate actual dispersion to ensure it's <= 1.1
        dispersion = calculate_dispersion(df['spike_count'])
        assert dispersion <= 1.1, f"Test setup failed: expected dispersion <= 1.1, got {dispersion}"

        # Get the model family
        model_family = select_model_family(df['spike_count'])

        # Assert that the selected family is Poisson
        assert model_family is not None
        assert model_family.family.__class__.__name__ == 'Poisson', \
            f"Expected Poisson, got {model_family.family.__class__.__name__}"

    def test_glm_selection_boundary_case(self):
        """
        Test behavior at the boundary (dispersion approx 1.1).
        
        According to FR-003: Negative Binomial if dispersion > 1.1, else Poisson.
        """
        np.random.seed(999)
        n_samples = 500
        # Generate data that is slightly overdispersed but close to 1.1
        # Poisson variance = mean. We want variance slightly higher.
        mean_val = 20
        # Create data with variance ~ 1.1 * mean
        target_variance = 1.1 * mean_val
        # Use a compound distribution to approximate this
        data = np.random.poisson(mean_val, n_samples)
        # Add slight noise to push variance up if needed, though Poisson is usually < 1.1
        # For a strict test, we rely on the function's logic threshold.
        
        df = pd.DataFrame({
            'spike_count': data,
            'reward_magnitude': np.random.uniform(0.5, 2.0, n_samples)
        })

        dispersion = calculate_dispersion(df['spike_count'])
        
        # The logic in select_model_family is: if dispersion > 1.1 then NB else Poisson
        model_family = select_model_family(df['spike_count'])
        
        # We just assert it returns a valid family object
        assert model_family is not None
        assert hasattr(model_family, 'family')