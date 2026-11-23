import numpy as np
import random
from src.utils.seed import set_global_seed

def test_numpy_determinism():
    """
    Verify that setting the seed produces identical NumPy random outputs.
    This directly implements the verification step requested in T000.
    """
    seed = 42
    set_global_seed(seed)
    val1 = np.random.rand()
    
    set_global_seed(seed)
    val2 = np.random.rand()
    
    assert val1 == val2, f"NumPy RNG not deterministic: {val1} != {val2}"

def test_python_random_determinism():
    """
    Verify that setting the seed produces identical Python random outputs.
    """
    seed = 42
    set_global_seed(seed)
    val1 = random.random()
    
    set_global_seed(seed)
    val2 = random.random()
    
    assert val1 == val2, f"Python random not deterministic: {val1} != {val2}"

def test_package_import_seeds():
    """
    Verify that importing the src package automatically seeds the RNG.
    """
    import src
    # The import should have called set_global_seed(42)
    # We check if the first value matches the known seed 42 result
    set_global_seed(42)
    expected = np.random.rand()
    
    # Reset and check package default
    import importlib
    import src
    importlib.reload(src)
    actual = np.random.rand()
    
    assert expected == actual, "Package import did not apply default seed correctly"
