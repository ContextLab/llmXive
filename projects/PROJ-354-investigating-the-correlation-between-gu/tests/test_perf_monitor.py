"""
Tests for performance monitoring and optimization utilities.
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import gc

from code.perf_monitor import (
    get_current_memory_usage,
    estimate_dataframe_memory,
    estimate_batch_memory,
    calculate_safe_batch_size,
    trigger_memory_cleanup,
    check_memory_pressure,
    optimize_dataframe_memory,
    validate_memory_constraints
)


class TestMemoryEstimation:
    """Tests for memory estimation functions."""

    def test_estimate_dataframe_memory_empty(self):
        """Test memory estimation for empty DataFrame."""
        df = pd.DataFrame()
        assert estimate_dataframe_memory(df) == 0.0
    
    def test_estimate_dataframe_memory_none(self):
        """Test memory estimation for None input."""
        assert estimate_dataframe_memory(None) == 0.0
    
    def test_estimate_dataframe_memory_basic(self):
        """Test memory estimation with basic DataFrame."""
        df = pd.DataFrame({
            'a': [1, 2, 3],
            'b': [1.0, 2.0, 3.0],
            'c': ['x', 'y', 'z']
        })
        
        mem_gb = estimate_dataframe_memory(df)
        assert mem_gb > 0
        assert isinstance(mem_gb, float)
    
    def test_estimate_batch_memory(self):
        """Test batch memory estimation."""
        mem_gb = estimate_batch_memory(
            num_rows=1000,
            num_columns=10,
            dtype_estimate=8.0
        )
        
        # Should be small but positive
        assert mem_gb > 0
        assert mem_gb < 1.0  # Less than 1GB


class TestBatchSizeCalculation:
    """Tests for safe batch size calculation."""

    def test_calculate_safe_batch_size_from_sample(self):
        """Test batch size calculation from sample DataFrame."""
        sample_df = pd.DataFrame({
            'a': np.random.rand(1000),
            'b': np.random.rand(1000)
        })
        
        batch_size = calculate_safe_batch_size(df_sample=sample_df)
        
        assert batch_size >= 100
        assert isinstance(batch_size, int)
    
    def test_calculate_safe_batch_size_from_hints(self):
        """Test batch size calculation from row/column hints."""
        batch_size = calculate_safe_batch_size(
            num_rows_hint=100000,
            num_columns_hint=20
        )
        
        assert batch_size >= 100
        assert isinstance(batch_size, int)
    
    def test_calculate_safe_batch_size_default(self):
        """Test default batch size when no info provided."""
        batch_size = calculate_safe_batch_size()
        
        assert batch_size == 10000


class TestMemoryCleanup:
    """Tests for memory cleanup functions."""

    def test_trigger_memory_cleanup(self):
        """Test that cleanup function runs without error."""
        # Should not raise
        trigger_memory_cleanup()
    
    @patch('code.perf_monitor.psutil.Process')
    def test_check_memory_pressure(self, mock_process):
        """Test memory pressure checking."""
        # Mock memory info
        mock_process.return_value.memory_info.return_value = MagicMock(
            rss=1 * 1024**3,  # 1GB
            vms=2 * 1024**3
        )
        mock_process.return_value.memory_percent.return_value = 50.0
        
        is_pressure, percent = check_memory_pressure(threshold_percent=80.0)
        
        assert isinstance(is_pressure, bool)
        assert isinstance(percent, float)
        assert not is_pressure  # 1GB is below 7GB * 0.8


class TestDataFrameOptimization:
    """Tests for DataFrame memory optimization."""

    def test_optimize_dataframe_memory_empty(self):
        """Test optimization of empty DataFrame."""
        df = pd.DataFrame()
        optimized = optimize_dataframe_memory(df)
        assert optimized.empty
    
    def test_optimize_dataframe_memory_none(self):
        """Test optimization of None input."""
        result = optimize_dataframe_memory(None)
        assert result is None
    
    def test_optimize_dataframe_memory_downcast(self):
        """Test that optimization downcasts numeric types."""
        df = pd.DataFrame({
            'int_col': pd.Series([1, 2, 3], dtype='int64'),
            'float_col': pd.Series([1.0, 2.0, 3.0], dtype='float64'),
            'obj_col': pd.Series(['a', 'b', 'c'], dtype='object')
        })
        
        initial_mem = estimate_dataframe_memory(df)
        optimized = optimize_dataframe_memory(df)
        optimized_mem = estimate_dataframe_memory(optimized)
        
        # Memory should be same or less (optimization may not always reduce)
        assert optimized_mem <= initial_mem
    
    def test_optimize_dataframe_memory_category_conversion(self):
        """Test that low-cardinality objects are converted to category."""
        df = pd.DataFrame({
            'low_card': pd.Series(['a', 'a', 'b', 'a', 'b'] * 100, dtype='object')
        })
        
        optimized = optimize_dataframe_memory(df)
        
        # Should be converted to category
        assert optimized['low_card'].dtype.name == 'category'


class TestMemoryConstraintsValidation:
    """Tests for memory constraint validation."""

    def test_validate_memory_constraints_valid(self):
        """Test validation with valid memory usage."""
        df = pd.DataFrame({'a': [1, 2, 3]})
        result = validate_memory_constraints(df, ['operation1', 'operation2'])
        
        assert 'is_valid' in result
        assert 'df_memory_gb' in result
        assert 'estimated_total_memory_gb' in result
        assert 'recommendations' in result
        assert isinstance(result['recommendations'], list)
    
    def test_validate_memory_constraints_invalid(self):
        """Test validation with invalid memory usage (simulated)."""
        # Create a large DataFrame to potentially trigger recommendations
        df = pd.DataFrame({
            'a': np.random.rand(100000),
            'b': np.random.rand(100000)
        })
        
        result = validate_memory_constraints(df, ['op'] * 100)
        
        assert 'is_valid' in result
        assert 'recommendations' in result
        # Even if valid, should have recommendations list
        assert isinstance(result['recommendations'], list)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])