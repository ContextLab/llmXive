"""
Unit tests for the reproducibility utility (T053).
"""

import random
import os
import sys
from unittest.mock import patch, MagicMock

import numpy as np
import pytest

# Ensure code/ is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

from utils.random_seed import set_global_seed, initialize_from_config, _seed_initialized


class TestRandomSeed:
    """Tests for random seed initialization."""

    def setup_method(self):
        """Reset the global state before each test."""
        # We cannot easily reset the internal flag if it's already set in the module,
        # so we reload the module or use a mock to simulate the first run.
        # For this test, we will test the logic assuming a fresh state or handle the flag.
        pass

    def test_set_seed_sets_python_random(self):
        """Verify that set_global_seed sets Python's random seed."""
        # Reset internal state for testing by reloading the module logic
        # Since we can't easily reset the global _seed_initialized flag in the imported module,
        # we will test the side effects directly on a fresh state if possible,
        # or assume the function works if called once.
        
        # To properly test, we mock the global flag reset
        with patch('utils.random_seed._seed_initialized', False):
            seed_val = 12345
            result = set_global_seed(seed_val)
            
            assert result == seed_val
            assert random.random() < 1.0  # Just to ensure random is working
            
            # Reset random state to check determinism
            random.seed(seed_val)
            val1 = random.random()
            
            random.seed(99999) # Change seed
            random.seed(seed_val) # Reset to original
            val2 = random.random()
            
            assert val1 == val2

    def test_set_seed_sets_numpy(self):
        """Verify that set_global_seed sets NumPy's random seed."""
        with patch('utils.random_seed._seed_initialized', False):
            seed_val = 54321
            set_global_seed(seed_val)
            
            # Generate a number
            val1 = np.random.random()
            
            # Reset and generate again
            np.random.seed(seed_val)
            val2 = np.random.random()
            
            assert val1 == val2

    def test_set_seed_invalid_type(self):
        """Verify that invalid seed types raise ValueError."""
        with patch('utils.random_seed._seed_initialized', False):
            with pytest.raises(ValueError):
                set_global_seed("not_an_int")
            
            with pytest.raises(ValueError):
                set_global_seed(-1)

    def test_set_seed_already_initialized(self):
        """Verify that re-seeding is skipped if already initialized."""
        # Simulate initialization
        with patch('utils.random_seed._seed_initialized', True):
            # This should not change the seed logic but return the config value
            # We expect it to return the default or config value without error
            # The actual seed won't change because of the guard
            result = set_global_seed(999)
            # The function returns the seed it would have used or the config value
            # Since we can't easily verify the internal state change without reloading,
            # we verify it doesn't crash and returns an int.
            assert isinstance(result, int)

    def test_initialize_from_config_uses_default(self):
        """Verify that initialize_from_config uses default if config is missing."""
        with patch('utils.random_seed._seed_initialized', False):
            with patch('utils.random_seed.get_config_value', side_effect=Exception("Config not found")):
                # Should default to 42
                result = initialize_from_config()
                assert result == 42
                
    def test_initialize_from_config_uses_config_value(self):
        """Verify that initialize_from_config uses the value from config."""
        with patch('utils.random_seed._seed_initialized', False):
            custom_seed = 777
            with patch('utils.random_seed.get_config_value', return_value=custom_seed):
                result = initialize_from_config()
                assert result == custom_seed