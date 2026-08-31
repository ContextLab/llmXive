"""
Unit tests for code/utils/seed.py
Tests deterministic seeding across all libraries
"""
import os
import sys
import unittest
import random
import hashlib
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.utils.seed import set_seed


class TestSeedDeterminism(unittest.TestCase):
    """Tests for deterministic seeding behavior"""

    def test_python_random_deterministic(self):
        """Test that Python random is deterministic after seeding"""
        set_seed(42)
        seq1 = [random.random() for _ in range(10)]
        
        set_seed(42)
        seq2 = [random.random() for _ in range(10)]
        
        self.assertEqual(seq1, seq2)

    def test_numpy_deterministic(self):
        """Test that numpy is deterministic after seeding"""
        import numpy as np
        
        set_seed(42)
        arr1 = np.random.rand(10)
        
        set_seed(42)
        arr2 = np.random.rand(10)
        
        self.assertTrue(np.array_equal(arr1, arr2))

    def test_torch_deterministic(self):
        """Test that torch is deterministic after seeding"""
        try:
            import torch
            
            set_seed(42)
            t1 = torch.rand(10)
            
            set_seed(42)
            t2 = torch.rand(10)
            
            self.assertTrue(torch.equal(t1, t2))
        except ImportError:
            self.skipTest("PyTorch not installed")

    def test_different_seeds_different_results(self):
        """Test that different seeds produce different results"""
        set_seed(42)
        seq1 = [random.random() for _ in range(10)]
        
        set_seed(123)
        seq2 = [random.random() for _ in range(10)]
        
        self.assertNotEqual(seq1, seq2)

    def test_seed_preserves_state(self):
        """Test that seed resets state consistently"""
        set_seed(42)
        val1 = random.random()
        val2 = random.random()
        
        set_seed(42)
        val3 = random.random()
        val4 = random.random()
        
        self.assertEqual(val1, val3)
        self.assertEqual(val2, val4)


class TestSeedEdgeCases(unittest.TestCase):
    """Tests for edge cases in seeding"""

    def test_seed_zero(self):
        """Test seeding with 0"""
        set_seed(0)
        seq1 = [random.random() for _ in range(5)]
        
        set_seed(0)
        seq2 = [random.random() for _ in range(5)]
        
        self.assertEqual(seq1, seq2)

    def test_seed_large(self):
        """Test seeding with large number"""
        set_seed(999999999)
        seq1 = [random.random() for _ in range(5)]
        
        set_seed(999999999)
        seq2 = [random.random() for _ in range(5)]
        
        self.assertEqual(seq1, seq2)

    def test_seed_negative(self):
        """Test seeding with negative number"""
        set_seed(-42)
        seq1 = [random.random() for _ in range(5)]
        
        set_seed(-42)
        seq2 = [random.random() for _ in range(5)]
        
        self.assertEqual(seq1, seq2)

    def test_seed_string_hash(self):
        """Test that string seeds are hashed deterministically"""
        set_seed("test_seed")
        seq1 = [random.random() for _ in range(5)]
        
        set_seed("test_seed")
        seq2 = [random.random() for _ in range(5)]
        
        self.assertEqual(seq1, seq2)

        # Different string should give different result
        set_seed("different_seed")
        seq3 = [random.random() for _ in range(5)]
        
        self.assertNotEqual(seq1, seq3)


class TestSeedIntegration(unittest.TestCase):
    """Integration tests for seed module"""

    def test_multiple_libraries_same_seed(self):
        """Test that seeding affects all libraries consistently"""
        import numpy as np
        try:
            import torch
            has_torch = True
        except ImportError:
            has_torch = False
        
        set_seed(42)
        py_val = random.random()
        np_val = np.random.rand()
        torch_val = torch.rand(1).item() if has_torch else 0
        
        set_seed(42)
        py_val2 = random.random()
        np_val2 = np.random.rand()
        torch_val2 = torch.rand(1).item() if has_torch else 0
        
        self.assertEqual(py_val, py_val2)
        self.assertEqual(np_val, np_val2)
        if has_torch:
            self.assertAlmostEqual(torch_val, torch_val2, places=6)

    def test_seed_with_environment(self):
        """Test that seeding works with environment variables"""
        os.environ['PYTHONHASHSEED'] = '42'
        set_seed(42)
        seq1 = [random.random() for _ in range(5)]
        
        set_seed(42)
        seq2 = [random.random() for _ in range(5)]
        
        self.assertEqual(seq1, seq2)


if __name__ == "__main__":
    unittest.main()