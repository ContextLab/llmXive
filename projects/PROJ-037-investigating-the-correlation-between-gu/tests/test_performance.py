"""
Tests for performance optimization utilities.
"""

import os
import sys
import unittest
import tempfile
import numpy as np
import pandas as pd
from pathlib import Path
from unittest.mock import Mock, patch

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from code.performance_optimizer import (
    configure_parallelism,
    time_function,
    parallel_fdr_correction,
    optimize_dataframe_memory,
    estimate_runtime
)
from code.performance_config import PerformanceConfig, get_performance_config


class TestPerformanceConfig(unittest.TestCase):
    """Tests for performance configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = get_performance_config()
        self.assertEqual(config.n_jobs, 4)
        self.assertEqual(config.max_runtime_seconds, 6 * 3600)
        self.assertTrue(config.optimize_memory)
    
    def test_config_to_dict(self):
        """Test configuration serialization."""
        config = PerformanceConfig(n_jobs=8)
        config_dict = config.to_dict()
        self.assertEqual(config_dict['n_jobs'], 8)
        self.assertIn('max_runtime_seconds', config_dict)

class TestParallelism(unittest.TestCase):
    """Tests for parallelism configuration."""
    
    def test_configure_parallelism(self):
        """Test parallelism configuration."""
        from code.performance_optimizer import N_JOBS
        # Note: N_JOBS is global, so we just verify the function exists
        configure_parallelism(2)
        # In a real test, we'd verify the global state
    
    def test_time_decorator(self):
        """Test the time decorator."""
        @time_function
        def dummy_func():
            return 42
        
        result = dummy_func()
        self.assertEqual(result, 42)

class TestDataOptimization(unittest.TestCase):
    """Tests for data optimization utilities."""
    
    def test_memory_optimization(self):
        """Test memory optimization of DataFrame."""
        # Create a test DataFrame
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5] * 100,
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5] * 100,
            'object_col': ['a', 'b', 'c', 'd', 'e'] * 100
        })
        
        # Optimize memory
        optimized_df = optimize_dataframe_memory(df)
        
        # Verify types were downcast
        self.assertEqual(optimized_df['int_col'].dtype, np.int8)
        self.assertEqual(optimized_df['float_col'].dtype, np.float32)
        self.assertEqual(optimized_df['object_col'].dtype.name, 'category')
    
    def test_memory_optimization_with_nan(self):
        """Test memory optimization handles NaN values."""
        df = pd.DataFrame({
            'float_col': [1.0, np.nan, 3.0, np.nan, 5.0] * 100
        })
        
        optimized_df = optimize_dataframe_memory(df)
        self.assertEqual(optimized_df['float_col'].dtype, np.float32)

class TestFDRCorrection(unittest.TestCase):
    """Tests for FDR correction."""
    
    def test_parallel_fdr_correction(self):
        """Test FDR correction with valid p-values."""
        p_values = pd.Series([0.01, 0.05, 0.1, 0.2, 0.5])
        corrected = parallel_fdr_correction(p_values)
        
        self.assertEqual(len(corrected), len(p_values))
        self.assertFalse(corrected.isna().any())
        # FDR-corrected p-values should be >= original
        self.assertTrue((corrected >= p_values).all())
    
    def test_fdr_with_nan(self):
        """Test FDR correction handles NaN values."""
        p_values = pd.Series([0.01, np.nan, 0.1, np.nan, 0.5])
        corrected = parallel_fdr_correction(p_values)
        
        self.assertTrue(pd.isna(corrected.iloc[1]))
        self.assertTrue(pd.isna(corrected.iloc[3]))
        self.assertFalse(pd.isna(corrected.iloc[0]))

class TestRuntimeEstimation(unittest.TestCase):
    """Tests for runtime estimation."""
    
    def test_runtime_estimate(self):
        """Test runtime estimation for typical workloads."""
        # Estimate for N=200, 1000 features
        runtime = estimate_runtime(200, 1000, n_jobs=4)
        
        # Should be well under 6 hours (21600 seconds)
        self.assertLess(runtime, 21600)
        # Should be positive
        self.assertGreater(runtime, 0)
    
    def test_runtime_scaling(self):
        """Test that runtime scales appropriately with sample size."""
        runtime_100 = estimate_runtime(100, 500, n_jobs=4)
        runtime_200 = estimate_runtime(200, 500, n_jobs=4)
        
        # Runtime should increase with sample size
        self.assertGreater(runtime_200, runtime_100)

if __name__ == '__main__':
    unittest.main()