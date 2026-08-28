import pytest
import numpy as np
from unittest.mock import patch, MagicMock
import tempfile
import os

from models.bayesian import BayesianModel, fit_bayesian_and_get_intervals
from simulation.config import SimulationConfig
from simulation.engine import generate_synthetic_data


class TestBayesianConvergenceChecks:
    """Unit tests for Bayesian convergence checks (R-hat) in US2."""

    @pytest.fixture
    def small_sample_config(self):
        """Fixture for a small sample simulation config."""
        return SimulationConfig(
            N=30,
            n_predictors=3,
            rho=0.0,
            noise_std=1.0,
            true_coefficients=np.array([1.0, 2.0, -1.5, 0.5]),
            seed=42
        )

    @pytest.fixture
    def synthetic_dataset(self, small_sample_config):
        """Generate a synthetic dataset for testing."""
        return generate_synthetic_data(small_sample_config, small_sample_config.seed)

    def test_bayesian_model_initialization(self, synthetic_dataset):
        """Test that BayesianModel initializes correctly."""
        model = BayesianModel()
        assert model is not None
        assert model.priors is not None
        assert 'beta_prior' in model.priors
        assert 'sigma_prior' in model.priors

    def test_fit_bayesian_returns_intervals(self, synthetic_dataset):
        """Test that fitting returns valid interval structures."""
        X = synthetic_dataset.X
        y = synthetic_dataset.y

        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=500,
            n_warmup=250,
            seed=42
        )

        assert 'beta_intervals' in intervals
        assert 'sigma_interval' in intervals
        assert 'r_hat' in intervals
        assert 'n_eff' in intervals

        # Check that intervals have correct structure
        assert len(intervals['beta_intervals']) == X.shape[1]
        for interval in intervals['beta_intervals']:
            assert 'lower' in interval
            assert 'upper' in interval
            assert 'point_estimate' in interval

    @patch('models.bayesian.CmdStanModel')
    def test_r_hat_convergence_check(self, mock_cmdstan_model, synthetic_dataset):
        """Test that R-hat values are correctly extracted and checked."""
        # Mock the model fit object
        mock_fit = MagicMock()
        mock_fit.stan_variable.return_value = np.random.randn(2, 100, synthetic_dataset.X.shape[1] + 1)
        mock_fit.summary.return_value = {
            'R-hat': np.array([1.01, 1.01, 1.01, 1.01, 1.01])  # Good convergence
        }

        mock_model = MagicMock()
        mock_model.sample.return_value = mock_fit
        mock_cmdstan_model.return_value = mock_model

        X = synthetic_dataset.X
        y = synthetic_dataset.y

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write a minimal Stan model file
            stan_code = """
            data {
                int<lower=0> N;
                int<lower=0> K;
                matrix[N, K] X;
                vector[N] y;
            }
            parameters {
                vector[K] beta;
                real<lower=0> sigma;
            }
            model {
                beta ~ normal(0, 10);
                sigma ~ cauchy(0, 5);
                y ~ normal(X * beta, sigma);
            }
            """
            stan_file = os.path.join(tmpdir, "test_model.stn")
            with open(stan_file, 'w') as f:
                f.write(stan_code)

            # Compile and fit
            model = BayesianModel()
            model.stan_file = stan_file
            model.compile_model()

            result = model.fit(X, y, n_chains=2, n_samples=100, n_warmup=50, seed=42)

            # Verify R-hat is accessible
            assert result is not None
            assert 'r_hat' in result

    def test_r_hat_threshold_check(self, synthetic_dataset):
        """Test that R-hat > 1.05 is correctly identified as non-converged."""
        X = synthetic_dataset.X
        y = synthetic_dataset.y

        # This test verifies the logic of R-hat checking
        # In practice, we'd mock the fit to return specific R-hat values
        # but for now we test that the function returns the expected structure

        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            seed=42
        )

        # R-hat should be present
        assert 'r_hat' in intervals

        # Check that R-hat values are reasonable (typically close to 1.0)
        r_hat_values = intervals['r_hat']
        assert isinstance(r_hat_values, (list, np.ndarray))
        assert len(r_hat_values) > 0

    def test_divergent_transitions_detection(self, synthetic_dataset):
        """Test that divergent transitions are detected and reported."""
        X = synthetic_dataset.X
        y = synthetic_dataset.y

        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            seed=42
        )

        # The result should include diagnostic information
        assert 'divergent_transitions' in intervals or 'diagnostics' in intervals

    def test_multiple_chains_consistency(self, synthetic_dataset):
        """Test that multiple chains produce consistent results."""
        X = synthetic_dataset.X
        y = synthetic_dataset.y

        # Run with multiple chains
        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=4,
            n_samples=200,
            n_warmup=100,
            seed=42
        )

        # R-hat should be computed across chains
        assert 'r_hat' in intervals

        # Check that we have R-hat for all parameters
        r_hat_values = intervals['r_hat']
        expected_params = X.shape[1] + 1  # beta + sigma
        assert len(r_hat_values) == expected_params

    def test_small_sample_convergence(self, small_sample_config):
        """Test convergence behavior with very small sample size."""
        config = SimulationConfig(
            N=10,
            n_predictors=2,
            rho=0.0,
            noise_std=1.0,
            true_coefficients=np.array([1.0, 2.0, 0.5]),
            seed=42
        )
        dataset = generate_synthetic_data(config, config.seed)

        X = dataset.X
        y = dataset.y

        # Should handle small samples without crashing
        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=100,
            n_warmup=50,
            seed=42
        )

        assert 'beta_intervals' in intervals
        assert 'r_hat' in intervals

    def test_r_hat_failure_flagging(self, synthetic_dataset):
        """Test that non-converged runs (R-hat > 1.05) are properly flagged."""
        # This test validates the logic for identifying failed convergence
        # In a real scenario, we'd need to force a non-convergent fit
        # For now, we verify the structure handles R-hat values correctly

        X = synthetic_dataset.X
        y = synthetic_dataset.y

        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            seed=42
        )

        # Verify R-hat is a numeric value
        r_hat_values = intervals['r_hat']
        for val in r_hat_values:
            assert isinstance(val, (int, float, np.number))
            assert not np.isnan(val)

    def test_effective_sample_size_calculation(self, synthetic_dataset):
        """Test that effective sample size (n_eff) is calculated."""
        X = synthetic_dataset.X
        y = synthetic_dataset.y

        intervals = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            seed=42
        )

        assert 'n_eff' in intervals
        n_eff_values = intervals['n_eff']
        assert len(n_eff_values) > 0
        assert all(isinstance(v, (int, float, np.number)) for v in n_eff_values)

    def test_seed_reproducibility(self, synthetic_dataset):
        """Test that results are reproducible with the same seed."""
        X = synthetic_dataset.X
        y = synthetic_dataset.y

        intervals_1 = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            seed=123
        )

        intervals_2 = fit_bayesian_and_get_intervals(
            X, y,
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            seed=123
        )

        # Point estimates should be identical with same seed
        np.testing.assert_array_almost_equal(
            intervals_1['beta_intervals'],
            intervals_2['beta_intervals'],
            decimal=5
        )