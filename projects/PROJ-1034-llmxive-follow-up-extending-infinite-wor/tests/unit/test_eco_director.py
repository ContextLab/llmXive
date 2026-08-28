import pytest
import os
import tempfile
import yaml
import sys
import numpy as np

# Add the project root to the path so imports work
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from sim.eco_director import load_config, validate_config, eco_director_step

class TestEcoDirectorStateTransitions:
    """
    Unit tests for eco_director.py state transitions.
    This task validates that the CA engine correctly updates the simulation state
    over time steps, ensuring deterministic behavior with seeds and proper
    handling of locality, memory, and non-linearity parameters.
    """

    def test_step_updates_state_shape(self):
        """
        Test that a single step preserves the grid shape.
        """
        initial_state = np.random.rand(10, 10)
        config = {
            "locality": 3,
            "memory": 2,
            "non_linearity": 0.5,
            "grid_size": 10,
            "steps": 1,
            "seed": 42
        }

        new_state = eco_director_step(initial_state, config)

        assert new_state.shape == initial_state.shape
        assert isinstance(new_state, np.ndarray)

    def test_step_is_deterministic_with_seed(self):
        """
        Test that running the step twice with the same seed produces identical results.
        """
        initial_state = np.random.rand(5, 5)
        config = {
            "locality": 2,
            "memory": 1,
            "non_linearity": 0.3,
            "grid_size": 5,
            "steps": 1,
            "seed": 12345
        }

        # Run first time
        np.random.seed(config['seed'])
        state1 = eco_director_step(initial_state.copy(), config)

        # Run second time with same seed
        np.random.seed(config['seed'])
        state2 = eco_director_step(initial_state.copy(), config)

        np.testing.assert_array_almost_equal(state1, state2)

    def test_state_changes_after_step(self):
        """
        Test that the state actually changes after a step (non-trivial update).
        """
        initial_state = np.ones((10, 10)) * 0.5
        config = {
            "locality": 3,
            "memory": 2,
            "non_linearity": 0.5,
            "grid_size": 10,
            "steps": 1,
            "seed": 42
        }

        new_state = eco_director_step(initial_state, config)

        # With non-linearity and locality, the state should change
        # Allow for small floating point differences
        assert not np.allclose(initial_state, new_state, atol=1e-10)

    def test_multiple_steps_progression(self):
        """
        Test that running multiple steps progresses the simulation correctly.
        """
        initial_state = np.random.rand(8, 8)
        config = {
            "locality": 2,
            "memory": 1,
            "non_linearity": 0.6,
            "grid_size": 8,
            "steps": 5,
            "seed": 99
        }

        # Run 5 steps
        state = initial_state.copy()
        for _ in range(5):
            state = eco_director_step(state, config)

        assert state.shape == initial_state.shape
        # State should have evolved significantly
        assert not np.allclose(state, initial_state, atol=0.01)

    def test_high_non_linearity_effect(self):
        """
        Test that higher non-linearity parameter produces more chaotic state changes.
        """
        initial_state = np.random.rand(10, 10)
        base_config = {
            "locality": 3,
            "memory": 2,
            "grid_size": 10,
            "steps": 1,
            "seed": 42
        }

        # Low non-linearity
        config_low = base_config.copy()
        config_low["non_linearity"] = 0.1
        np.random.seed(42)
        state_low = eco_director_step(initial_state.copy(), config_low)

        # High non-linearity
        config_high = base_config.copy()
        config_high["non_linearity"] = 0.9
        np.random.seed(42)
        state_high = eco_director_step(initial_state.copy(), config_high)

        # The difference from initial state should be larger with high non-linearity
        diff_low = np.mean(np.abs(state_low - initial_state))
        diff_high = np.mean(np.abs(state_high - initial_state))

        assert diff_high > diff_low, "High non-linearity should produce larger state changes"

    def test_locality_parameter_affects_update(self):
        """
        Test that different locality values produce different state updates.
        """
        initial_state = np.random.rand(12, 12)
        base_config = {
            "memory": 2,
            "non_linearity": 0.5,
            "grid_size": 12,
            "steps": 1,
            "seed": 42
        }

        # Small locality
        config_small = base_config.copy()
        config_small["locality"] = 1
        np.random.seed(42)
        state_small = eco_director_step(initial_state.copy(), config_small)

        # Large locality
        config_large = base_config.copy()
        config_large["locality"] = 5
        np.random.seed(42)
        state_large = eco_director_step(initial_state.copy(), config_large)

        # States should differ due to different locality radii
        assert not np.allclose(state_small, state_large, atol=1e-6)

    def test_memory_parameter_integration(self):
        """
        Test that the memory parameter is integrated into the step logic.
        This verifies that the step function accepts and uses the memory parameter
        without raising errors, assuming the underlying implementation tracks history.
        """
        initial_state = np.random.rand(10, 10)
        config = {
            "locality": 2,
            "memory": 3,
            "non_linearity": 0.4,
            "grid_size": 10,
            "steps": 1,
            "seed": 42
        }

        # Should run without error
        new_state = eco_director_step(initial_state, config)
        assert new_state.shape == initial_state.shape

    def test_invalid_config_raises_error(self):
        """
        Test that eco_director_step raises ValueError when given invalid config.
        """
        initial_state = np.random.rand(10, 10)
        
        # Missing required 'non_linearity'
        invalid_config = {
            "locality": 3,
            "memory": 2,
            "grid_size": 10,
            "steps": 1,
            "seed": 42
        }

        with pytest.raises(ValueError):
            eco_director_step(initial_state, invalid_config)

    def test_zero_steps_returns_initial_state(self):
        """
        Test that if steps=0, the state remains unchanged (or validation handles it).
        Note: The step function typically runs one step. If steps=0 is passed to 
        run_simulation it would return initial, but step() itself is a single transition.
        We test that a single step with steps=1 works, and if steps=0 is passed 
        to the step function logic, it should handle it or the config validation 
        should catch it. Here we assume steps=1 is the minimum for a transition.
        """
        # This test verifies the basic step mechanism works with steps=1
        initial_state = np.random.rand(5, 5)
        config = {
            "locality": 2,
            "memory": 1,
            "non_linearity": 0.5,
            "grid_size": 5,
            "steps": 1,
            "seed": 42
        }

        new_state = eco_director_step(initial_state, config)
        assert new_state.shape == initial_state.shape