import pytest
import pandas as pd
import numpy as np
import time
from code.performance_optimizer import time_function, optimize_dataframe_memory, estimate_runtime

class TestTimeFunction:
    def test_time_function_returns_time(self):
        """Test that time_function returns execution time."""
        def dummy_func():
            time.sleep(0.1)
            
        elapsed = time_function(dummy_func)
        assert elapsed >= 0.1
        assert isinstance(elapsed, float)

    def test_time_function_returns_result(self):
        """Test that time_function returns the function result."""
        def dummy_func():
            return 42
            
        result, elapsed = time_function(dummy_func)
        assert result == 42
        assert isinstance(elapsed, float)

class TestOptimizeDataFrameMemory:
    def test_optimize_dataframe_memory_reduces_size(self):
        """Test that optimize_dataframe_memory reduces memory usage."""
        # Create a large dataframe
        df = pd.DataFrame({
            'int_col': range(10000),
            'float_col': np.random.rand(10000),
            'str_col': ['category_' + str(i % 10) for i in range(10000)]
        })
        
        original_memory = df.memory_usage(deep=True).sum()
        optimized_df = optimize_dataframe_memory(df)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()
        
        # Optimized should use less or equal memory
        assert optimized_memory <= original_memory

    def test_optimize_dataframe_memory_preserves_data(self):
        """Test that optimize_dataframe_memory preserves data values."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'str_col': ['a', 'b', 'c', 'd', 'e']
        })
        
        optimized_df = optimize_dataframe_memory(df)
        
        # Values should be preserved
        pd.testing.assert_frame_equal(df, optimized_df)

class TestEstimateRuntime:
    def test_estimate_runtime_positive(self):
        """Test that estimate_runtime returns positive values."""
        # Mock data processing time
        n_samples = 1000
        estimated_time = estimate_runtime(n_samples)
        assert estimated_time >= 0

    def test_estimate_runtime_scaling(self):
        """Test that estimate_runtime scales with input size."""
        time_small = estimate_runtime(100)
        time_large = estimate_runtime(1000)
        
        # Larger input should take longer (or at least not less)
        assert time_large >= time_small