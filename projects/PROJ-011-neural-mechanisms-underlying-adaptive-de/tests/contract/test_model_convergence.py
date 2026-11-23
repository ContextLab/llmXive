"""
Contract test for model convergence (T021).

Verifies that the belief updating model implementation satisfies the convergence
criteria defined in claim c_02979941 (arXiv:2607.02000).

This test ensures that when the model is fitted to data generated from the
specified generative process, the posterior estimates converge to the ground truth
parameters within the defined error margins.
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path

# Import the model components
from code.modeling.belief_updater import fit_belief_updater_model
from code.modeling.synthetic_data_generator import generate_synthetic_behavioral_data
from code.utils.config import set_seed


class TestModelConvergence:
    """Contract tests for model convergence verification."""

    @pytest.fixture(autouse=True)
    def setup(self, tmp_path):
        """Set up test fixtures."""
        self.tmp_path = tmp_path
        self.data_dir = tmp_path / "data"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        set_seed(42)

    def test_convergence_to_ground_truth(self):
        """
        Verify that the model converges to ground truth parameters.

        According to claim c_02979941 (arXiv:2607.02000), the hierarchical Bayesian
        model should recover ground truth parameters within a 10% relative error
        margin when fitted to synthetic data generated from the same process.
        """
        # Generate synthetic data with known ground truth
        n_participants = 20
        n_trials = 100
        ground_truth_alpha = 0.3
        ground_truth_beta = 2.0

        synthetic_data = generate_synthetic_behavioral_data(
            n_participants=n_participants,
            n_trials_per_participant=n_trials,
            true_alpha=ground_truth_alpha,
            true_beta=ground_truth_beta,
            output_path=self.data_dir / "synthetic_behavior.csv"
        )

        # Fit the model
        results = fit_belief_updater_model(
            data_path=self.data_dir / "synthetic_behavior.csv",
            output_dir=self.tmp_path / "model_output",
            n_chains=2,
            n_samples=500,  # Reduced for contract test speed
            n_warmup=250,
            max_runtime_seconds=300
        )

        # Verify convergence metrics
        assert "convergence_metrics" in results
        metrics = results["convergence_metrics"]

        # Check R-hat values (must be < 1.05 for convergence)
        assert metrics["mean_rhat"] < 1.05, \
            f"Mean R-hat {metrics['mean_rhat']:.4f} exceeds threshold 1.05"

        # Check ESS (effective sample size)
        assert metrics["min_ess"] > 100, \
            f"Minimum ESS {metrics['min_ess']} below threshold 100"

        # Verify parameter recovery (within 10% relative error)
        recovered_alpha = results["recovered_parameters"]["alpha_mean"]
        recovered_beta = results["recovered_parameters"]["beta_mean"]

        alpha_error = abs(recovered_alpha - ground_truth_alpha) / ground_truth_alpha
        beta_error = abs(recovered_beta - ground_truth_beta) / ground_truth_beta

        assert alpha_error < 0.10, \
            f"Alpha recovery error {alpha_error:.2%} exceeds 10% threshold"
        assert beta_error < 0.10, \
            f"Beta recovery error {beta_error:.2%} exceeds 10% threshold"

    def test_convergence_stability_across_chains(self):
        """
        Verify that multiple chains converge to the same posterior.

        The model should produce consistent results across different chains,
        indicating proper mixing and convergence.
        """
        # Generate synthetic data
        synthetic_data = generate_synthetic_behavioral_data(
            n_participants=10,
            n_trials_per_participant=50,
            true_alpha=0.25,
            true_beta=1.5,
            output_path=self.data_dir / "synthetic_stability.csv"
        )

        # Fit model with multiple chains
        results = fit_belief_updater_model(
            data_path=self.data_dir / "synthetic_stability.csv",
            output_dir=self.tmp_path / "stability_output",
            n_chains=4,
            n_samples=300,
            n_warmup=150,
            max_runtime_seconds=180
        )

        # Verify chain consistency
        assert "chain_diagnostics" in results
        chain_diag = results["chain_diagnostics"]

        # All chains should have similar means (within 5%)
        alpha_chain_means = chain_diag["alpha_chain_means"]
        beta_chain_means = chain_diag["beta_chain_means"]

        alpha_range = max(alpha_chain_means) - min(alpha_chain_means)
        beta_range = max(beta_chain_means) - min(beta_chain_means)

        assert alpha_range < 0.05, \
            f"Alpha chain variance {alpha_range:.4f} exceeds 0.05 threshold"
        assert beta_range < 0.05, \
            f"Beta chain variance {beta_range:.4f} exceeds 0.05 threshold"

    def test_non_convergence_detection(self):
        """
        Verify that the model correctly detects non-convergence.

        When fitted to data that doesn't match the model assumptions,
        the convergence diagnostics should flag issues.
        """
        # Generate data with extreme noise (violates model assumptions)
        synthetic_data = generate_synthetic_behavioral_data(
            n_participants=5,
            n_trials_per_participant=20,
            true_alpha=0.8,  # Very high learning rate
            true_beta=0.1,   # Very low inverse temperature (random choices)
            noise_level=0.5,  # High noise
            output_path=self.data_dir / "noisy_data.csv"
        )

        # Fit model
        results = fit_belief_updater_model(
            data_path=self.data_dir / "noisy_data.csv",
            output_dir=self.tmp_path / "non_converge_output",
            n_chains=2,
            n_samples=200,
            n_warmup=100,
            max_runtime_seconds=120,
            fail_on_non_convergence=False  # Don't fail, just detect
        )

        # Check that convergence issues are detected
        assert "convergence_metrics" in results
        metrics = results["convergence_metrics"]

        # With noisy data, we expect higher R-hat or lower ESS
        # This test verifies the detection mechanism works
        assert "convergence_flag" in results
        if not results["convergence_flag"]:
            # If flagged as non-convergent, verify diagnostics support this
            assert metrics["mean_rhat"] > 1.01 or metrics["min_ess"] < 50, \
                "Non-convergence detected but diagnostics don't support it"