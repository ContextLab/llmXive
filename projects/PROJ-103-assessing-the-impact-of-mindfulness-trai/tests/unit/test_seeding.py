import numpy as np
import pytest
from code.src.utils.seeding import set_all_seeds, verify_determinism, DEFAULT_SEED

def test_numpy_determinism():
    """Confirm that NumPy produces identical results when seeds are reset."""
    set_all_seeds(DEFAULT_SEED)
    a = np.random.rand(10)
    set_all_seeds(DEFAULT_SEED)
    b = np.random.rand(10)
    np.testing.assert_array_equal(a, b)

def test_verify_determinism_success():
    """Test that verify_determinism returns True for deterministic functions."""
    def deterministic_func():
        return np.random.rand(5)
    
    assert verify_determinism(deterministic_func, seed=DEFAULT_SEED) is True

def test_verify_determinism_failure():
    """Test that verify_determinism raises RuntimeError for non-deterministic functions."""
    # State is shared, so if we don't reset seeds inside the func, 
    # it's non-deterministic across calls.
    # However, verify_determinism calls set_all_seeds internally.
    # To force failure, we use a function that depends on external state.
    counter = 0
    def non_deterministic_func():
        nonlocal counter
        counter += 1
        return counter
    
    with pytest.raises(RuntimeError, match="Function output is not deterministic"):
        verify_determinism(non_deterministic_func)