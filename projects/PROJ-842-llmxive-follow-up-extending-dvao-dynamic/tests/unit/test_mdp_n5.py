"""
Unit tests for N=5 MDP generation (Task T031a).
Explicitly verifies FR-003 N=5 requirement.
"""
import pytest
import numpy as np
import sys
import os

# Add project root to path to allow imports from src/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.environment.synthetic_mdp import generate_mdp, SyntheticTabularMDP


class TestMDPN5:
    """Tests specifically for the N=5 requirement (FR-003)."""

    def test_generate_mdp_n5_objectives(self):
        """Verify generate_mdp(5) returns a valid MDP with exactly 5 objectives."""
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        assert isinstance(mdp, SyntheticTabularMDP), f"Expected SyntheticTabularMDP, got {type(mdp)}"
        assert mdp.n_objectives == 5, f"Expected 5 objectives, got {mdp.n_objectives}"

    def test_generate_mdp_n5_dimensions(self):
        """Verify dimensions are consistent for N=5."""
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        # Check transition shape: (S, A, S)
        assert mdp.transition_probs.shape == (mdp.n_states, mdp.n_actions, mdp.n_states), \
            f"Transition shape mismatch: {mdp.transition_probs.shape}"
        
        # Check reward matrices: List of (S, N) arrays
        assert len(mdp.reward_matrices) == mdp.n_actions, \
            f"Expected {mdp.n_actions} reward matrices, got {len(mdp.reward_matrices)}"
        
        for i, R in enumerate(mdp.reward_matrices):
            assert R.shape == (mdp.n_states, 5), \
                f"Reward matrix {i} shape mismatch: expected (S, 5), got {R.shape}"

    def test_generate_mdp_n5_determinism(self):
        """Verify that same seed produces same MDP for N=5."""
        mdp1 = generate_mdp(n_objectives=5, seed=123)
        mdp2 = generate_mdp(n_objectives=5, seed=123)
        
        assert mdp1.n_states == mdp2.n_states, "State count mismatch"
        assert mdp1.n_actions == mdp2.n_actions, "Action count mismatch"
        
        np.testing.assert_array_almost_equal(
            mdp1.transition_probs, 
            mdp2.transition_probs,
            decimal=6,
            err_msg="Transition probabilities differ for same seed"
        )
        
        for i, (R1, R2) in enumerate(zip(mdp1.reward_matrices, mdp2.reward_matrices)):
            np.testing.assert_array_almost_equal(
                R1, R2, decimal=6,
                err_msg=f"Reward matrix {i} differs for same seed"
            )

    def test_generate_mdp_n5_noise_correlation(self):
        """Verify N=5 works with different noise correlation values."""
        for rho in [0.0, 0.2, 0.5, 1.0]:
            mdp = generate_mdp(n_objectives=5, noise_correlation=rho, seed=42)
            assert mdp.n_objectives == 5, f"Failed for rho={rho}: objectives mismatch"
            assert mdp.noise_correlation == rho, f"Failed for rho={rho}: correlation mismatch"

    def test_generate_mdp_n5_valid_spaces(self):
        """Verify state and action spaces are valid and non-empty."""
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        assert mdp.n_states > 0, "State space is empty"
        assert mdp.n_actions > 0, "Action space is empty"
        
        # Verify transition probabilities sum to 1.0
        row_sums = mdp.transition_probs.sum(axis=2)
        np.testing.assert_allclose(
            row_sums, 
            1.0, 
            atol=1e-6, 
            err_msg="Transition probabilities do not sum to 1.0"
        )
    
    def test_cli_verification(self):
        """
        Verify the specific command from T015b/T031a:
        python -c "from src.environment.synthetic_mdp import generate_mdp; mdp = generate_mdp(5); assert mdp.n_objectives == 5"
        """
        mdp = generate_mdp(5)
        assert mdp.n_objectives == 5, "CLI verification failed: N != 5"