"""
Unit tests for synthetic MDP generation.

Tests cover:
- Basic MDP generation with N objectives
- Noise correlation parameter ρ (FR-009)
- Deterministic seeded random state management
- Edge cases (N=5, N=50, ρ=0, ρ=1)
"""

import pytest
import numpy as np
import sys
import os
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.environment.synthetic_mdp import SyntheticTabularMDP, generate_mdp


class TestSyntheticMDPGeneration:
    """Test basic MDP generation functionality."""

    def test_generate_mdp_basic(self):
        """Test basic MDP generation with default parameters."""
        mdp = generate_mdp(n_objectives=5)
        assert mdp.n_objectives == 5
        assert mdp.n_actions == 5
        assert mdp.n_horizon == 20
        assert mdp.noise_correlation == 0.0

    def test_generate_mdp_custom_params(self):
        """Test MDP generation with custom parameters."""
        mdp = generate_mdp(
            n_objectives=10,
            n_states=100,
            n_actions=3,
            n_horizon=50,
            noise_correlation=0.5,
            seed=42
        )
        assert mdp.n_objectives == 10
        assert mdp.n_states == 100
        assert mdp.n_actions == 3
        assert mdp.n_horizon == 50
        assert mdp.noise_correlation == 0.5
        assert mdp.seed == 42

    def test_generate_mdp_n5_requirement(self):
        """Test N=5 case explicitly as per FR-003."""
        mdp = generate_mdp(n_objectives=5)
        assert mdp.n_objectives == 5
        assert mdp.reward_matrix.shape[0] == 5  # 5 objectives

    def test_generate_mdp_large_n(self):
        """Test MDP generation with large N (e.g., N=50)."""
        mdp = generate_mdp(n_objectives=50)
        assert mdp.n_objectives == 50
        # State space should auto-scale but be reasonable
        assert mdp.n_states >= 100  # At least 2*N

    def test_reward_matrix_shape(self):
        """Test that reward matrix has correct shape."""
        n_states, n_actions, n_objectives = 20, 5, 10
        mdp = generate_mdp(
            n_objectives=n_objectives,
            n_states=n_states,
            n_actions=n_actions
        )
        # Reward matrix shape: (n_objectives, n_states, n_actions)
        assert mdp.reward_matrix.shape == (n_objectives, n_states, n_actions)


class TestNoiseCorrelation:
    """Test noise correlation parameter ρ (FR-009)."""

    def test_noise_correlation_zero(self):
        """Test that ρ=0 produces independent noise (identity covariance)."""
        mdp = generate_mdp(n_objectives=5, noise_correlation=0.0, seed=42)
        cov = mdp.noise_covariance
        expected = np.eye(5)
        assert np.allclose(cov, expected), "ρ=0 should produce identity covariance"

    def test_noise_correlation_positive(self):
        """Test that ρ>0 produces correlated noise."""
        rho = 0.5
        mdp = generate_mdp(n_objectives=5, noise_correlation=rho, seed=42)
        cov = mdp.noise_covariance
        # Diagonal should be 1
        assert np.allclose(np.diag(cov), np.ones(5))
        # Off-diagonal should be rho
        off_diag = cov[np.triu_indices(5, k=1)]
        assert np.allclose(off_diag, rho), f"Off-diagonal should be {rho}"

    def test_noise_correlation_edge_cases(self):
        """Test noise correlation at boundaries."""
        # ρ=0
        mdp0 = generate_mdp(n_objectives=3, noise_correlation=0.0)
        assert np.allclose(mdp0.noise_covariance, np.eye(3))

        # ρ=1 (perfect correlation)
        mdp1 = generate_mdp(n_objectives=3, noise_correlation=1.0)
        expected = np.ones((3, 3))
        assert np.allclose(mdp1.noise_covariance, expected)

    def test_noise_correlation_invalid(self):
        """Test that invalid ρ raises error."""
        with pytest.raises(ValueError):
            generate_mdp(n_objectives=5, noise_correlation=-0.1)
        with pytest.raises(ValueError):
            generate_mdp(n_objectives=5, noise_correlation=1.5)

    def test_sample_noise_correlation(self):
        """Test that sampled noise exhibits expected correlation."""
        rho = 0.8
        mdp = generate_mdp(n_objectives=5, noise_correlation=rho, seed=42)

        # Sample many noise vectors
        n_samples = 10000
        samples = mdp.sample_noise(n_samples)

        # Compute empirical covariance
        emp_cov = np.cov(samples.T)

        # Check correlation structure (allow some sampling error)
        # Diagonal should be close to 1
        assert np.allclose(np.diag(emp_cov), np.ones(5), atol=0.1)
        # Off-diagonal should be close to rho
        off_diag_emp = emp_cov[np.triu_indices(5, k=1)]
        assert np.allclose(off_diag_emp, rho, atol=0.1), \
            f"Empirical correlation {np.mean(off_diag_emp):.3f} != {rho}"


