import pytest
import numpy as np
import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.environment.synthetic_mdp import generate_heavy_tailed_mdp

class TestHeavyTailedIntegration:
    """Integration tests for heavy-tailed MDP generation."""

    def test_full_generation_cycle(self):
        """Test complete generation cycle with verification."""
        mdp = generate_heavy_tailed_mdp(
            n_objectives=10,
            n_states=50,
            n_actions=5,
            noise_correlation=0.3,
            seed=42,
            dof=3
        )
        
        # Verify all components
        assert mdp.n_objectives == 10
        assert mdp.n_states == 50
        assert mdp.n_actions == 5
        assert mdp.noise_correlation == 0.3
        assert mdp.dof == 3
        assert mdp.seed == 42
        
        # Verify reward functions exist and have correct shape
        assert len(mdp.reward_functions) == 10
        for i, reward_matrix in enumerate(mdp.reward_functions):
            assert reward_matrix.shape == (50, 5)
            assert np.all(np.isfinite(reward_matrix))

    def test_to_dict_serialization(self):
        """Test MDP serialization to dictionary."""
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        
        mdp_dict = mdp.to_dict()
        
        assert 'n_states' in mdp_dict
        assert 'n_actions' in mdp_dict
        assert 'n_objectives' in mdp_dict
        assert 'noise_correlation' in mdp_dict
        assert 'noise_distribution' in mdp_dict
        assert 'dof' in mdp_dict
        assert 'seed' in mdp_dict
        assert 'metadata' in mdp_dict
        
        assert mdp_dict['noise_distribution'] == 'heavy_tailed'
        assert mdp_dict['dof'] == 3

    def test_json_serialization(self):
        """Test MDP metadata can be serialized to JSON."""
        mdp = generate_heavy_tailed_mdp(n_objectives=5, seed=42)
        
        mdp_dict = mdp.to_dict()
        
        # This should not raise
        json_str = json.dumps(mdp_dict)
        assert len(json_str) > 0
        
        # Verify deserialization
        mdp_dict2 = json.loads(json_str)
        assert mdp_dict2['n_objectives'] == mdp_dict['n_objectives']
        assert mdp_dict2['noise_distribution'] == mdp_dict['noise_distribution']

    def test_reproducibility_across_calls(self):
        """Test that multiple calls with same seed produce identical results."""
        seeds = [42, 123, 456, 789]
        n_objectives = 10
        
        for seed in seeds:
            mdp1 = generate_heavy_tailed_mdp(
                n_objectives=n_objectives,
                seed=seed,
                dof=3
            )
            mdp2 = generate_heavy_tailed_mdp(
                n_objectives=n_objectives,
                seed=seed,
                dof=3
            )
            
            # Check metadata
            assert mdp1.to_dict() == mdp2.to_dict()
            
            # Check reward functions
            for r1, r2 in zip(mdp1.reward_functions, mdp2.reward_functions):
                np.testing.assert_array_equal(r1, r2)

    def test_noise_distribution_properties(self):
        """Test that heavy-tailed noise exhibits expected statistical properties."""
        # Generate a large MDP to sample noise statistics
        mdp = generate_heavy_tailed_mdp(
            n_objectives=5,
            n_states=100,
            n_actions=10,
            seed=42,
            dof=3
        )
        
        # Collect all reward values
        all_rewards = []
        for reward_matrix in mdp.reward_functions:
            all_rewards.extend(reward_matrix.flatten())
        
        all_rewards = np.array(all_rewards)
        
        # For heavy-tailed distribution with dof=3, we expect:
        # - Finite mean (should be close to 0 after centering)
        # - Finite variance (dof/(dof-2) = 3 for dof=3)
        # - Higher kurtosis than Gaussian
        
        # Check that mean is reasonable (close to 0 due to standardization)
        mean_val = np.mean(all_rewards)
        assert np.abs(mean_val) < 1.0, f"Mean should be close to 0, got {mean_val}"
        
        # Check that variance is finite and reasonable
        var_val = np.var(all_rewards)
        assert np.isfinite(var_val), "Variance should be finite"
        assert var_val > 0, "Variance should be positive"

    def test_edge_cases(self):
        """Test edge cases and boundary conditions."""
        # Minimum valid objectives
        mdp_min = generate_heavy_tailed_mdp(n_objectives=1, seed=42)
        assert mdp_min.n_objectives == 1
        
        # Minimum valid states
        mdp_min_states = generate_heavy_tailed_mdp(n_objectives=5, n_states=1, seed=42)
        assert mdp_min_states.n_states == 1
        
        # Minimum valid actions
        mdp_min_actions = generate_heavy_tailed_mdp(n_objectives=5, n_actions=1, seed=42)
        assert mdp_min_actions.n_actions == 1

    def test_correlation_zero(self):
        """Test heavy-tailed MDP with zero correlation."""
        mdp = generate_heavy_tailed_mdp(
            n_objectives=5,
            noise_correlation=0.0,
            seed=42
        )
        
        assert mdp.noise_correlation == 0.0
        # With rho=0, objectives should be independent

    def test_correlation_max(self):
        """Test heavy-tailed MDP with maximum correlation."""
        mdp = generate_heavy_tailed_mdp(
            n_objectives=5,
            noise_correlation=1.0,
            seed=42
        )
        
        assert mdp.noise_correlation == 1.0
        # With rho=1, objectives should be perfectly correlated

if __name__ == '__main__':
    pytest.main([__file__, '-v'])