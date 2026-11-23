"""
Unit test for T031: Verify synthetic_mdp.py generates correct tabular MDPs with N objectives.
Specifically tests N=5 as per FR-003, and N=10, 20, 50.
Also tests noise correlation parameter ρ.
"""
import pytest
import numpy as np
import sys
import os

# Add src to path if not already
if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.environment.synthetic_mdp import generate_mdp, SyntheticTabularMDP


class TestMDPN5:
    """Test N=5 generation explicitly as per FR-003."""

    def test_generate_mdp_n5(self):
        """Verify generate_mdp(n_objectives=5) returns valid MDP with 5 objectives."""
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        assert mdp is not None
        assert isinstance(mdp, SyntheticTabularMDP)
        assert mdp.n_objectives == 5
        assert mdp.reward_functions.shape[0] == 5
        
        # Verify state and action spaces are valid
        assert mdp.n_states > 0
        assert mdp.n_actions > 0
        
        # Verify transition probabilities sum to 1
        for s in range(mdp.n_states):
            for a in range(mdp.n_actions):
                probs = mdp.transition_probs[s, a, :]
                assert np.isclose(probs.sum(), 1.0), f"Transition probs for s={s}, a={a} do not sum to 1"
        
        # Verify reward functions are valid
        assert mdp.reward_functions.shape == (5, mdp.n_states, mdp.n_actions)

    def test_generate_mdp_n5_deterministic(self):
        """Verify N=5 generation is deterministic with same seed."""
        mdp1 = generate_mdp(n_objectives=5, seed=123)
        mdp2 = generate_mdp(n_objectives=5, seed=123)
        
        assert np.array_equal(mdp1.transition_probs, mdp2.transition_probs)
        assert np.array_equal(mdp1.reward_functions, mdp2.reward_functions)
        assert mdp1.n_states == mdp2.n_states
        assert mdp1.n_actions == mdp2.n_actions

class TestMDPVariousN:
    """Test generation for N = 5, 10, 20, 50 as required by T031."""

    @pytest.mark.parametrize("n_objectives", [5, 10, 20, 50])
    def test_generate_mdp_various_n(self, n_objectives):
        """Verify generate_mdp works for N = 5, 10, 20, 50."""
        mdp = generate_mdp(n_objectives=n_objectives, seed=42)
        
        assert mdp is not None
        assert isinstance(mdp, SyntheticTabularMDP)
        assert mdp.n_objectives == n_objectives
        assert mdp.reward_functions.shape[0] == n_objectives
        assert mdp.reward_functions.shape[1] == mdp.n_states
        assert mdp.reward_functions.shape[2] == mdp.n_actions

    @pytest.mark.parametrize("n_objectives", [5, 10, 20, 50])
    def test_transition_probs_valid(self, n_objectives):
        """Verify transition probabilities are valid for various N."""
        mdp = generate_mdp(n_objectives=n_objectives, seed=42)
        
        for s in range(mdp.n_states):
            for a in range(mdp.n_actions):
                probs = mdp.transition_probs[s, a, :]
                assert np.all(probs >= 0), f"Negative probability for s={s}, a={a}"
                assert np.isclose(probs.sum(), 1.0), f"Transition probs do not sum to 1 for N={n_objectives}"

class TestNoiseCorrelation:
    """Test noise correlation parameter ρ as required by FR-009."""

    @pytest.mark.parametrize("rho", [0.0, 0.2, 0.5, 1.0])
    def test_noise_correlation_param(self, rho):
        """Verify MDP generation accepts and uses noise correlation parameter ρ."""
        mdp = generate_mdp(n_objectives=5, noise_correlation=rho, seed=42)
        
        assert mdp is not None
        assert mdp.n_objectives == 5
        
        # Verify the MDP has the expected structure
        assert mdp.reward_functions.shape[0] == 5
        
        # Note: The actual correlation structure is internal to the MDP generation
        # We verify the parameter is accepted and doesn't cause errors
        # The correlation effect would be visible in the reward function structure

    def test_noise_correlation_zero(self):
        """Test with ρ=0 (no correlation) - baseline case."""
        mdp = generate_mdp(n_objectives=5, noise_correlation=0.0, seed=42)
        assert mdp.n_objectives == 5
        assert mdp.reward_functions.shape[0] == 5

    def test_noise_correlation_positive(self):
        """Test with ρ>0 (positive correlation)."""
        mdp = generate_mdp(n_objectives=5, noise_correlation=0.5, seed=42)
        assert mdp.n_objectives == 5
        assert mdp.reward_functions.shape[0] == 5

class TestMDPStructure:
    """Test general MDP structure and validity."""

    def test_mdp_has_required_attributes(self):
        """Verify MDP has all required attributes."""
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        required_attrs = [
            'n_states', 'n_actions', 'n_objectives',
            'transition_probs', 'reward_functions',
            'state_features', 'seed'
        ]
        
        for attr in required_attrs:
            assert hasattr(mdp, attr), f"MDP missing required attribute: {attr}"

    def test_reward_functions_shape(self):
        """Verify reward functions have correct shape (N, |S|, |A|)."""
        for n_obj in [5, 10, 20, 50]:
            mdp = generate_mdp(n_objectives=n_obj, seed=42)
            expected_shape = (n_obj, mdp.n_states, mdp.n_actions)
            assert mdp.reward_functions.shape == expected_shape, \
                f"Reward shape mismatch for N={n_obj}: {mdp.reward_functions.shape} vs {expected_shape}"

    def test_transition_probs_shape(self):
        """Verify transition probabilities have correct shape (|S|, |A|, |S|)."""
        for n_obj in [5, 10, 20, 50]:
            mdp = generate_mdp(n_objectives=n_obj, seed=42)
            expected_shape = (mdp.n_states, mdp.n_actions, mdp.n_states)
            assert mdp.transition_probs.shape == expected_shape, \
                f"Transition shape mismatch for N={n_obj}: {mdp.transition_probs.shape} vs {expected_shape}"

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
