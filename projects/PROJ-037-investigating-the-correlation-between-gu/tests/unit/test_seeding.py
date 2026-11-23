import pytest
import numpy as np
import random
from code.utils.seeding import SeedManager, set_seed, get_seed_manager

class TestSeedManager:
    def test_seed_manager_singleton(self):
        """Test that SeedManager returns the same instance."""
        manager1 = get_seed_manager()
        manager2 = get_seed_manager()
        assert manager1 is manager2

    def test_seed_manager_reset(self):
        """Test that SeedManager can be reset."""
        manager1 = get_seed_manager()
        manager1.set_seed(42)
        seed1 = manager1.seed
        
        # Reset and set different seed
        manager1.reset()
        manager1.set_seed(123)
        seed2 = manager1.seed
        
        assert seed1 != seed2

    def test_seed_reproducibility(self):
        """Test that setting the same seed produces reproducible results."""
        manager = get_seed_manager()
        manager.set_seed(42)
        
        # Generate some random numbers
        rand1_np = np.random.rand(5)
        rand1_py = [random.random() for _ in range(5)]
        
        # Reset and generate again
        manager.set_seed(42)
        rand2_np = np.random.rand(5)
        rand2_py = [random.random() for _ in range(5)]
        
        # Check reproducibility
        np.testing.assert_array_equal(rand1_np, rand2_np)
        assert rand1_py == rand2_py

class TestSetSeed:
    def test_set_seed_function(self):
        """Test that set_seed function works correctly."""
        set_seed(42)
        rand1 = np.random.rand(5)
        
        set_seed(42)
        rand2 = np.random.rand(5)
        
        np.testing.assert_array_equal(rand1, rand2)

    def test_set_seed_different_seeds(self):
        """Test that different seeds produce different results."""
        set_seed(42)
        rand1 = np.random.rand(5)
        
        set_seed(123)
        rand2 = np.random.rand(5)
        
        # Should be different (with very high probability)
        assert not np.array_equal(rand1, rand2)