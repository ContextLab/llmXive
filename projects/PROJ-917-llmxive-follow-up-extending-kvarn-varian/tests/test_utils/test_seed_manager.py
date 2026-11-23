"""
Tests for the seed management module.
"""
import pytest
import random
import numpy as np

# Try to import torch for testing if available
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from utils.seed_manager import set_seed, get_seed, reset_seed, ensure_seed_set

def test_set_seed_sets_all_modules():
    """Test that set_seed correctly sets seeds for all modules."""
    seed = 42
    set_seed(seed)

    assert random.random() == random.random()  # This will fail if seeds aren't set consistently
    # Reset and check again
    set_seed(seed, force=True)
    val1 = random.random()
    val2 = np.random.rand()

    set_seed(seed, force=True)
    val3 = random.random()
    val4 = np.random.rand()

    assert val1 == val3
    assert val2 == val4

def test_get_seed_returns_correct_value():
    """Test that get_seed returns the correct seed value."""
    seed = 123
    set_seed(seed)
    assert get_seed() == seed

    reset_seed()
    assert get_seed() is None

def test_reset_seed_clears_global_seed():
    """Test that reset_seed clears the global seed."""
    set_seed(456)
    reset_seed()
    assert get_seed() is None

def test_set_seed_without_force_raises_error():
    """Test that setting a seed without force raises an error if seed is already set."""
    set_seed(789)
    with pytest.raises(ValueError):
        set_seed(999)

def test_set_seed_with_force_overwrites():
    """Test that setting a seed with force overwrites the existing seed."""
    set_seed(111)
    set_seed(222, force=True)
    assert get_seed() == 222

def test_ensure_seed_set_uses_provided_seed():
    """Test that ensure_seed_set uses the provided seed."""
    seed = 333
    result = ensure_seed_set(seed)
    assert result == seed
    assert get_seed() == seed

def test_ensure_seed_set_uses_global_seed():
    """Test that ensure_seed_set uses the global seed if no seed is provided."""
    set_seed(444)
    result = ensure_seed_set()
    assert result == 444

def test_ensure_seed_set_generates_new_seed():
    """Test that ensure_seed_set generates a new seed if none is set."""
    reset_seed()
    result = ensure_seed_set()
    assert result is not None
    assert get_seed() == result

@pytest.mark.skipif(not TORCH_AVAILABLE, reason="PyTorch not available")
def test_set_seed_sets_torch_seeds():
    """Test that set_seed correctly sets torch seeds if torch is available."""
    seed = 555
    set_seed(seed)

    # Reset and check
    set_seed(seed, force=True)
    val1 = torch.rand(1).item()

    set_seed(seed, force=True)
    val2 = torch.rand(1).item()

    assert val1 == val2