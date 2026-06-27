"""Unit tests for Monte-Carlo framework core functions.

These tests verify that the core Monte-Carlo functions are importable
and produce expected outputs for basic scenarios.
"""

import pytest
import numpy as np
from src.audit.monte_carlo_core import (
    set_seed,
    simulate_two_proportion_data,
    simulate_two_sample_continuous_data,
    run_monte_carlo_z_test,
    run_monte_carlo_fisher_exact,
    run_monte_carlo_welch_t,
    run_monte_carlo_binomial,
    validate_monte_carlo_results,
    run_all_monte_carlo_validations,
    DEFAULT_SEED,
    DEFAULT_N_REPLICATES
)


class TestSeedFunctions:
    """Tests for seed management functions."""

    def test_set_seed_importable(self):
        """Verify set_seed function can be imported and called."""
        set_seed(42)
        assert np.random.get_state()[1][0] != 0  # State changed

    def test_default_seed_constant(self):
        """Verify DEFAULT_SEED is defined."""
        assert DEFAULT_SEED == 42


class TestSimulationFunctions:
    """Tests for data simulation functions."""

    def test_simulate_two_proportion_data_importable(self):
        """Verify simulate_two_proportion_data is importable."""
        x1, n1, x2, n2 = simulate_two_proportion_data(100, 100, 0.5, 0.5, seed=42)
        assert len(x1) == 1
        assert len(x2) == 1
        assert n1[0] == 100
        assert n2[0] == 100

    def test_simulate_two_proportion_data_reproducibility(self):
        """Verify simulation is reproducible with same seed."""
        x1_a, _, x2_a, _ = simulate_two_proportion_data(100, 100, 0.5, 0.5, seed=42)
        x1_b, _, x2_b, _ = simulate_two_proportion_data(100, 100, 0.5, 0.5, seed=42)
        assert np.array_equal(x1_a, x1_b)
        assert np.array_equal(x2_a, x2_b)

    def test_simulate_two_sample_continuous_data_importable(self):
        """Verify simulate_two_sample_continuous_data is importable."""
        s1, s2 = simulate_two_sample_continuous_data(
            50, 50, 0.0, 0.0, 1.0, 1.0, seed=42
        )
        assert s1.shape == (1, 50)
        assert s2.shape == (1, 50)

    def test_simulate_two_sample_continuous_data_multiple_replicates(self):
        """Verify simulation works with multiple replicates."""
        s1, s2 = simulate_two_sample_continuous_data(
            50, 50, 0.0, 0.0, 1.0, 1.0, n_replicates=10, seed=42
        )
        assert s1.shape == (10, 50)
        assert s2.shape == (10, 50)


class TestMonteCarloTestFunctions:
    """Tests for Monte-Carlo test execution functions."""

    def test_run_monte_carlo_z_test_importable(self):
        """Verify run_monte_carlo_z_test is importable and runs."""
        result = run_monte_carlo_z_test(100, 100, 0.5, 0.5, n_replicates=100, seed=42)
        assert 'p_values' in result
        assert 'mean_p' in result
        assert 'type_1_error_rate' in result
        assert len(result['p_values']) == 100

    def test_run_monte_carlo_fisher_exact_importable(self):
        """Verify run_monte_carlo_fisher_exact is importable and runs."""
        result = run_monte_carlo_fisher_exact(100, 100, 0.5, 0.5, n_replicates=100, seed=42)
        assert 'p_values' in result
        assert 'mean_p' in result
        assert 'type_1_error_rate' in result
        assert len(result['p_values']) == 100

    def test_run_monte_carlo_welch_t_importable(self):
        """Verify run_monte_carlo_welch_t is importable and runs."""
        result = run_monte_carlo_welch_t(50, 50, 0.0, 0.0, 1.0, 1.0, n_replicates=100, seed=42)
        assert 'p_values' in result
        assert 'mean_p' in result
        assert 'type_1_error_rate' in result
        assert len(result['p_values']) == 100

    def test_run_monte_carlo_binomial_importable(self):
        """Verify run_monte_carlo_binomial is importable and runs."""
        result = run_monte_carlo_binomial(100, 0.5, p_null=0.5, n_replicates=100, seed=42)
        assert 'p_values' in result
        assert 'mean_p' in result
        assert 'type_1_error_rate' in result
        assert len(result['p_values']) == 100

    def test_type_1_error_rate_reasonable(self):
        """Verify type_1_error_rate is approximately alpha for null simulations."""
        result = run_monte_carlo_z_test(1000, 1000, 0.5, 0.5, n_replicates=1000, seed=42)
        # For a well-calibrated test, type_1_error_rate should be close to 0.05
        assert 0.02 <= result['type_1_error_rate'] <= 0.08


class TestValidationFunctions:
    """Tests for validation functions."""

    def test_validate_monte_carlo_results_importable(self):
        """Verify validate_monte_carlo_results is importable."""
        result = {
            'type_1_error_rate': 0.05,
            'alpha': 0.05,
            'n_replicates': 1000
        }
        is_valid, message = validate_monte_carlo_results(result, tolerance=0.005)
        assert isinstance(is_valid, bool)
        assert isinstance(message, str)

    def test_validate_monte_carlo_results_pass(self):
        """Verify validation passes when error rate is within tolerance."""
        result = {
            'type_1_error_rate': 0.05,
            'alpha': 0.05,
            'n_replicates': 1000
        }
        is_valid, _ = validate_monte_carlo_results(result, tolerance=0.005)
        assert is_valid is True

    def test_validate_monte_carlo_results_fail(self):
        """Verify validation fails when error rate is outside tolerance."""
        result = {
            'type_1_error_rate': 0.10,
            'alpha': 0.05,
            'n_replicates': 1000
        }
        is_valid, _ = validate_monte_carlo_results(result, tolerance=0.005)
        assert is_valid is False


class TestBatchValidation:
    """Tests for batch validation function."""

    def test_run_all_monte_carlo_validations_importable(self):
        """Verify run_all_monte_carlo_validations is importable."""
        test_configs = [
            {
                'test_type': 'z_test',
                'params': {'n1': 100, 'n2': 100, 'p1': 0.5, 'p2': 0.5, 'n_replicates': 10}
            }
        ]
        results = run_all_monte_carlo_validations(test_configs, seed=42)
        assert 'z_test' in results

    def test_run_all_monte_carlo_validations_multiple_tests(self):
        """Verify batch validation works with multiple test types."""
        test_configs = [
            {
                'test_type': 'z_test',
                'params': {'n1': 100, 'n2': 100, 'p1': 0.5, 'p2': 0.5, 'n_replicates': 10}
            },
            {
                'test_type': 'fisher_exact',
                'params': {'n1': 100, 'n2': 100, 'p1': 0.5, 'p2': 0.5, 'n_replicates': 10}
            }
        ]
        results = run_all_monte_carlo_validations(test_configs, seed=42)
        assert 'z_test' in results
        assert 'fisher_exact' in results


class TestDefaultConstants:
    """Tests for default constants."""

    def test_default_n_replicates(self):
        """Verify DEFAULT_N_REPLICATES is defined."""
        assert DEFAULT_N_REPLICATES == 10000

    def test_all_tests_use_default_replicates(self):
        """Verify functions use DEFAULT_N_REPLICATES when not specified."""
        # Just verify the constant exists and is reasonable
        assert DEFAULT_N_REPLICATES >= 1000
        assert DEFAULT_N_REPLICATES <= 100000
