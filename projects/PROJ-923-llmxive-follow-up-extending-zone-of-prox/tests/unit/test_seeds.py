"""
Unit tests for the deterministic seed management system.
"""
import random
import numpy as np
import pytest
from utils.seeds import (
    set_global_seed, get_seed, reset_to_default, 
    generate_seed, seed_context, initialize_project_seed
)

def test_set_global_seed_sets_random():
    """Test that set_global_seed correctly sets the random module seed."""
    seed_val = 12345
    set_global_seed(seed_val)
    
    val1 = random.random()
    set_global_seed(seed_val)
    val2 = random.random()
    
    assert val1 == val2, "Random sequences should be identical with same seed"

def test_set_global_seed_sets_numpy():
    """Test that set_global_seed correctly sets the numpy seed."""
    seed_val = 54321
    set_global_seed(seed_val)
    
    arr1 = np.random.rand(5)
    set_global_seed(seed_val)
    arr2 = np.random.rand(5)
    
    assert np.array_equal(arr1, arr2), "Numpy arrays should be identical with same seed"

def test_get_seed_returns_current():
    """Test that get_seed returns the currently set seed."""
    seed_val = 999
    set_global_seed(seed_val)
    assert get_seed() == seed_val

def test_reset_to_default():
    """Test that reset_to_default resets to the default value."""
    set_global_seed(111)
    reset_to_default()
    # The default is 42, but the function returns the seed used.
    # We check that the state is reset by setting a known seed and checking.
    # Note: reset_to_default calls set_global_seed(42).
    assert get_seed() == 42

def test_seed_context():
    """Test that seed_context temporarily changes the seed and restores it."""
    set_global_seed(100)
    current = get_seed()
    
    with seed_context(200) as s:
        assert s == 200
        assert get_seed() == 200
    
    assert get_seed() == current

def test_seed_context_no_arg():
    """Test that seed_context without arg uses a generated seed."""
    set_global_seed(100)
    current = get_seed()
    
    with seed_context() as s:
        # s should be a valid integer
        assert isinstance(s, int)
        assert get_seed() == s
    
    assert get_seed() == current

def test_initialize_project_seed_with_config():
    """Test initialize_project_seed with a provided config seed."""
    seed_val = 777
    result = initialize_project_seed(seed_val)
    assert result == seed_val
    assert get_seed() == seed_val

def test_initialize_project_seed_random():
    """Test initialize_project_seed generates a seed when None provided."""
    result = initialize_project_seed(None)
    assert isinstance(result, int)
    assert get_seed() == result