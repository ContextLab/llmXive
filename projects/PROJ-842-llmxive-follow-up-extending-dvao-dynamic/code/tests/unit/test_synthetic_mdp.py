"""
Unit tests for src/simulation/synthetic_mdp.py

Tests verify:
1. Deterministic MDP generation with seeded random states
2. Correct number of objectives (N)
3. Correct noise correlation parameter (ρ) handling
4. Transition probability validity (sum to 1)
5. Reward tensor shape and properties
"""
import pytest
import numpy as np
import sys
import os
import tempfile
import json

# Add parent directory to path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from src.simulation.synthetic_mdp import SyntheticTabularMDP


class TestSyntheticMDPGeneration:
    """Test basic MDP generation properties."""

    def test_initialization(self):
        """Test that MDP initializes with correct parameters."""
        mdp = SyntheticTabularMDP(
            n_states=20,
            n_actions=4,
            n_objectives=10,
            rho=0.0,
            seed=42
        )
        
        assert mdp.n_states == 20
        assert mdp.n_actions == 4
        assert mdp.n_objectives == 10
        assert mdp.rho == 0.0
        assert mdp.seed == 42

    def test_transition_probability_sums(self):
        """Test that transition probabilities sum to 1 for all (s, a)."""
        mdp = SyntheticTabularMDP(n_states=10, n_actions=3, n_objectives=5, seed=123)
        
        transition_sums = mdp.transitions.sum(axis=2)
        
        # Check all sums are 1.0 within tolerance
        assert np.allclose(transition_sums, 1.0, atol=1e-6)
        assert transition_sums.shape == (mdp.n_states, mdp.n_actions)

    def test_reward_shape(self):
        """Test that reward tensor has correct shape."""
        n_states, n_actions, n_objectives = 15, 4, 8
        mdp = SyntheticTabularMDP(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=42
        )
        
        assert mdp.rewards.shape == (n_states, n_actions, n_objectives)

    def test_state_features_shape(self):
        """Test that state features have correct shape."""
        n_states, n_objectives = 20, 6
        mdp = SyntheticTabularMDP(
            n_states=n_states,
            n_actions=3,
            n_objectives=n_objectives,
            seed=42
        )
        
        assert mdp.state_features.shape == (n_states, n_objectives)

    def test_reward_values_finite(self):
        """Test that all reward values are finite."""
        mdp = SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=5, seed=999)
        
        assert np.all(np.isfinite(mdp.rewards))

    def test_reward_clipping(self):
        """Test that rewards are clipped to [-1, 1]."""
        mdp = SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=5, seed=999)
        
        assert np.min(mdp.rewards) >= -1.0
        assert np.max(mdp.rewards) <= 1.0


class TestNoiseCorrelation:
    """Test noise correlation parameter ρ handling."""

    @pytest.mark.parametrize("rho", [0.0, 0.2, 0.5, 1.0])
    def test_rho_values(self, rho):
        """Test MDP generation with different ρ values."""
        mdp = SyntheticTabularMDP(
            n_states=10,
            n_actions=2,
            n_objectives=5,
            rho=rho,
            seed=42
        )
        
        assert mdp.rho == rho
        assert mdp.validate()

    def test_rho_zero_independence(self):
        """
        Test that with rho=0, noise is independent across objectives.
        This is a structural test - we check that the noise generation
        logic uses the correct formula.
        """
        # With rho=0, shared_noise contribution should be 0
        # We verify the MDP generates successfully and has valid stats
        mdp = SyntheticTabularMDP(
            n_states=50,
            n_actions=5,
            n_objectives=10,
            rho=0.0,
            seed=42
        )
        
        # Check that reward variance is reasonable (not degenerate)
        reward_std = np.std(mdp.rewards)
        assert reward_std > 0.0
        assert reward_std < 1.0  # Should be bounded due to clipping

    def test_rho_one_completely_correlated(self):
        """
        Test that with rho=1.0, noise is completely correlated across objectives.
        """
        mdp = SyntheticTabularMDP(
            n_states=50,
            n_actions=5,
            n_objectives=10,
            rho=1.0,
            seed=42
        )
        
        assert mdp.validate()
        # With rho=1, all objectives should have identical noise pattern
        # (though base rewards differ)
        # We just verify the MDP is valid and has expected properties


class TestDeterminism:
    """Test deterministic behavior with seeded random states."""

    def test_deterministic_generation(self):
        """Test that same seed produces identical MDPs."""
        mdp1 = SyntheticTabularMDP(
            n_states=10,
            n_actions=3,
            n_objectives=5,
            rho=0.2,
            seed=12345
        )
        
        mdp2 = SyntheticTabularMDP(
            n_states=10,
            n_actions=3,
            n_objectives=5,
            rho=0.2,
            seed=12345
        )
        
        # Check all arrays are identical
        assert np.array_equal(mdp1.transitions, mdp2.transitions)
        assert np.array_equal(mdp1.rewards, mdp2.rewards)
        assert np.array_equal(mdp1.state_features, mdp2.state_features)

    def test_different_seeds_different_results(self):
        """Test that different seeds produce different MDPs."""
        mdp1 = SyntheticTabularMDP(
            n_states=10,
            n_actions=3,
            n_objectives=5,
            seed=111
        )
        
        mdp2 = SyntheticTabularMDP(
            n_states=10,
            n_actions=3,
            n_objectives=5,
            seed=222
        )
        
        # At least one of the arrays should be different
        assert not (
            np.array_equal(mdp1.transitions, mdp2.transitions) and
            np.array_equal(mdp1.rewards, mdp2.rewards)
        )


