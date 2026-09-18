"""
Unit tests for seed manager functionality.
Verifies deterministic behavior and seed initialization.
"""
import pytest
import os
import numpy as np
import random
from pathlib import Path
import sys

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code' / 'src'))
from utils.seed_manager import (
    init_seed, get_seed, is_seed_initialized, add_seed_argument,
    validate_seed, reset_seed
)
import argparse

class TestSeedManager:
    """Test suite for seed management utilities."""

    def test_init_seed_sets_random_state(self):
        """Test that init_seed properly sets random states."""
        init_seed(42)
        assert is_seed_initialized()
        assert get_seed() == 42
        
        # Check that random is seeded
        val1 = random.random()
        init_seed(42)
        val2 = random.random()
        assert val1 == val2, "Random state should be deterministic"

    def test_init_seed_sets_numpy_state(self):
        """Test that init_seed properly sets numpy random state."""
        init_seed(123)
        arr1 = np.random.rand(5)
        
        init_seed(123)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2, "NumPy state should be deterministic")

    def test_get_seed_default(self):
        """Test that get_seed returns default if not initialized."""
        reset_seed()
        assert get_seed() == 42

    def test_add_seed_argument(self):
        """Test that add_seed_argument adds --seed to parser."""
        parser = argparse.ArgumentParser()
        parser = add_seed_argument(parser)
        args = parser.parse_args(['--seed', '999'])
        assert args.seed == 999

    def test_add_seed_argument_default(self):
        """Test that --seed defaults to 42."""
        parser = argparse.ArgumentParser()
        parser = add_seed_argument(parser)
        args = parser.parse_args([])
        assert args.seed == 42

    def test_validate_seed(self):
        """Test seed validation."""
        assert validate_seed(42) is True
        assert validate_seed(0) is True
        assert validate_seed(-1) is False
        assert validate_seed("42") is False

    def test_reset_seed(self):
        """Test reset_seed functionality."""
        init_seed(999)
        assert get_seed() == 999
        reset_seed()
        assert get_seed() == 42
        assert not is_seed_initialized()

    def test_environment_variable_set(self):
        """Test that PYTHONHASHSEED is set."""
        init_seed(42)
        assert os.environ.get('PYTHONHASHSEED') == '42'