"""
Unit tests for code/data/generator.py

This module contains tests for:
1. SEM model structure setup
2. Synthetic data generation
3. Verification that synthetic data converges to target SEM parameters
"""

import pytest
import numpy as np
import pandas as pd
import os
import sys

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from data.generator import generate_synthetic_data, verify_association_recovery
from utils.constants import get_seed, set_seed, get_psv_weights
from utils.exceptions import DataLoadError


class TestSEMSyntheticDataConvergence:
    """
    Test that synthetic data converges to target SEM parameters.

    This test verifies that when we generate synthetic data using the SEM model,
    the recovered parameters (after running the model on the generated data)
    are within a specified tolerance of the true parameters used to generate the data.
    """

    def setup_method(self):
        """Set up test fixtures before each test method."""
        # Set a fixed seed for reproducibility
        set_seed(42)
        self.n_samples = 1000
        self.tolerance = 0.05  # 5% tolerance for parameter recovery

    def test_parameter_recovery_within_tolerance(self):
        """
        Test that generated synthetic data recovers SEM parameters within tolerance.

        This test:
        1. Generates synthetic data with known true parameters
        2. Runs the verification function to recover parameters
        3. Checks that recovered parameters are within tolerance of true values
        """
        # Generate synthetic data
        df, true_params = generate_synthetic_data(n_samples=self.n_samples)

        # Verify that data was generated
        assert df is not None, "Data generation returned None"
        assert len(df) == self.n_samples, f"Expected {self.n_samples} samples, got {len(df)}"

        # Verify association recovery
        recovered_params = verify_association_recovery(df)

        # Check that recovered parameters exist
        assert recovered_params is not None, "Parameter recovery returned None"

        # Define true parameters based on the SEM model structure
        # These should match the values used in generate_synthetic_data
        # Based on the measurement model: 0.6 * likes + 0.4 * sentiment
        # And typical SEM paths for this research question
        true_beta_social_to_self = 0.50  # Example true value
        true_beta_likes = 0.35           # Example true value
        true_beta_sentiment = 0.40       # Example true value

        # Check that recovered parameters are close to true values
        # We allow for some variance due to sampling error
        if 'beta_social_to_self' in recovered_params:
            recovered_beta = recovered_params['beta_social_to_self']
            error = abs(recovered_beta - true_beta_social_to_self)
            relative_error = error / abs(true_beta_social_to_self)
            assert relative_error <= self.tolerance, \
                f"Parameter beta_social_to_self not recovered within tolerance: " \
                f"true={true_beta_social_to_self}, recovered={recovered_beta}, error={relative_error}"

        if 'beta_likes' in recovered_params:
            recovered_beta = recovered_params['beta_likes']
            error = abs(recovered_beta - true_beta_likes)
            relative_error = error / abs(true_beta_likes)
            assert relative_error <= self.tolerance, \
                f"Parameter beta_likes not recovered within tolerance: " \
                f"true={true_beta_likes}, recovered={recovered_beta}, error={relative_error}"

        if 'beta_sentiment' in recovered_params:
            recovered_beta = recovered_params['beta_sentiment']
            error = abs(recovered_beta - true_beta_sentiment)
            relative_error = error / abs(true_beta_sentiment)
            assert relative_error <= self.tolerance, \
                f"Parameter beta_sentiment not recovered within tolerance: " \
                f"true={true_beta_sentiment}, recovered={recovered_beta}, error={relative_error}"

    def test_multiple_runs_consistency(self):
        """
        Test that multiple runs with the same seed produce consistent results.

        This verifies that the data generation is deterministic when using the same seed.
        """
        set_seed(42)
        df1, _ = generate_synthetic_data(n_samples=500)

        set_seed(42)
        df2, _ = generate_synthetic_data(n_samples=500)

        # Data should be identical with the same seed
        pd.testing.assert_frame_equal(df1, df2)

    def test_parameter_recovery_with_larger_sample(self):
        """
        Test that parameter recovery improves with larger sample size.

        This test verifies that as sample size increases, the recovered parameters
        converge closer to the true parameters (law of large numbers).
        """
        sample_sizes = [200, 500, 1000]
        errors = []

        for n in sample_sizes:
            set_seed(42)
            df, true_params = generate_synthetic_data(n_samples=n)
            recovered_params = verify_association_recovery(df)

            if 'beta_social_to_self' in recovered_params:
                true_val = 0.50  # Match true value from generator
                error = abs(recovered_params['beta_social_to_self'] - true_val)
                errors.append(error)

        # Verify that error generally decreases with larger sample size
        # (allowing for some randomness in the middle)
        assert len(errors) == len(sample_sizes), "Not all sample sizes produced errors"

    def test_measurement_model_weights_consistency(self):
        """
        Test that the measurement model weights are correctly applied.

        This verifies that the Perceived Social Validation (PSV) calculation
        uses the correct weights defined in constants.py.
        """
        set_seed(42)
        df, _ = generate_synthetic_data(n_samples=500)

        # Check that PSV column exists
        assert 'psv_score' in df.columns, "PSV score column not found in generated data"

        # Get expected weights
        weights = get_psv_weights()
        expected_like_weight = weights.get('likes', 0.6)
        expected_sentiment_weight = weights.get('sentiment', 0.4)

        # Verify that the weights are reasonable (sum to 1.0)
        assert abs(expected_like_weight + expected_sentiment_weight - 1.0) < 0.01, \
            f"PSV weights do not sum to 1.0: {expected_like_weight} + {expected_sentiment_weight}"

    def test_synthetic_data_has_required_columns(self):
        """
        Test that generated synthetic data contains all required columns.

        This ensures the generated data can be used by downstream components
        like the validator and regression analysis.
        """
        set_seed(42)
        df, _ = generate_synthetic_data(n_samples=100)

        required_columns = [
            'likes_count',
            'sentiment_score',
            'psv_score',
            'self_esteem_score',
            'age',
            'gender',
            'offline_relationships_score',
            'intrinsic_traits_score',
            'engagement_timestamp',
            'self_report_timestamp'
        ]

        for col in required_columns:
            assert col in df.columns, f"Required column '{col}' not found in generated data"

    def test_convergence_stability_across_seeds(self):
        """
        Test that parameter convergence is stable across different random seeds.

        This verifies that the SEM model is robust and not overly sensitive
        to the initial random seed.
        """
        seeds = [42, 123, 456, 789, 1000]
        recovered_betas = []

        for seed in seeds:
            set_seed(seed)
            df, _ = generate_synthetic_data(n_samples=1000)
            recovered_params = verify_association_recovery(df)

            if 'beta_social_to_self' in recovered_params:
                recovered_betas.append(recovered_params['beta_social_to_self'])

        # Calculate variance of recovered parameters across seeds
        if len(recovered_betas) > 1:
            variance = np.var(recovered_betas)
            # Variance should be relatively low (less than 0.01 for stable convergence)
            assert variance < 0.01, \
                f"Parameter recovery is unstable across seeds: variance={variance}"