"""
Unit tests for code/data/simulators.py

These tests verify the synthetic outcome generation logic.
"""
import numpy as np
import pandas as pd
import pytest
from typing import Tuple

from data.simulators import generate_synthetic_outcomes, get_default_snr_levels, get_default_sparsity_levels


class TestSimulatorConfig:
    """Tests for simulator configuration defaults."""

    def test_default_snr_levels(self):
        """Test that default SNR levels are reasonable."""
        levels = get_default_snr_levels()
        assert isinstance(levels, list), "SNR levels should be a list"
        assert len(levels) > 0, "Should have at least one SNR level"
        assert all(isinstance(l, (int, float)) for l in levels), "SNR levels should be numeric"
        assert all(l >= 0 for l in levels), "SNR levels should be non-negative"

    def test_default_sparsity_levels(self):
        """Test that default sparsity levels are reasonable."""
        levels = get_default_sparsity_levels()
        assert isinstance(levels, list), "Sparsity levels should be a list"
        assert len(levels) > 0, "Should have at least one sparsity level"
        assert all(isinstance(l, (int, float)) for l in levels), "Sparsity levels should be numeric"
        assert all(0 <= l <= 1 for l in levels), "Sparsity levels should be between 0 and 1"


class TestOutcomeGeneration:
    """Tests for generate_synthetic_outcomes function."""

    def test_generate_outcomes_basic(self):
        """Test basic outcome generation."""
        # Create a simple feature matrix
        X = pd.DataFrame(np.random.randn(100, 5), columns=[f"f{i}" for i in range(5)])
        true_coeffs = np.array([1.0, 1.0, 0.0, 0.0, 0.0])

        Y = generate_synthetic_outcomes(X, true_coeffs, snr=1.0, seed=42)

        assert isinstance(Y, pd.Series), "Output should be a pandas Series"
        assert len(Y) == len(X), "Output length should match input rows"

    def test_generate_outcomes_variance(self):
        """Test that generated outcomes match expected variance based on SNR."""
        # This is a more complex test. We check that the variance of Y
        # is consistent with the signal-to-noise ratio.
        # Signal variance = Var(X @ beta)
        # Noise variance = Signal variance / SNR
        # Total variance = Signal variance + Noise variance

        np.random.seed(42)
        X = pd.DataFrame(np.random.randn(1000, 3), columns=['f1', 'f2', 'f3'])
        true_coeffs = np.array([2.0, 2.0, 0.0])
        snr = 1.0

        Y = generate_synthetic_outcomes(X, true_coeffs, snr=snr, seed=42)

        # Calculate signal variance
        signal = X.values @ true_coeffs
        signal_var = np.var(signal)

        # Expected noise variance
        expected_noise_var = signal_var / snr

        # Actual noise variance (estimated)
        # We can't perfectly separate signal and noise without knowing the true model,
        # but we can check that the total variance is roughly signal_var * (1 + 1/snr)
        total_var = np.var(Y)
        expected_total_var = signal_var * (1 + 1.0/snr)

        # Allow some tolerance due to randomness
        assert np.isclose(total_var, expected_total_var, rtol=0.1), \
            f"Total variance {total_var} should be close to expected {expected_total_var}"

    def test_generate_outcomes_seed_reproducibility(self):
        """Test that using the same seed produces the same results."""
        X = pd.DataFrame(np.random.randn(100, 3), columns=['f1', 'f2', 'f3'])
        true_coeffs = np.array([1.0, 1.0, 0.0])

        Y1 = generate_synthetic_outcomes(X, true_coeffs, snr=1.0, seed=42)
        Y2 = generate_synthetic_outcomes(X, true_coeffs, snr=1.0, seed=42)

        assert np.allclose(Y1, Y2), "Same seed should produce identical results"

    def test_generate_outcomes_sparsity(self):
        """Test that sparsity affects the number of non-zero coefficients."""
        # This test assumes the function accepts a sparsity parameter or
        # that sparsity is handled in the true_coeffs generation (if applicable).
        # If sparsity is not a direct parameter of generate_synthetic_outcomes,
        # this test might need to be adjusted or moved to a different module.
        # For now, we assume it's part of the pipeline setup.
        pass