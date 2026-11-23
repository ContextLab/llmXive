import pytest
import numpy as np
import sys
import os

# Ensure src is in path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from src.simulation.synthetic_mdp import generate_tabular_mdp, generate_noise_correlated

class TestMDPGenerationDeterminism:
    """
    Verify that MDP generation is deterministic given the same seed.
    Tests T015 requirement: deterministic seeded random state management.
    """

    def test_same_seed_produces_identical_mdp(self):
        """
        Generating an MDP twice with the same seed must produce identical
        transition matrices, reward matrices, and initial state distributions.
        """
        n_states = 10
        n_actions = 4
        n_objectives = 5
        seed = 42

        # First generation
        mdp_1 = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed
        )

        # Second generation
        mdp_2 = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed
        )

        # Verify structural equality
        assert mdp_1['n_states'] == mdp_2['n_states']
        assert mdp_1['n_actions'] == mdp_2['n_actions']
        assert mdp_1['n_objectives'] == mdp_2['n_objectives']

        # Verify numerical equality of arrays
        assert np.array_equal(mdp_1['P'], mdp_2['P'])
        assert np.array_equal(mdp_1['R'], mdp_2['R'])
        assert np.array_equal(mdp_1['initial_state_dist'], mdp_2['initial_state_dist'])

    def test_different_seed_produces_different_mdp(self):
        """
        Generating an MDP with different seeds should produce different
        transition and reward matrices (with high probability).
        """
        n_states = 10
        n_actions = 4
        n_objectives = 5
        seed_1 = 42
        seed_2 = 123

        mdp_1 = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed_1
        )

        mdp_2 = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed_2
        )

        # While collisions are theoretically possible, they are astronomically unlikely
        # for random matrices of this size. We assert they are different.
        assert not np.array_equal(mdp_1['P'], mdp_2['P']) or \
               not np.array_equal(mdp_1['R'], mdp_2['R'])


class TestMDPObjectiveCounts:
    """
    Verify that MDP generation correctly sets the number of objectives.
    Tests T015 requirement: tabular MDP generation with N objectives.
    """

    @pytest.mark.parametrize("n_objectives", [1, 5, 10, 50])
    def test_objective_count_matches_input(self, n_objectives):
        """
        The generated MDP must have a reward tensor with shape
        (n_states, n_actions, n_objectives).
        """
        n_states = 5
        n_actions = 2
        seed = 42

        mdp = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed
        )

        assert mdp['n_objectives'] == n_objectives
        assert mdp['R'].shape == (n_states, n_actions, n_objectives)
        assert mdp['R'].shape[2] == n_objectives

    def test_reward_values_within_expected_range(self):
        """
        Verify that generated rewards are within expected bounds (typically [-1, 1]
        or similar normalized range depending on implementation).
        """
        n_states = 5
        n_actions = 2
        n_objectives = 3
        seed = 42

        mdp = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed
        )

        # Check that rewards are finite and reasonably bounded
        assert np.all(np.isfinite(mdp['R']))
        # Assuming normalized rewards in [-1, 1] or similar
        # If implementation uses different scaling, adjust this check
        assert np.min(mdp['R']) >= -10.0
        assert np.max(mdp['R']) <= 10.0


