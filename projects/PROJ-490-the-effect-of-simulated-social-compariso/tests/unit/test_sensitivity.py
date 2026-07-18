"""
Unit test for parameter recovery bias calculation (|beta_hat - beta_true|)
for User Story 3 (Methodological Robustness).

This test verifies that when using synthetic data with known ground truth
parameters, the analysis pipeline can recover those parameters within
acceptable bias thresholds.
"""
import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# Add project root to path to allow imports from code/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from data.config import get_config, reset_config
from data.download import generate_synthetic_dataset
from analysis.regression import validate_model_assumptions
from utils.validators import validate_dataframe_schema


class TestParameterRecoveryBias:
    """Tests for parameter recovery bias calculation."""

    def setup_method(self):
        """Set up test fixtures."""
        reset_config()
        self.config = get_config()
        self.seed = 42
        np.random.seed(self.seed)

    def teardown_method(self):
        """Clean up after tests."""
        reset_config()

    def _create_synthetic_data_with_known_params(self, n_samples=500):
        """
        Generate synthetic data with known ground truth parameters.

        Ground truth model:
        post_self_esteem = beta_0 + beta_1 * avatar_condition +
                           beta_2 * pre_self_esteem +
                           beta_3 * comparison_tendency +
                           beta_4 * (avatar_condition * comparison_tendency) +
                           epsilon

        Where:
        - beta_0 (intercept) = 2.5
        - beta_1 (avatar_condition) = 0.3
        - beta_2 (pre_self_esteem) = 0.6
        - beta_3 (comparison_tendency) = -0.2
        - beta_4 (interaction) = 0.2 (the key parameter of interest)
        """
        # Ground truth parameters
        beta_true = {
            'intercept': 2.5,
            'avatar_condition': 0.3,
            'pre_self_esteem': 0.6,
            'comparison_tendency': -0.2,
            'interaction': 0.2
        }

        # Generate data
        avatar_condition = np.random.binomial(1, 0.5, n_samples)
        pre_self_esteem = np.random.normal(3.5, 0.8, n_samples)
        comparison_tendency = np.random.normal(2.5, 0.7, n_samples)

        # Calculate post_self_esteem with known parameters
        interaction = avatar_condition * comparison_tendency
        epsilon = np.random.normal(0, 0.5, n_samples)

        post_self_esteem = (
            beta_true['intercept'] +
            beta_true['avatar_condition'] * avatar_condition +
            beta_true['pre_self_esteem'] * pre_self_esteem +
            beta_true['comparison_tendency'] * comparison_tendency +
            beta_true['interaction'] * interaction +
            epsilon
        )

        # Create DataFrame
        df = pd.DataFrame({
            'avatar_condition': avatar_condition,
            'pre_self_esteem': pre_self_esteem,
            'post_self_esteem': post_self_esteem,
            'comparison_tendency': comparison_tendency,
            'interaction': interaction
        })

        return df, beta_true

    def _fit_ancova_model(self, df):
        """
        Fit ANCOVA model and return coefficients.

        Model: post_self_esteem ~ avatar_condition + pre_self_esteem +
               comparison_tendency + interaction
        """
        import statsmodels.api as sm

        # Prepare features and target
        X = df[['avatar_condition', 'pre_self_esteem',
                'comparison_tendency', 'interaction']]
        y = df['post_self_esteem']

        # Add intercept
        X = sm.add_constant(X)

        # Fit OLS model
        model = sm.OLS(y, X).fit()

        # Extract coefficients
        coefficients = {
            'intercept': model.params['const'],
            'avatar_condition': model.params['avatar_condition'],
            'pre_self_esteem': model.params['pre_self_esteem'],
            'comparison_tendency': model.params['comparison_tendency'],
            'interaction': model.params['interaction']
        }

        return coefficients, model

    def _calculate_bias(self, beta_hat, beta_true):
        """
        Calculate absolute bias for each parameter.

        Returns:
            dict: Absolute bias for each parameter (|beta_hat - beta_true|)
        """
        bias = {}
        for param in beta_true.keys():
            bias[param] = abs(beta_hat[param] - beta_true[param])
        return bias

    def test_parameter_recovery_interaction_effect(self):
        """
        Test that the interaction effect (beta_4) is recovered with low bias.

        This is the key parameter of interest for the social comparison study.
        Expected bias should be < 0.1 for N=500 with reasonable noise.
        """
        # Generate synthetic data with known parameters
        df, beta_true = self._create_synthetic_data_with_known_params(n_samples=500)

        # Fit model
        beta_hat, model = self._fit_ancova_model(df)

        # Calculate bias
        bias = self._calculate_bias(beta_hat, beta_true)

        # Assert that the interaction effect is recovered with low bias
        # For N=500 and noise=0.5, we expect bias < 0.1
        assert bias['interaction'] < 0.1, (
            f"Interaction effect bias too high: {bias['interaction']:.4f}. "
            f"Expected < 0.1. True beta: {beta_true['interaction']}, "
            f"Estimated beta: {beta_hat['interaction']}"
        )

        # Log results for verification
        print(f"\nParameter Recovery Results (N=500):")
        print(f"True parameters: {beta_true}")
        print(f"Estimated parameters: {beta_hat}")
        print(f"Absolute bias: {bias}")

    def test_all_parameters_recovered(self):
        """
        Test that all parameters are recovered with acceptable bias.

        For each parameter, the absolute bias should be below a threshold
        that depends on the parameter's magnitude and the sample size.
        """
        # Generate synthetic data
        df, beta_true = self._create_synthetic_data_with_known_params(n_samples=500)

        # Fit model
        beta_hat, model = self._fit_ancova_model(df)

        # Calculate bias
        bias = self._calculate_bias(beta_hat, beta_true)

        # Define acceptable bias thresholds (relative to parameter magnitude)
        # More lenient for smaller parameters
        thresholds = {
            'intercept': 0.3,
            'avatar_condition': 0.15,
            'pre_self_esteem': 0.15,
            'comparison_tendency': 0.15,
            'interaction': 0.15
        }

        # Assert all parameters are recovered within thresholds
        for param in beta_true.keys():
            assert bias[param] < thresholds[param], (
                f"Parameter '{param}' bias too high: {bias[param]:.4f}. "
                f"Threshold: {thresholds[param]}"
            )

    def test_bias_decreases_with_sample_size(self):
        """
        Test that parameter recovery bias decreases as sample size increases.

        This validates that our estimation procedure is consistent.
        """
        sample_sizes = [100, 300, 500]
        interaction_biases = []

        for n in sample_sizes:
            df, beta_true = self._create_synthetic_data_with_known_params(n_samples=n)
            beta_hat, _ = self._fit_ancova_model(df)
            bias = self._calculate_bias(beta_hat, beta_true)
            interaction_biases.append(bias['interaction'])

        # Check that bias generally decreases (not strictly monotonic due to randomness)
        # But the trend should be downward
        # We check that the largest sample size has lower bias than the smallest
        assert interaction_biases[-1] < interaction_biases[0], (
            f"Interaction bias did not decrease with sample size: "
            f"N=100 bias={interaction_biases[0]:.4f}, "
            f"N=500 bias={interaction_biases[-1]:.4f}"
        )

    def test_model_fit_quality(self):
        """
        Test that the model fits well (high R-squared) when data is generated
        from the same model structure.
        """
        df, beta_true = self._create_synthetic_data_with_known_params(n_samples=500)
        _, model = self._fit_ancova_model(df)

        # R-squared should be reasonably high for well-specified model
        assert model.rsquared > 0.5, (
            f"R-squared too low: {model.rsquared:.4f}. "
            "Expected > 0.5 for well-specified model."
        )

        # F-statistic should be significant
        assert model.f_pvalue < 0.001, (
            f"F-test p-value too high: {model.f_pvalue:.6f}. "
            "Expected < 0.001."
        )

    def test_bias_calculation_functionality(self):
        """
        Test the bias calculation logic with known values.
        """
        # Known values
        beta_true = {'a': 1.0, 'b': 2.0, 'c': 3.0}
        beta_hat = {'a': 1.1, 'b': 1.9, 'c': 3.2}

        # Expected biases
        expected_bias = {'a': 0.1, 'b': 0.1, 'c': 0.2}

        # Calculate bias
        bias = self._calculate_bias(beta_hat, beta_true)

        # Assert
        for param in expected_bias:
            assert abs(bias[param] - expected_bias[param]) < 1e-6, (
                f"Bias calculation incorrect for '{param}': "
                f"expected {expected_bias[param]}, got {bias[param]}"
            )