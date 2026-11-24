import random
import numpy as np
import pytest
from code.utils.io_utils import set_global_seeds

def test_seed_consistency():
    """
    Verify that setting the global seed produces identical sequences 
    of random numbers for both Python's random module and numpy.
    """
    seed = 42
    
    # First run
    set_global_seeds(seed)
    val1_py = random.random()
    val1_np = np.random.rand()

    # Second run (reset seed)
    set_global_seeds(seed)
    val2_py = random.random()
    val2_np = np.random.rand()

    assert val1_py == val2_py, f"Python random seed not consistent: {val1_py} != {val2_py}"
    assert val1_np == val2_np, f"Numpy random seed not consistent: {val1_np} != {val2_np}"

def test_different_seeds_produce_different_results():
    """
    Verify that different seeds produce different random sequences.
    """
    set_global_seeds(42)
    val1 = np.random.rand()
    
    set_global_seeds(43)
    val2 = np.random.rand()
    
    assert val1 != val2, "Different seeds produced the same random value"
