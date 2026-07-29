import pytest
import numpy as np
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.environment.synthetic_mdp import generate_heavy_tailed_mdp, generate_mdp

class TestHeavyTailedMDP:
    """Test cases for heavy-tailed MDP generation (T034c)."""

    def test_heavy_tailed_generation_basic(self):
        """Test basic heavy-tailed MDP generation with default parameters."""
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        
        assert mdp.n_objectives == 5
        assert mdp.noise_distribution == 'heavy_tailed'
        assert mdp.dof == 3
        assert mdp.seed == 42
        assert mdp.n_states > 0
        assert mdp.n_actions > 0

    def test_heavy_tailed_reproducibility(self):
        """Test that heavy-tailed MDP generation is reproducible with same seed."""
        mdp1 = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        mdp2 = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        
        # Check that metadata matches
        assert mdp1.to_dict() == mdp2.to_dict()
        
        # Check that reward functions are identical
        for r1, r2 in zip(mdp1.reward_functions, mdp2.reward_functions):
            np.testing.assert_array_equal(r1, r2)

    def test_heavy_tailed_different_seeds(self):
        """Test that different seeds produce different MDPs."""
        mdp1 = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        mdp2 = generate_heavy_tailed_mdp(n_objectives=5, seed=123)
        
        # At least one reward function should be different
        different = False
        for r1, r2 in zip(mdp1.reward_functions, mdp2.reward_functions):
            if not np.allclose(r1, r2):
                different = True
                break
        
        assert different, "Different seeds should produce different MDPs"

    def test_heavy_tailed_dof_parameter(self):
        """Test that degrees of freedom parameter is correctly set."""
        for dof in [3, 5, 10]:
            mdp = generate_heavy_tailed_mdp(n_objectives=5, dof=dof, seed=42)
            assert mdp.dof == dof
            assert mdp.noise_distribution == 'heavy_tailed'

    def test_heavy_tailed_invalid_dof(self):
        """Test that dof <= 2 raises an error (variance undefined)."""
        with pytest.raises(ValueError, match="Degrees of freedom must be > 2"):
            generate_heavy_tailed_mdp(n_objectives=5, dof=2)
        
        with pytest.raises(ValueError, match="Degrees of freedom must be > 2"):
            generate_heavy_tailed_mdp(n_objectives=5, dof=1)

    def test_heavy_tailed_noise_correlation(self):
        """Test heavy-tailed MDP with noise correlation."""
        for rho in [0.0, 0.2, 0.5]:
            mdp = generate_heavy_tailed_mdp(
                n_objectives=5, 
                noise_correlation=rho, 
                seed=42
            )
            assert mdp.noise_correlation == rho
            assert mdp.noise_distribution == 'heavy_tailed'

    def test_heavy_tailed_objective_count(self):
        """Test that MDP has correct number of objectives."""
        for n_obj in [5, 10, 20]:
            mdp = generate_heavy_tailed_mdp(n_objectives=n_obj, seed=42)
            assert mdp.n_objectives == n_obj
            assert len(mdp.reward_functions) == n_obj

    def test_heavy_tailed_reward_shape(self):
        """Test that reward functions have correct shape."""
        n_states = 20
        n_actions = 4
        n_objectives = 5
        
        mdp = generate_heavy_tailed_mdp(
            n_objectives=n_objectives,
            n_states=n_states,
            n_actions=n_actions,
            seed=42
        )
        
        assert mdp.n_states == n_states
        assert mdp.n_actions == n_actions
        
        for reward_matrix in mdp.reward_functions:
            assert reward_matrix.shape == (n_states, n_actions)

    def test_heavy_tailed_transition_matrix(self):
        """Test that transition matrix is valid stochastic matrix."""
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        
        # Check shape
        assert mdp.transition_matrix.shape == (
            mdp.n_states, mdp.n_actions, mdp.n_states
        )
        
        # Check that rows sum to 1
        row_sums = mdp.transition_matrix.sum(axis=2)
        np.testing.assert_allclose(row_sums, 1.0, atol=1e-6)
        
        # Check that all values are non-negative
        assert np.all(mdp.transition_matrix >= 0)

    def test_heavy_tailed_metadata(self):
        """Test that metadata contains expected fields."""
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42, dof=5)
        
        assert 'generation_seed' in mdp.metadata
        assert 'noise_distribution' in mdp.metadata
        assert 'degrees_of_freedom' in mdp.metadata
        assert 'correlation_parameter' in mdp.metadata
        
        assert mdp.metadata['noise_distribution'] == 'heavy_tailed'
        assert mdp.metadata['degrees_of_freedom'] == 5
        assert mdp.metadata['correlation_parameter'] == 0.0

    def test_heavy_tailed_vs_gaussian(self):
        """Test that heavy-tailed and Gaussian MDPs are different."""
        mdp_heavy = generate_heavy_tailed_mdp(n_objectives=5, seed=42, dof=3)
        mdp_gauss = generate_mdp(n_objectives=5, seed=42, noise_distribution='gaussian')
        
        # They should be different due to different noise distributions
        different = False
        for r1, r2 in zip(mdp_heavy.reward_functions, mdp_gauss.reward_functions):
            if not np.allclose(r1, r2):
                different = True
                break
        
        assert different, "Heavy-tailed and Gaussian MDPs should be different"

    def test_heavy_tailed_large_objectives(self):
        """Test heavy-tailed MDP with larger number of objectives."""
        mdp = generate_heavy_tailed_mdp(n_objectives=50, seed=42)
        assert mdp.n_objectives == 50
        assert len(mdp.reward_functions) == 50

    def test_heavy_tailed_state_space_degradation(self):
        """Test state space reduction for N > 50 with force_reduce_state_space."""
        # This tests the integration with the state space reduction logic
        mdp = generate_heavy_tailed_mdp(
            n_objectives=100, 
            seed=42,
            force_reduce_state_space=True
        )
        
        assert mdp.n_objectives == 100
        assert mdp.metadata.get('state_space_reduced', False) is True
        assert 'effective_n_states' in mdp.metadata
        assert 'original_n_states' in mdp.metadata

if __name__ == '__main__':
    pytest.main([__file__, '-v'])
