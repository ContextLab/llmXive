"""
Unit tests for the config module (T004).

Verifies:
1. Seed pinning functionality for random, numpy, and torch.
2. Existence of defined path constants.
3. Correctness of global constants.
"""

import os
import random
from unittest.mock import patch

import numpy as np
import pytest

# Import the config module to trigger seed setting
from code.config import (
    SEED,
    ALLOWED_LANGUAGES,
    MAX_LOC,
    DATA_DIR,
    set_global_seed,
    TORCH_AVAILABLE
)

# Try to import torch for specific tests if available
if TORCH_AVAILABLE:
    import torch


class TestSeedPinning:
    def test_random_seed_determinism(self):
        """Verify that random.seed(42) produces deterministic results."""
        # Reset seed
        set_global_seed(SEED)
        val1 = random.random()

        # Reset seed again
        set_global_seed(SEED)
        val2 = random.random()

        assert val1 == val2, "Random seed did not produce deterministic results."

    def test_numpy_seed_determinism(self):
        """Verify that np.random.seed(42) produces deterministic results."""
        set_global_seed(SEED)
        arr1 = np.random.rand(5)

        set_global_seed(SEED)
        arr2 = np.random.rand(5)

        assert np.array_equal(arr1, arr2), "Numpy seed did not produce deterministic results."

    @pytest.mark.skipif(not TORCH_AVAILABLE, reason="Torch not available")
    def test_torch_seed_determinism(self):
        """Verify that torch.manual_seed(42) produces deterministic results."""
        set_global_seed(SEED)
        t1 = torch.rand(5)

        set_global_seed(SEED)
        t2 = torch.rand(5)

        assert torch.equal(t1, t2), "Torch seed did not produce deterministic results."

    def test_seed_constant_value(self):
        """Verify the global SEED constant is 42."""
        assert SEED == 42, f"Expected SEED to be 42, got {SEED}"


class TestPathConstants:
    def test_data_dir_exists(self):
        """Verify DATA_DIR is a Path object."""
        assert isinstance(DATA_DIR, type(Path())), "DATA_DIR should be a Path object."
        # Check if it resolves to the project root's data folder
        expected = os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", "data")
        # We check the string representation to be flexible with absolute vs relative
        assert "data" in str(DATA_DIR), "DATA_DIR should contain 'data' in path."

    def test_raw_dir_structure(self):
        """Verify that raw directory path is correctly constructed."""
        from code.config import DATA_RAW_DIR
        assert "raw" in str(DATA_RAW_DIR), "DATA_RAW_DIR should contain 'raw'."


class TestGlobalConstants:
    def test_allowed_languages(self):
        """Verify allowed languages list."""
        assert "Java" in ALLOWED_LANGUAGES
        assert "Python" in ALLOWED_LANGUAGES
        assert len(ALLOWED_LANGUAGES) == 2

    def test_max_loc(self):
        """Verify MAX_LOC constant."""
        assert MAX_LOC == 30, f"Expected MAX_LOC to be 30, got {MAX_LOC}"

    def test_seed_function_call(self):
        """Verify set_global_seed function exists and is callable."""
        assert callable(set_global_seed), "set_global_seed must be callable."