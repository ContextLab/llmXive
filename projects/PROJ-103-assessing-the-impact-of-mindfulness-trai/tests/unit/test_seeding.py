"""
Unit tests for the seeding module.

Tests verify that:
1. Seeds are correctly set for numpy, random, and torch.
2. Functions produce deterministic output when seeds are reset.
3. Default seed value is 42.
"""
import random
import unittest
from unittest.mock import patch, MagicMock
import numpy as np

# Import the module under test
from src.utils import seeding


class TestSeeding(unittest.TestCase):
    """Tests for the seeding module."""

    def test_default_seed_value(self):
        """Test that the default seed is 42."""
        self.assertEqual(seeding.DEFAULT_SEED, 42)
        self.assertEqual(seeding.get_seed(), 42)

    def test_set_all_seeds_numpy(self):
        """Test that numpy seed is set correctly."""
        seeding.set_all_seeds(123)
        arr1 = np.random.rand(5)
        
        seeding.set_all_seeds(123)
        arr2 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr1, arr2)

    def test_set_all_seeds_random(self):
        """Test that random module seed is set correctly."""
        seeding.set_all_seeds(456)
        val1 = random.random()
        
        seeding.set_all_seeds(456)
        val2 = random.random()
        
        self.assertEqual(val1, val2)

    @unittest.skipIf(not seeding.TORCH_AVAILABLE, "PyTorch not available")
    def test_set_all_seeds_torch(self):
        """Test that torch seed is set correctly."""
        import torch
        seeding.set_all_seeds(789)
        tensor1 = torch.rand(5)
        
        seeding.set_all_seeds(789)
        tensor2 = torch.rand(5)
        
        self.assertTrue(torch.equal(tensor1, tensor2))

    @unittest.skipIf(not seeding.TORCH_AVAILABLE, "PyTorch not available")
    def test_torch_determinism_flags(self):
        """Test that torch determinism flags are set."""
        import torch
        seeding.set_all_seeds(42)
        
        self.assertTrue(torch.backends.cudnn.deterministic)
        self.assertFalse(torch.backends.cudnn.benchmark)

    def test_verify_determinism_numpy(self):
        """Test determinism verification with numpy."""
        def generate_array():
            return np.random.rand(10)
        
        result = seeding.verify_determinism(generate_array, iterations=3)
        self.assertTrue(result)

    def test_verify_determinism_random(self):
        """Test determinism verification with random module."""
        def generate_value():
            return random.random()
        
        result = seeding.verify_determinism(generate_value, iterations=3)
        self.assertTrue(result)

    @unittest.skipIf(not seeding.TORCH_AVAILABLE, "PyTorch not available")
    def test_verify_determinism_torch(self):
        """Test determinism verification with torch."""
        import torch
        def generate_tensor():
            return torch.rand(5)
        
        result = seeding.verify_determinism(generate_tensor, iterations=3)
        self.assertTrue(result)

    def test_verify_determinism_failure(self):
        """Test that verify_determinism raises on non-deterministic function."""
        counter = [0]
        def non_deterministic_func():
            counter[0] += 1
            return counter[0]
        
        with self.assertRaises(RuntimeError):
            seeding.verify_determinism(non_deterministic_func, iterations=2)

    def test_set_seed_none_uses_default(self):
        """Test that passing None uses the default seed."""
        seeding.set_all_seeds(999)
        arr1 = np.random.rand(5)
        
        seeding.set_all_seeds(None)  # Should use DEFAULT_SEED (42)
        arr2 = np.random.rand(5)
        
        seeding.set_all_seeds(42)
        arr3 = np.random.rand(5)
        
        np.testing.assert_array_equal(arr2, arr3)


if __name__ == '__main__':
    unittest.main()