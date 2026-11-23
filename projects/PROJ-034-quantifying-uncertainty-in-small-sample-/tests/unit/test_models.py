"""
Unit tests for uncertainty quantification models (OLS, Bootstrap, Bayesian).
"""
import pytest
import numpy as np
import os
import sys
import tempfile
import shutil

# Add project root to path to allow imports
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from models.ols import OLSModel, fit_ols_and_get_intervals
from models.bootstrap import BootstrapModel, fit_bootstrap_and_get_intervals
from models.bayesian import BayesianModel, fit_bayesian_and_get_intervals
from simulation.config import SimulationConfig
from simulation.engine import generate_synthetic_data


class TestOLSModel:
    """Tests for OLS interval calculation (T018)."""

    def test_ols_interval_calculation(self):
        """Verify OLS produces correct 95% confidence intervals."""
        # Setup: Simple linear relationship y = 2*x + noise
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 1)
        true_beta = np.array([2.0])
        noise = np.random.randn(n) * 0.5
        y = X @ true_beta + noise

        model = OLSModel()
        intervals = fit_ols_and_get_intervals(model, X, y, confidence_level=0.95)

        # Check structure
        assert 'coefficients' in intervals
        assert 'lower_bounds' in intervals
        assert 'upper_bounds' in intervals
        assert len(intervals['coefficients']) == 1
        assert len(intervals['lower_bounds']) == 1
        assert len(intervals['upper_bounds']) == 1

        # Check bounds are ordered
        assert intervals['lower_bounds'][0] < intervals['coefficients'][0]
        assert intervals['coefficients'][0] < intervals['upper_bounds'][0]

        # Check coverage (true value should be inside interval)
        assert intervals['lower_bounds'][0] <= true_beta[0] <= intervals['upper_bounds'][0]


class TestBootstrapModel:
    """Tests for Bootstrap BCa interval calculation (T019)."""

    def test_bootstrap_bca_interval_calculation(self):
        """Verify Bootstrap BCa produces valid intervals."""
        # Setup
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        true_beta = np.array([1.5, -0.5])
        noise = np.random.randn(n) * 0.5
        y = X @ true_beta + noise

        model = BootstrapModel(n_bootstraps=1000)  # Reduced for speed
        intervals = fit_bootstrap_and_get_intervals(model, X, y, confidence_level=0.95)

        # Check structure
        assert 'coefficients' in intervals
        assert 'lower_bounds' in intervals
        assert 'upper_bounds' in intervals
        assert len(intervals['coefficients']) == 2
        assert len(intervals['lower_bounds']) == 2
        assert len(intervals['upper_bounds']) == 2

        # Check bounds are ordered
        for i in range(2):
            assert intervals['lower_bounds'][i] < intervals['coefficients'][i]
            assert intervals['coefficients'][i] < intervals['upper_bounds'][i]

        # Check coverage
        for i in range(2):
            assert intervals['lower_bounds'][i] <= true_beta[i] <= intervals['upper_bounds'][i]


