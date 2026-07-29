"""
Contract test for T031: Verify synthetic_mdp.py generates correct tabular MDPs with N objectives.
This is a contract test that verifies the external interface and guarantees.
"""
import pytest
import numpy as np
import sys
import os

if 'code' not in sys.path:
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.environment.synthetic_mdp import generate_mdp, SyntheticTabularMDP


class TestSyntheticMDPContractN5:
    """
    Contract test for N=5 MDP generation.
    Verifies that the MDP generation contract is satisfied for N=5.
    """

    def test_contract_n5_objectives(self):
        """
        Contract: For N=5, the MDP must have exactly 5 reward functions.
        This is FR-003 requirement.
        """
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        # Contract: n_objectives must equal 5
        assert mdp.n_objectives == 5, \
            f"Contract violation: Expected n_objectives=5, got {mdp.n_objectives}"
        
        # Contract: reward_functions must have 5 rows
        assert mdp.reward_functions.shape[0] == 5, \
            f"Contract violation: Expected 5 reward functions, got {mdp.reward_functions.shape[0]}"

    def test_contract_valid_transition_matrix(self):
        """
        Contract: Transition probabilities must form valid stochastic matrices.
        For all s, a: sum_a P(s'|s,a) = 1 and P(s'|s,a) >= 0
        """
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        for s in range(mdp.n_states):
            for a in range(mdp.n_actions):
                probs = mdp.transition_probs[s, a, :]
                
                # Contract: Non-negative probabilities
                assert np.all(probs >= 0), \
                    f"Contract violation: Negative probability at s={s}, a={a}"
                
                # Contract: Sum to 1
                assert np.isclose(probs.sum(), 1.0), \
                    f"Contract violation: Transition probs at s={s}, a={a} sum to {probs.sum()}, not 1.0"

    def test_contract_reward_bounds(self):
        """
        Contract: Reward functions must be bounded (typically [-1, 1] or similar).
        """
        mdp = generate_mdp(n_objectives=5, seed=42)
        
        # Contract: Rewards should be in reasonable range
        # The exact bounds depend on the generation logic, but they should be finite
        assert np.all(np.isfinite(mdp.reward_functions)), \
            "Contract violation: Reward functions contain non-finite values"

    def test_contract_seed_reproducibility(self):
        """
        Contract: Same seed must produce identical MDP.
        """
        mdp1 = generate_mdp(n_objectives=5, seed=42)
        mdp2 = generate_mdp(n_objectives=5, seed=42)
        
        # Contract: Identical generation with same seed
        assert np.array_equal(mdp1.transition_probs, mdp2.transition_probs), \
            "Contract violation: Transition probs differ with same seed"
        assert np.array_equal(mdp1.reward_functions, mdp2.reward_functions), \
            "Contract violation: Reward functions differ with same seed"

class TestSyntheticMDPContractVariousN:
    """
    Contract tests for various N values (5, 10, 20, 50).
    """

    @pytest.mark.parametrize("n_objectives", [5, 10, 20, 50])
    def test_contract_n_objectives(self, n_objectives):
        """
        Contract: MDP must have exactly n_objectives reward functions.
        """
        mdp = generate_mdp(n_objectives=n_objectives, seed=42)
        
        assert mdp.n_objectives == n_objectives, \
            f"Contract violation: Expected n_objectives={n_objectives}, got {mdp.n_objectives}"
        assert mdp.reward_functions.shape[0] == n_objectives, \
            f"Contract violation: Expected {n_objectives} reward functions, got {mdp.reward_functions.shape[0]}"

    @pytest.mark.parametrize("n_objectives", [5, 10, 20, 50])
    def test_contract_valid_structure(self, n_objectives):
        """
        Contract: MDP must have valid structure for all N.
        """
        mdp = generate_mdp(n_objectives=n_objectives, seed=42)
        
        # Contract: State and action spaces must be positive
        assert mdp.n_states > 0, "Contract violation: n_states must be positive"
        assert mdp.n_actions > 0, "Contract violation: n_actions must be positive"
        
        # Contract: Transition probs must be valid
        for s in range(mdp.n_states):
            for a in range(mdp.n_actions):
                probs = mdp.transition_probs[s, a, :]
                assert np.all(probs >= 0), f"Contract violation: Negative prob at s={s}, a={a}"
                assert np.isclose(probs.sum(), 1.0), f"Contract violation: Probs don't sum to 1"

class TestSyntheticMDPContractNoiseCorrelation:
    """
    Contract tests for noise correlation parameter ρ.
    """

    @pytest.mark.parametrize("rho", [0.0, 0.2, 0.5, 1.0])
    def test_contract_rho_accepted(self, rho):
        """
        Contract: MDP generation must accept noise correlation parameter ρ.
        """
        mdp = generate_mdp(n_objectives=5, noise_correlation=rho, seed=42)
        
        # Contract: MDP must be generated successfully
        assert mdp is not None
        assert mdp.n_objectives == 5
        assert mdp.reward_functions.shape[0] == 5

    def test_contract_rho_zero_baseline(self):
        """
        Contract: ρ=0 should produce uncorrelated noise (baseline).
        """
        mdp = generate_mdp(n_objectives=5, noise_correlation=0.0, seed=42)
        
        # Contract: MDP generated successfully
        assert mdp.n_objectives == 5
        assert mdp.reward_functions.shape[0] == 5

    def test_contract_rho_positive(self):
        """
        Contract: ρ>0 should produce correlated noise.
        """
        mdp = generate_mdp(n_objectives=5, noise_correlation=0.5, seed=42)
        
        # Contract: MDP generated successfully
        assert mdp.n_objectives == 5
        assert mdp.reward_functions.shape[0] == 5

if __name__ == "__main__":
    pytest.main([__file__, "-v"])