"""
Unit tests for memory optimization utilities.
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
import tempfile
import gc

from code.memory_utils import (
    optimize_dataframe_memory,
    check_memory_usage,
    get_memory_profile_summary,
    clear_unused_memory
)

class TestMemoryUtils:
    """Tests for memory optimization functions."""
    
    def test_optimize_dataframe_memory_reduces_size(self):
        """Test that memory optimization reduces DataFrame size."""
        # Create a large DataFrame
        df = pd.DataFrame({
            'int_col': range(100000),
            'float_col': np.random.random(100000),
            'object_col': [f'item_{i % 100}' for i in range(100000)]
        })
        
        initial_memory = df.memory_usage(deep=True).sum()
        
        # Optimize
        optimized_df = optimize_dataframe_memory(df)
        final_memory = optimized_df.memory_usage(deep=True).sum()
        
        # Check that memory was reduced (or stayed same if already optimal)
        assert final_memory <= initial_memory
        assert optimized_df.shape == df.shape
    
    def test_optimize_dataframe_memory_preserves_data(self):
        """Test that memory optimization preserves data values."""
        df = pd.DataFrame({
            'int_col': [1, 2, 3, 4, 5],
            'float_col': [1.1, 2.2, 3.3, 4.4, 5.5],
            'object_col': ['a', 'b', 'c', 'd', 'e']
        })
        
        optimized_df = optimize_dataframe_memory(df)
        
        # Check data integrity
        assert list(optimized_df['int_col']) == list(df['int_col'])
        assert list(optimized_df['float_col']) == list(df['float_col'])
        assert list(optimized_df['object_col']) == list(df['object_col'])
    
    def test_check_memory_usage_no_error(self):
        """Test that memory check doesn't raise error under normal conditions."""
        # Should not raise
        result = check_memory_usage(warn_only=True)
        assert result is True
    
    def test_get_memory_profile_summary(self):
        """Test memory profile summary generation."""
        profile = get_memory_profile_summary()
        
        assert 'current_bytes' in profile
        assert 'peak_bytes' in profile
        assert 'max_allowed_bytes' in profile
        assert 'within_limit' in profile
        assert profile['max_allowed_bytes'] == 4 * 1024**3
    
    def test_clear_unused_memory(self):
        """Test that memory clearing function runs without error."""
        # Create some data
        df = pd.DataFrame({'a': range(1000)})
        del df
        gc.collect()
        
        # Clear memory
        clear_unused_memory()
        
        # Should not raise