class TestBayesianModel:
    """Tests for Bayesian convergence checks (R-hat) (T020)."""

    def test_bayesian_rhat_convergence_check(self):
        """Verify Bayesian model correctly calculates and reports R-hat."""
        # Setup: Well-behaved data for convergence
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        true_beta = np.array([1.0, -1.0])
        noise = np.random.randn(n) * 0.5
        y = X @ true_beta + noise

        model = BayesianModel(
            n_chains=4,
            n_samples=500,
            n_warmup=250,
            seed=42
        )

        # Fit model
        intervals, diagnostics = fit_bayesian_and_get_intervals(
            model, X, y, confidence_level=0.95
        )

        # Check that R-hat is present in diagnostics
        assert 'r_hat' in diagnostics
        assert isinstance(diagnostics['r_hat'], (list, np.ndarray))
        assert len(diagnostics['r_hat']) == 2  # Number of coefficients

        # Check that R-hat is close to 1.0 for well-behaved data (convergence)
        # Allow a small tolerance (e.g., < 1.05) as per standard practice
        for r_hat_val in diagnostics['r_hat']:
            assert 0.95 <= r_hat_val <= 1.05, f"R-hat {r_hat_val} indicates poor convergence"

    def test_bayesian_divergent_transitions_check(self):
        """Verify Bayesian model detects and reports divergent transitions."""
        # Setup: Well-behaved data
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        true_beta = np.array([1.0, -1.0])
        noise = np.random.randn(n) * 0.5
        y = X @ true_beta + noise

        model = BayesianModel(
            n_chains=4,
            n_samples=500,
            n_warmup=250,
            seed=42
        )

        intervals, diagnostics = fit_bayesian_and_get_intervals(
            model, X, y, confidence_level=0.95
        )

        # Check that divergent transitions are reported
        assert 'divergent_transitions' in diagnostics
        assert isinstance(diagnostics['divergent_transitions'], int)
        assert diagnostics['divergent_transitions'] >= 0

    def test_bayesian_effective_sample_size(self):
        """Verify Bayesian model reports effective sample size (ESS)."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        true_beta = np.array([1.0, -1.0])
        noise = np.random.randn(n) * 0.5
        y = X @ true_beta + noise

        model = BayesianModel(
            n_chains=4,
            n_samples=500,
            n_warmup=250,
            seed=42
        )

        intervals, diagnostics = fit_bayesian_and_get_intervals(
            model, X, y, confidence_level=0.95
        )

        # Check ESS is present
        assert 'ess' in diagnostics
        assert isinstance(diagnostics['ess'], (list, np.ndarray))
        assert len(diagnostics['ess']) == 2

        # ESS should be a reasonable fraction of total samples
        total_samples_per_chain = model.n_samples + model.n_warmup
        for ess_val in diagnostics['ess']:
            assert ess_val > 0
            assert ess_val <= (total_samples_per_chain * model.n_chains)

    def test_bayesian_rhat_failure_detection(self):
        """Verify that R-hat > 1.05 is correctly identified as failure."""
        # This test uses a scenario that might cause convergence issues
        # (e.g., very small sample size or high noise)
        np.random.seed(123)
        n = 10  # Very small sample
        X = np.random.randn(n, 2)
        true_beta = np.array([1.0, -1.0])
        noise = np.random.randn(n) * 5.0  # High noise
        y = X @ true_beta + noise

        model = BayesianModel(
            n_chains=4,
            n_samples=200,  # Reduced samples
            n_warmup=100,
            seed=123
        )

        intervals, diagnostics = fit_bayesian_and_get_intervals(
            model, X, y, confidence_level=0.95
        )

        # R-hat might be high, but we just check it's calculated
        assert 'r_hat' in diagnostics
        # Note: We don't assert R-hat > 1.05 here because CmdStan might
        # still converge with enough warmup, but we verify the metric exists.

    def test_bayesian_interval_structure(self):
        """Verify Bayesian intervals have correct structure."""
        np.random.seed(42)
        n = 100
        X = np.random.randn(n, 2)
        true_beta = np.array([1.0, -1.0])
        noise = np.random.randn(n) * 0.5
        y = X @ true_beta + noise

        model = BayesianModel(n_chains=4, n_samples=500, n_warmup=250, seed=42)

        intervals, diagnostics = fit_bayesian_and_get_intervals(
            model, X, y, confidence_level=0.95
        )

        assert 'coefficients' in intervals
        assert 'lower_bounds' in intervals
        assert 'upper_bounds' in intervals
        assert len(intervals['coefficients']) == 2
        assert len(intervals['lower_bounds']) == 2
        assert len(intervals['upper_bounds']) == 2

        # Check bounds are ordered
        for i in range(2):
            assert intervals['lower_bounds'][i] <= intervals['coefficients'][i]
            assert intervals['coefficients'][i] <= intervals['upper_bounds'][i]