class TestDeterminism:
    """Test deterministic seeded random state management."""

    def test_determinism_same_seed(self):
        """Test that same seed produces identical MDPs."""
        seed = 12345
        mdp1 = generate_mdp(n_objectives=5, seed=seed)
        mdp2 = generate_mdp(n_objectives=5, seed=seed)

        assert np.allclose(mdp1.state_features, mdp2.state_features)
        assert np.allclose(mdp1.reward_weights, mdp2.reward_weights)
        assert np.allclose(mdp1.transition_matrix, mdp2.transition_matrix)
        assert np.allclose(mdp1.noise_covariance, mdp2.noise_covariance)

    def test_determinism_different_seed(self):
        """Test that different seeds produce different MDPs."""
        mdp1 = generate_mdp(n_objectives=5, seed=100)
        mdp2 = generate_mdp(n_objectives=5, seed=200)

        assert not np.allclose(mdp1.state_features, mdp2.state_features)
        assert not np.allclose(mdp1.reward_weights, mdp2.reward_weights)

    def test_determinism_no_seed(self):
        """Test that no seed produces different MDPs each time."""
        mdp1 = generate_mdp(n_objectives=5)
        mdp2 = generate_mdp(n_objectives=5)

        # Very unlikely to be identical by chance
        assert not np.allclose(mdp1.state_features, mdp2.state_features)


class TestValidation:
    """Test MDP validation and properties."""

    def test_transition_matrix_valid(self):
        """Test that transition matrix is valid (rows sum to 1)."""
        mdp = generate_mdp(n_objectives=5, n_states=20, n_actions=5)
        # Sum over next states should be 1 for each state-action pair
        row_sums = mdp.transition_matrix.sum(axis=2)
        assert np.allclose(row_sums, np.ones((20, 5)))

    def test_noise_covariance_psd(self):
        """Test that noise covariance is positive semi-definite."""
        for rho in [0.0, 0.2, 0.5, 0.8, 1.0]:
            mdp = generate_mdp(n_objectives=5, noise_correlation=rho)
            eigvals = np.linalg.eigvalsh(mdp.noise_covariance)
            assert np.all(eigvals >= -1e-10), f"ρ={rho} produced non-PSD matrix"

    def test_reward_structure(self):
        """Test that rewards follow the linear combination structure."""
        mdp = generate_mdp(n_objectives=3, n_states=10, seed=42)

        # R(s,o) should be w_o · φ(s)
        for s in range(mdp.n_states):
            for o in range(mdp.n_objectives):
                expected = np.dot(mdp.reward_weights[o], mdp.state_features[s])
                assert np.isclose(mdp.base_rewards[o, s], expected)


class TestMetadataAndIO:
    """Test MDP metadata and I/O operations."""

    def test_get_info(self):
        """Test that get_info returns correct metadata."""
        mdp = generate_mdp(n_objectives=5, noise_correlation=0.3, seed=42)
        info = mdp.get_info()

        assert info["n_objectives"] == 5
        assert info["noise_correlation"] == 0.3
        assert info["seed"] == 42
        assert "n_states" in info
        assert "n_actions" in info
        assert "noise_covariance_eigvals" in info

    def test_save_and_load(self):
        """Test saving and loading MDP to/from JSON."""
        mdp1 = generate_mdp(n_objectives=5, n_states=20, seed=42)

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            mdp1.save(temp_path)
            mdp2 = SyntheticTabularMDP.load(temp_path)

            assert mdp1.n_objectives == mdp2.n_objectives
            assert mdp1.n_states == mdp2.n_states
            assert np.allclose(mdp1.state_features, mdp2.state_features)
            assert np.allclose(mdp1.reward_weights, mdp2.reward_weights)
            assert np.allclose(mdp1.noise_covariance, mdp2.noise_covariance)
        finally:
            os.unlink(temp_path)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimal_mdp(self):
        """Test minimal valid MDP (N=1)."""
        mdp = generate_mdp(n_objectives=1)
        assert mdp.n_objectives == 1
        assert mdp.reward_matrix.shape[0] == 1

    def test_large_noise_correlation(self):
        """Test MDP with high noise correlation."""
        mdp = generate_mdp(n_objectives=10, noise_correlation=0.99)
        eigvals = np.linalg.eigvalsh(mdp.noise_covariance)
        assert np.all(eigvals >= 0)

    def test_state_space_scaling(self):
        """Test that state space scales appropriately with N."""
        mdp5 = generate_mdp(n_objectives=5)
        mdp50 = generate_mdp(n_objectives=50)

        # State space should increase with N
        assert mdp50.n_states > mdp5.n_states
        # But should be reasonable (not exponential)
        assert mdp50.n_states < 500  # Cap check

    def test_step_function(self):
        """Test the step function returns valid outputs."""
        mdp = generate_mdp(n_objectives=3, n_states=10, n_actions=5)
        state = mdp.reset()

        next_state, rewards = mdp.step(state, action=0)

        assert 0 <= next_state < mdp.n_states
        assert len(rewards) == mdp.n_objectives
        assert isinstance(rewards, np.ndarray)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])