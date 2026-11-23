"""
Unit tests for the configuration utilities in utils.config.
"""
import os
import random
import numpy as np
import pytest
from pathlib import Path

# Import the functions to test
from utils.config import set_seed, get_project_root, get_data_dir, get_code_dir


class TestSetSeed:
    """Tests for the set_seed function."""

    def test_set_seed_changes_random_state(self):
        """Verify that set_seed changes the random state deterministically."""
        seed_value = 42
        
        # Set seed
        set_seed(seed_value)
        rand_val_1 = random.random()
        np_val_1 = np.random.rand()
        
        # Reset seed to the same value
        set_seed(seed_value)
        rand_val_2 = random.random()
        np_val_2 = np.random.rand()
        
        # Values should be identical
        assert rand_val_1 == rand_val_2
        assert np_val_1 == np_val_2

    def test_set_seed_sets_environment_variable(self):
        """Verify that set_seed sets the PYTHONHASHSEED environment variable."""
        seed_value = 12345
        set_seed(seed_value)
        
        assert os.environ.get("PYTHONHASHSEED") == str(seed_value)

    def test_set_seed_different_seeds_produce_different_results(self):
        """Verify that different seeds produce different random sequences."""
        set_seed(42)
        val_42 = random.random()
        
        set_seed(123)
        val_123 = random.random()
        
        assert val_42 != val_123

class TestPathFunctions:
    """Tests for path utility functions."""

    def test_get_project_root(self):
        """Verify that get_project_root returns a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.exists()

    def test_get_data_dir(self):
        """Verify that get_data_dir returns the correct path relative to root."""
        root = get_project_root()
        data_dir = get_data_dir()
        expected = root / "data"
        assert data_dir == expected

    def test_get_code_dir(self):
        """Verify that get_code_dir returns the correct path relative to root."""
        root = get_project_root()
        code_dir = get_code_dir()
        expected = root / "code"
        assert code_dir == expected