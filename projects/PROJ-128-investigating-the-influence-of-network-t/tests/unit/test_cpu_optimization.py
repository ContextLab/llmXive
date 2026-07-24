"""
Unit tests for CPU optimization utilities.
"""

import unittest
import numpy as np
import pandas as pd
import os
import sys

# Ensure the code directory is in the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.cpu_optimization import (
    optimize_memory_usage,
    validate_no_gpu_acceleration,
    set_random_seed,
    ensure_numpy_arrays_contiguous
)
from pathlib import Path

class TestCpuOptimization(unittest.TestCase):

    def test_optimize_memory_downcast_integers(self):
        """Test that integers are downcast to the smallest possible type."""
        df = pd.DataFrame({
            'small_int': [1, 2, 3],  # Fits in int8
            'large_int': [1000, 2000, 3000]  # Fits in int16
        })
        
        optimized = optimize_memory_usage(df)
        
        self.assertEqual(optimized['small_int'].dtype, np.int8)
        self.assertEqual(optimized['large_int'].dtype, np.int16)

    def test_optimize_memory_downcast_floats(self):
        """Test that floats are downcast from float64 to float32."""
        df = pd.DataFrame({
            'floats': [1.1, 2.2, 3.3]
        })
        
        original_dtype = df['floats'].dtype
        self.assertEqual(original_dtype, np.float64)
        
        optimized = optimize_memory_usage(df)
        
        # Should be downcast to float32
        self.assertEqual(optimized['floats'].dtype, np.float32)

    def test_optimize_memory_preserves_values(self):
        """Test that optimization does not alter data values."""
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [1.5, 2.5, 3.5]
        })
        
        optimized = optimize_memory_usage(df)
        
        pd.testing.assert_frame_equal(
            df.astype({'a': np.int8, 'b': np.float32}),
            optimized,
            check_dtype=False  # We expect dtype changes, but values should match
        )

    def test_validate_no_gpu_acceleration(self):
        """Test that GPU validation returns True in a CPU-only environment."""
        # In the test environment, we expect no GPU to be configured
        result = validate_no_gpu_acceleration()
        self.assertTrue(result)

    def test_set_random_seed(self):
        """Test that random seed is set correctly."""
        set_random_seed(42)
        val1 = np.random.rand()
        
        set_random_seed(42)
        val2 = np.random.rand()
        
        self.assertEqual(val1, val2)

    def test_ensure_contiguous(self):
        """Test that arrays are made contiguous."""
        arr = np.random.rand(10, 10)
        # Create a non-contiguous view
        non_contiguous = arr[::2, ::2]
        self.assertFalse(non_contiguous.flags['C_CONTIGUOUS'])
        
        contiguous_list = ensure_numpy_arrays_contiguous([non_contiguous])
        self.assertTrue(contiguous_list[0].flags['C_CONTIGUOUS'])

if __name__ == '__main__':
    unittest.main()