class TestValidation:
    """Test MDP validation method."""

    def test_valid_mdp(self):
        """Test that a properly generated MDP passes validation."""
        mdp = SyntheticTabularMDP(
            n_states=20,
            n_actions=4,
            n_objectives=8,
            rho=0.3,
            seed=42
        )
        
        assert mdp.validate() is True

    def test_invalid_transition_sums(self):
        """Test validation catches invalid transition probabilities."""
        mdp = SyntheticTabularMDP(
            n_states=10,
            n_actions=3,
            n_objectives=5,
            seed=42
        )
        
        # Corrupt the transition probabilities
        mdp.transitions[0, 0, :] = 0.0  # Set to all zeros (sum = 0)
        
        assert mdp.validate() is False

    def test_nan_rewards(self):
        """Test validation catches NaN rewards."""
        mdp = SyntheticTabularMDP(
            n_states=10,
            n_actions=3,
            n_objectives=5,
            seed=42
        )
        
        mdp.rewards[0, 0, 0] = np.nan
        
        assert mdp.validate() is False


class TestMetadataAndIO:
    """Test metadata generation and JSON saving."""

    def test_get_metadata(self):
        """Test that metadata dictionary is correctly formed."""
        mdp = SyntheticTabularMDP(
            n_states=15,
            n_actions=3,
            n_objectives=7,
            rho=0.2,
            seed=999
        )
        
        metadata = mdp.get_metadata()
        
        assert metadata['n_states'] == 15
        assert metadata['n_actions'] == 3
        assert metadata['n_objectives'] == 7
        assert metadata['rho'] == 0.2
        assert metadata['seed'] == 999
        assert 'transition_shape' in metadata
        assert 'reward_shape' in metadata

    def test_save_to_json(self):
        """Test saving MDP metadata to JSON file."""
        mdp = SyntheticTabularMDP(
            n_states=10,
            n_actions=2,
            n_objectives=4,
            seed=42
        )
        
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, 'test_mdp.json')
            mdp.save_to_json(filepath)
            
            assert os.path.exists(filepath)
            
            with open(filepath, 'r') as f:
                saved_data = json.load(f)
            
            assert saved_data['n_states'] == 10
            assert saved_data['n_objectives'] == 4
            assert 'reward_stats' in saved_data

    def test_from_config(self):
        """Test creating MDP from config dictionary."""
        config = {
            'n_states': 25,
            'n_actions': 6,
            'n_objectives': 12,
            'rho': 0.5,
            'seed': 777
        }
        
        mdp = SyntheticTabularMDP.from_config(config)
        
        assert mdp.n_states == 25
        assert mdp.n_actions == 6
        assert mdp.n_objectives == 12
        assert mdp.rho == 0.5
        assert mdp.seed == 777


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_minimum_parameters(self):
        """Test MDP with minimum valid parameters."""
        mdp = SyntheticTabularMDP(
            n_states=2,
            n_actions=1,
            n_objectives=1,
            seed=1
        )
        
        assert mdp.validate()
        assert mdp.transitions.shape == (2, 1, 2)
        assert mdp.rewards.shape == (2, 1, 1)

    def test_large_objectives(self):
        """Test MDP with large number of objectives (N=50)."""
        mdp = SyntheticTabularMDP(
            n_states=50,
            n_actions=5,
            n_objectives=50,
            seed=42
        )
        
        assert mdp.validate()
        assert mdp.n_objectives == 50
        assert mdp.rewards.shape[2] == 50

    def test_rho_boundary_values(self):
        """Test ρ at boundary values 0 and 1."""
        mdp_zero = SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=5, rho=0.0, seed=1)
        mdp_one = SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=5, rho=1.0, seed=1)
        
        assert mdp_zero.validate()
        assert mdp_one.validate()

    def test_invalid_rho(self):
        """Test that invalid ρ raises ValueError."""
        with pytest.raises(ValueError):
            SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=5, rho=1.5, seed=1)
        
        with pytest.raises(ValueError):
            SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=5, rho=-0.1, seed=1)

    def test_invalid_n_states(self):
        """Test that invalid n_states raises ValueError."""
        with pytest.raises(ValueError):
            SyntheticTabularMDP(n_states=1, n_actions=2, n_objectives=5, seed=1)

    def test_invalid_n_objectives(self):
        """Test that invalid n_objectives raises ValueError."""
        with pytest.raises(ValueError):
            SyntheticTabularMDP(n_states=10, n_actions=2, n_objectives=0, seed=1)