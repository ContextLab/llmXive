"""
Tests for the random seed fixing infrastructure.
"""

import os
import random
import unittest
from unittest.mock import patch

import numpy as np

# Import the module under test
from utils.seed import (
    DEFAULT_SEED,
    SEED_ENV_VAR,
    get_seed_from_env,
    set_seed,
    seeded_generator,
    seeded_numpy_generator,
)


class TestSeedUtils(unittest.TestCase):
    """Test cases for seed utility functions."""

    def setUp(self):
        """Reset environment before each test."""
        # Save original environment
        self._original_seed_env = os.environ.get(SEED_ENV_VAR)
        # Clean environment
        if SEED_ENV_VAR in os.environ:
            del os.environ[SEED_ENV_VAR]

    def tearDown(self):
        """Restore original environment after each test."""
        # Restore original environment
        if self._original_seed_env is not None:
            os.environ[SEED_ENV_VAR] = self._original_seed_env
        elif SEED_ENV_VAR in os.environ:
            del os.environ[SEED_ENV_VAR]

    def test_default_seed_from_env_when_not_set(self):
        """Test that DEFAULT_SEED is returned when env var is not set."""
        seed = get_seed_from_env()
        self.assertEqual(seed, DEFAULT_SEED)

    def test_seed_from_env_when_set(self):
        """Test that the correct seed is returned from environment."""
        test_seed = 12345
        os.environ[SEED_ENV_VAR] = str(test_seed)
        seed = get_seed_from_env()
        self.assertEqual(seed, test_seed)

    def test_invalid_seed_from_env(self):
        """Test that invalid seed in environment raises ValueError."""
        os.environ[SEED_ENV_VAR] = "not_a_number"
        with self.assertRaises(ValueError):
            get_seed_from_env()

    def test_set_seed_default(self):
        """Test setting seed with default value."""
        result = set_seed()
        self.assertEqual(result, DEFAULT_SEED)
        self.assertEqual(os.environ.get(SEED_ENV_VAR), str(DEFAULT_SEED))

    def test_set_seed_custom(self):
        """Test setting seed with custom value."""
        test_seed = 999
        result = set_seed(test_seed)
        self.assertEqual(result, test_seed)
        self.assertEqual(os.environ.get(SEED_ENV_VAR), str(test_seed))

    def test_set_seed_invalid(self):
        """Test that invalid seed raises ValueError."""
        with self.assertRaises(ValueError):
            set_seed(-1)
        with self.assertRaises(ValueError):
            set_seed("not_an_int")  # type: ignore

    def test_reproducibility_python_random(self):
        """Test that Python random module produces reproducible results."""
        seed = 42
        set_seed(seed)
        values1 = [random.random() for _ in range(5)]

        set_seed(seed)
        values2 = [random.random() for _ in range(5)]

        self.assertEqual(values1, values2)

    def test_reproducibility_numpy_random(self):
        """Test that NumPy random module produces reproducible results."""
        seed = 42
        set_seed(seed)
        values1 = [np.random.random() for _ in range(5)]

        set_seed(seed)
        values2 = [np.random.random() for _ in range(5)]

        self.assertEqual(values1, values2)

    def test_seeded_generator_isolation(self):
        """Test that seeded_generator doesn't affect global state."""
        # Set global seed
        set_seed(100)
        global_val1 = random.random()

        # Create isolated generator
        rng = seeded_generator(200)
        isolated_val = rng.random()

        # Global state should be unchanged
        global_val2 = random.random()

        # Reset and verify
        set_seed(100)
        self.assertEqual(random.random(), global_val1)
        # The second global value should be different from isolated
        self.assertNotEqual(isolated_val, global_val2)

    def test_seeded_numpy_generator_isolation(self):
        """Test that seeded_numpy_generator doesn't affect global state."""
        # Set global seed
        set_seed(100)
        global_val1 = np.random.random()

        # Create isolated generator
        rng = seeded_numpy_generator(200)
        isolated_val = rng.random()

        # Global state should be unchanged
        global_val2 = np.random.random()

        # Reset and verify
        set_seed(100)
        self.assertEqual(np.random.random(), global_val1)
        # The second global value should be different from isolated
        self.assertNotEqual(isolated_val, global_val2)

    def test_seeded_generator_custom_seed(self):
        """Test creating a seeded generator with custom seed."""
        rng = seeded_generator(555)
        val1 = rng.random()

        rng2 = seeded_generator(555)
        val2 = rng2.random()

        self.assertEqual(val1, val2)

    def test_seeded_numpy_generator_custom_seed(self):
        """Test creating a seeded NumPy generator with custom seed."""
        rng = seeded_numpy_generator(555)
        val1 = rng.random()

        rng2 = seeded_numpy_generator(555)
        val2 = rng2.random()

        self.assertEqual(val1, val2)


if __name__ == "__main__":
    unittest.main()