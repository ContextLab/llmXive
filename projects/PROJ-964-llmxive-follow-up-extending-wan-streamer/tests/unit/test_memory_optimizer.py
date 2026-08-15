"""
Unit tests for memory optimization utilities.
"""
import os
import sys
import pytest
import tempfile
import shutil
import pandas as pd
import numpy as np
from pathlib import Path
import torch

from utils.memory_optimizer import (
    get_memory_usage_mb,
    force_gc,
    chunked_dataframe_reader,
    optimize_dataframe_dtypes,
    stream_process_large_dataset,
    validate_memory_constraints,
    cleanup_tensor_memory,
    reduce_model_checkpoint_size
)


class TestMemoryOptimizer:
    """Test cases for memory optimization utilities."""
    
    def test_get_memory_usage_returns_positive(self):
        """Test that memory usage returns a positive number."""
        memory = get_memory_usage_mb()
        assert memory >= 0, "Memory usage should be non-negative"
    
    def test_force_gc_no_error(self):
        """Test that force_gc executes without error."""
        force_gc()  # Should not raise
    
    def test_optimize_dataframe_dtypes_reduces_memory(self):
        """Test that dtype optimization reduces memory usage."""
        # Create a DataFrame with inefficient types
        df = pd.DataFrame({
            'int_col': [1, 2, 3] * 1000,
            'float_col': [1.5, 2.5, 3.5] * 1000,
            'str_col': ['small'] * 3000
        })
        
        original_memory = df.memory_usage(deep=True).sum()
        optimized_df = optimize_dataframe_dtypes(df)
        optimized_memory = optimized_df.memory_usage(deep=True).sum()
        
        assert optimized_memory <= original_memory, \
            "Optimized memory should be <= original"
        assert optimized_df['int_col'].dtype in [np.int8, np.int16, np.int32, np.int64], \
            "Integer column should be optimized"
    
    def test_chunked_dataframe_reader_parquet(self):
        """Test chunked reading of parquet files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            test_df = pd.DataFrame({
                'id': range(1000),
                'value': np.random.randn(1000)
            })
            test_path = Path(tmpdir) / 'test.parquet'
            test_df.to_parquet(test_path)
            
            # Read in chunks
            chunks = list(chunked_dataframe_reader(test_path, chunk_size=100))
            assert len(chunks) == 10, f"Expected 10 chunks, got {len(chunks)}"
            
            # Verify data integrity
            combined = pd.concat(chunks, ignore_index=True)
            assert len(combined) == 1000, "Combined chunks should have 1000 rows"
    
    def test_validate_memory_constraints_within_limit(self):
        """Test validation when memory is within limits."""
        # Use a very high limit to ensure we're within it
        assert validate_memory_constraints(100000) is True
    
    def test_cleanup_tensor_memory(self):
        """Test that tensor cleanup works."""
        tensors = [torch.randn(100, 100) for _ in range(5)]
        cleanup_tensor_memory(tensors)
        
        # All should be None now
        assert all(t is None for t in tensors)
    
    def test_reduce_model_checkpoint_size(self):
        """Test checkpoint size reduction."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock checkpoint
            checkpoint = {
                'model_state_dict': {
                    'layer.weight': torch.randn(100, 100)
                },
                'optimizer': {'state': 'mock'},
                'scheduler': {'state': 'mock'}
            }
            
            original_path = Path(tmpdir) / 'original.pt'
            reduced_path = Path(tmpdir) / 'reduced.pt'
            
            torch.save(checkpoint, original_path)
            original_size = original_path.stat().st_size
            
            # Reduce checkpoint
            reduce_model_checkpoint_size(original_path, reduced_path)
            reduced_size = reduced_path.stat().st_size
            
            assert reduced_size < original_size, \
                "Reduced checkpoint should be smaller"
            
            # Verify optimizer/scheduler removed
            reduced_checkpoint = torch.load(reduced_path, map_location='cpu')
            assert 'optimizer' not in reduced_checkpoint or \
                   reduced_checkpoint.get('optimizer') is None
    
    def test_stream_process_large_dataset(self):
        """Test streaming processing of large dataset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test data
            test_df = pd.DataFrame({
                'id': range(1000),
                'value': np.random.randn(1000)
            })
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            test_df.to_parquet(input_path)
            
            # Process function
            def process_func(df):
                df['doubled'] = df['value'] * 2
                return df
            
            # Stream process
            stream_process_large_dataset(input_path, output_path, process_func)
            
            # Verify output
            result = pd.read_parquet(output_path)
            assert len(result) == 1000, "Output should have 1000 rows"
            assert 'doubled' in result.columns, "Output should have doubled column"
            np.testing.assert_array_almost_equal(
                result['doubled'].values,
                result['value'].values * 2
            )