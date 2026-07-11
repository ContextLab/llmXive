"""
Unit tests for seed management functionality.
"""

import random
import pytest
import numpy as np

from utils.seeds import (
    set_global_seed,
    get_seed_from_string,
    seed_generator,
    SeedManager,
    validate_seed
)


class TestSetGlobalSeed:
    """Tests for set_global_seed function."""

    def test_set_seed_with_valid_integer(self):
        """Test setting seed with a valid integer."""
        seed_value = 42
        result = set_global_seed(seed_value)
        assert result == seed_value

        # Verify numpy and random are seeded
        arr1 = np.random.rand(5)
        random_val1 = random.random()

        set_global_seed(seed_value)
        arr2 = np.random.rand(5)
        random_val2 = random.random()

        np.testing.assert_array_equal(arr1, arr2)
        assert random_val1 == random_val2

    def test_set_seed_with_none_uses_default(self):
        """Test that None uses DEFAULT_SEED."""
        from utils.config import DEFAULT_SEED
        result = set_global_seed(None)
        assert result == DEFAULT_SEED

    def test_set_seed_with_negative_raises_error(self):
        """Test that negative seeds raise ValueError."""
        with pytest.raises(ValueError):
            set_global_seed(-1)

    def test_set_seed_with_float_raises_error(self):
        """Test that float seeds raise ValueError."""
        with pytest.raises(ValueError):
            set_global_seed(42.5)


class TestGetSeedFromString:
    """Tests for get_seed_from_string function."""

    def test_deterministic_hashing(self):
        """Test that the same string always produces the same seed."""
        seed_str = "test_seed_string"
        seed1 = get_seed_from_string(seed_str)
        seed2 = get_seed_from_string(seed_str)
        assert seed1 == seed2

    def test_different_strings_different_seeds(self):
        """Test that different strings produce different seeds."""
        seed1 = get_seed_from_string("string_one")
        seed2 = get_seed_from_string("string_two")
        assert seed1 != seed2

    def test_empty_string_raises_error(self):
        """Test that empty string raises ValueError."""
        with pytest.raises(ValueError):
            get_seed_from_string("")

    def test_seed_range(self):
        """Test that seeds are in valid range."""
        seed = get_seed_from_string("any_string")
        assert 0 <= seed < 2**32


class TestSeedGenerator:
    """Tests for seed_generator function."""

    def test_derived_seed_deterministic(self):
        """Test that derived seeds are deterministic."""
        base = 100
        offset = 5
        seed1 = seed_generator(base, offset)
        seed2 = seed_generator(base, offset)
        assert seed1 == seed2

    def test_different_offsets_different_seeds(self):
        """Test that different offsets produce different seeds."""
        base = 100
        seed1 = seed_generator(base, 0)
        seed2 = seed_generator(base, 1)
        assert seed1 != seed2

    def test_negative_offset_raises_error(self):
        """Test that negative offset raises ValueError."""
        with pytest.raises(ValueError):
            seed_generator(100, -1)


class TestSeedManager:
    """Tests for SeedManager context manager."""

    def test_seed_restored_after_context(self):
        """Test that seed state is restored after context exit."""
        # Set initial seed
        set_global_seed(123)
        initial_arr = np.random.rand(5)
        initial_random = random.random()

        # Use context manager with different seed
        with SeedManager(456):
            context_arr = np.random.rand(5)
            context_random = random.random()

            # Values should be different from initial
            assert not np.array_equal(initial_arr, context_arr)

        # After context, values should match initial
        after_arr = np.random.rand(5)
        after_random = random.random()

        np.testing.assert_array_equal(initial_arr, after_arr)
        assert initial_random == after_random

    def test_context_uses_provided_seed(self):
        """Test that context manager uses the provided seed."""
        set_global_seed(100)

        with SeedManager(999):
            arr = np.random.rand(5)
            random_val = random.random()

        # Reset to 999 and verify same values
        set_global_seed(999)
        arr2 = np.random.rand(5)
        random_val2 = random.random()

        np.testing.assert_array_equal(arr, arr2)
        assert random_val == random_val2


class TestValidateSeed:
    """Tests for validate_seed function."""

    def test_valid_integer_seed(self):
        """Test validation of valid integer seeds."""
        assert validate_seed(0) is True
        assert validate_seed(42) is True
        assert validate_seed(2**32 - 1) is True

    def test_invalid_seeds(self):
        """Test validation of invalid seeds."""
        assert validate_seed(-1) is False
        assert validate_seed(3.14) is False
        assert validate_seed("42") is False
        assert validate_seed(None) is False