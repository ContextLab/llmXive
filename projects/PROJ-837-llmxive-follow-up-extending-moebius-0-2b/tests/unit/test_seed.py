import pytest
import numpy as np
import random
import sys
from pathlib import Path

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.seed import set_seed

class TestSeed:
    """Unit tests for the seed utility."""

    def test_set_seed_python(self):
        """Test that set_seed affects Python's random module."""
        set_seed(42)
        val1 = random.random()
        
        set_seed(42)
        val2 = random.random()
        
        assert val1 == val2, f"Python random not deterministic: {val1} != {val2}"

    def test_set_seed_numpy(self):
        """Test that set_seed affects numpy's random state."""
        set_seed(42)
        arr1 = np.random.rand(5)
        
        set_seed(42)
        arr2 = np.random.rand(5)
        
        assert np.allclose(arr1, arr2), f"NumPy random not deterministic"

    def test_set_seed_reproducibility(self):
        """Test that set_seed ensures full reproducibility."""
        set_seed(12345)
        results = []
        for _ in range(10):
            results.append(random.random() + np.random.rand())
        
        set_seed(12345)
        results_check = []
        for _ in range(10):
            results_check.append(random.random() + np.random.rand())
        
        assert np.allclose(results, results_check), "Full reproducibility failed"

    def test_set_seed_different_values(self):
        """Test that different seeds produce different results."""
        set_seed(1)
        val1 = random.random()
        
        set_seed(2)
        val2 = random.random()
        
        assert val1 != val2, "Different seeds produced same result"