class TestNoiseCorrelation:
    """
    Verify that noise correlation parameter rho is correctly handled.
    Tests T015 requirement: explicit support for noise correlation parameter ρ.
    """

    def test_independent_noise_generates_uncorrelated_samples(self):
        """
        When rho=0, noise samples should be effectively uncorrelated.
        """
        n_samples = 10000
        n_objectives = 5
        rho = 0.0
        seed = 42

        noise_1, noise_2 = generate_noise_correlated(
            n_samples=n_samples,
            n_objectives=n_objectives,
            rho=rho,
            seed=seed
        )

        # Calculate correlation between objectives
        correlations = np.corrcoef(noise_1.T, noise_2.T)
        
        # Off-diagonal elements (between different objectives) should be near 0
        # We check a sample of off-diagonal correlations
        for i in range(n_objectives):
            for j in range(i + 1, n_objectives):
                corr_val = np.corrcoef(noise_1[:, i], noise_1[:, j])[0, 1]
                # Allow some tolerance due to finite sample size
                assert abs(corr_val) < 0.1, f"Correlation between objectives {i} and {j} is too high: {corr_val}"

    def test_positive_noise_correlation_increases_correlation(self):
        """
        When rho > 0, noise samples should show positive correlation.
        """
        n_samples = 10000
        n_objectives = 5
        rho = 0.5
        seed = 42

        noise_1, noise_2 = generate_noise_correlated(
            n_samples=n_samples,
            n_objectives=n_objectives,
            rho=rho,
            seed=seed
        )

        # Calculate correlation between objectives
        correlations = np.corrcoef(noise_1.T, noise_2.T)
        
        # Check that correlations are significantly positive on average
        avg_corr = 0.0
        count = 0
        for i in range(n_objectives):
            for j in range(i + 1, n_objectives):
                corr_val = np.corrcoef(noise_1[:, i], noise_1[:, j])[0, 1]
                avg_corr += corr_val
                count += 1

        avg_corr /= count
        # With rho=0.5 and large sample, we expect positive correlation
        assert avg_corr > 0.2, f"Average correlation too low for rho=0.5: {avg_corr}"

    def test_rho_values_in_valid_range(self):
        """
        Test that the function accepts valid rho values: 0, 0.2, 0.5.
        """
        valid_rhos = [0.0, 0.2, 0.5]
        
        for rho in valid_rhos:
            noise_1, noise_2 = generate_noise_correlated(
                n_samples=100,
                n_objectives=3,
                rho=rho,
                seed=42
            )
            assert noise_1.shape == (100, 3)
            assert noise_2.shape == (100, 3)
            assert np.all(np.isfinite(noise_1))
            assert np.all(np.isfinite(noise_2))

    def test_invalid_rho_raises_error(self):
        """
        Test that invalid rho values raise an appropriate error.
        """
        with pytest.raises(ValueError):
            generate_noise_correlated(
                n_samples=100,
                n_objectives=3,
                rho=1.5,  # Invalid: > 1
                seed=42
            )

        with pytest.raises(ValueError):
            generate_noise_correlated(
                n_samples=100,
                n_objectives=3,
                rho=-0.5,  # Invalid: < 0
                seed=42
            )

class TestMDPStructure:
    """
    Verify the structural integrity of generated MDPs.
    """

    def test_transition_matrix_stochasticity(self):
        """
        Transition probabilities must sum to 1 for each state-action pair.
        """
        n_states = 10
        n_actions = 4
        n_objectives = 5
        seed = 42

        mdp = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed
        )

        # P shape: (n_states, n_actions, n_states)
        # Sum over the last axis (next state) should be 1
        transition_sums = np.sum(mdp['P'], axis=2)
        assert np.allclose(transition_sums, 1.0), "Transition probabilities do not sum to 1"

    def test_initial_state_distribution_valid(self):
        """
        Initial state distribution must be a valid probability distribution.
        """
        n_states = 10
        n_actions = 4
        n_objectives = 5
        seed = 42

        mdp = generate_tabular_mdp(
            n_states=n_states,
            n_actions=n_actions,
            n_objectives=n_objectives,
            seed=seed
        )

        initial_dist = mdp['initial_state_dist']
        
        # Must sum to 1
        assert np.isclose(np.sum(initial_dist), 1.0), "Initial state distribution does not sum to 1"
        
        # All probabilities must be non-negative
        assert np.all(initial_dist >= 0), "Initial state distribution contains negative values"
        
        # Must have correct shape
        assert initial_dist.shape == (n_states,), f"Initial state distribution shape mismatch: {initial_dist.shape}"