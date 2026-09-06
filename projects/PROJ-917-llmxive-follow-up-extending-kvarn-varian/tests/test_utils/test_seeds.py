"""
Unit tests for global random seed management (T008).
"""

import random
import numpy as np
import pytest
import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.seeds import (
    set_global_seed,
    get_seed,
    ensure_seed_set,
    reset_seed,
    get_seed_info
)


class TestSeedManagement:
    """Tests for the seed management functions."""

    def test_set_global_seed_sets_all_libraries(self):
        """Test that set_global_seed sets seeds for random, numpy, and torch."""
        seed = 12345
        set_global_seed(seed)

        # Check internal state
        assert get_seed() == seed

        # Check Python random
        val1 = random.random()
        set_global_seed(seed)
        val2 = random.random()
        assert val1 == val2

        # Check NumPy
        arr1 = np.random.rand(5)
        set_global_seed(seed)
        arr2 = np.random.rand(5)
        np.testing.assert_array_equal(arr1, arr2)

        # Check torch if available
        try:
            import torch
            set_global_seed(seed)
            t1 = torch.rand(5)
            set_global_seed(seed)
            t2 = torch.rand(5)
            assert torch.equal(t1, t2)
        except ImportError:
            pass  # Torch not available, skip torch-specific checks

    def test_seed_type_validation(self):
        """Test that non-integer seeds raise TypeError."""
        with pytest.raises(TypeError):
            set_global_seed("42")
        with pytest.raises(TypeError):
            set_global_seed(42.5)

    def test_get_seed_before_set(self):
        """Test that get_seed returns None before any seed is set."""
        reset_seed()
        assert get_seed() is None

    def test_ensure_seed_set_uses_default(self):
        """Test that ensure_seed_set sets a default if none exists."""
        reset_seed()
        default_seed = 99999
        result = ensure_seed_set(default_seed)
        assert result == default_seed
        assert get_seed() == default_seed

    def test_ensure_seed_set_preserves_existing(self):
        """Test that ensure_seed_set doesn't overwrite an existing seed."""
        existing_seed = 11111
        set_global_seed(existing_seed)
        different_default = 22222
        result = ensure_seed_set(different_default)
        assert result == existing_seed
        assert get_seed() == existing_seed

    def test_reset_seed_clears_state(self):
        """Test that reset_seed clears the global state."""
        set_global_seed(55555)
        assert get_seed() == 55555
        reset_seed()
        assert get_seed() is None

    def test_reproducibility_with_same_seed(self):
        """Test that running the same sequence twice with same seed produces same results."""
        seed = 42
        
        # First run
        set_global_seed(seed)
        seq1 = [random.random(), np.random.rand(), np.random.rand(3).tolist()]
        
        # Second run
        set_global_seed(seed)
        seq2 = [random.random(), np.random.rand(), np.random.rand(3).tolist()]
        
        assert seq1 == seq2

    def test_different_seeds_produce_different_results(self):
        """Test that different seeds produce different random sequences."""
        set_global_seed(100)
        seq1 = [random.random(), np.random.rand()]
        
        set_global_seed(200)
        seq2 = [random.random(), np.random.rand()]
        
        # They should be different (with extremely high probability)
        assert seq1 != seq2

    def test_get_seed_info_structure(self):
        """Test that get_seed_info returns expected structure."""
        reset_seed()
        info = get_seed_info()
        assert "seed" in info
        assert "is_set" in info
        assert "torch_available" in info
        assert info["seed"] is None
        assert info["is_set"] is False

        set_global_seed(123)
        info = get_seed_info()
        assert info["seed"] == 123
        assert info["is_set"] is True