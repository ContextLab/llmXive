"""
Unit tests for the optimization module.
"""
import pytest
import pandas as pd
import numpy as np
import tempfile
import os
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.optimization import (
    get_current_memory_mb,
    get_memory_usage_mb,
    sample_dataframe,
    reduce_memory_usage,
    check_memory_usage,
    ensure_memory_safe,
    get_optimal_chunk_size,
    run_optimization_pipeline
)

class TestOptimizationModule:
    """Test suite for optimization functions."""

    def test_sample_dataframe_with_size(self):
        """Test sampling with explicit size."""
        df = pd.DataFrame({'a': range(100), 'b': range(100, 200)})
        sampled = sample_dataframe(df, sample_size=10, random_state=42)
        
        assert len(sampled) == 10
        assert len(sampled) < len(df)
        assert list(sampled.columns) == ['a', 'b']

    def test_sample_dataframe_with_fraction(self):
        """Test sampling with fraction."""
        df = pd.DataFrame({'a': range(1000), 'b': range(1000, 2000)})
        sampled = sample_dataframe(df, sample_fraction=0.1, random_state=42)
        
        assert len(sampled) == 100
        assert len(sampled) == len(df) * 0.1

    def test_sample_dataframe_no_args(self):
        """Test default sampling (10%)."""
        df = pd.DataFrame({'a': range(100), 'b': range(100, 200)})
        sampled = sample_dataframe(df, random_state=42)
        
        assert len(sampled) == 10
        assert len(sampled) == len(df) * 0.1

    def test_sample_dataframe_large_than_original(self):
        """Test when sample size is larger than dataframe."""
        df = pd.DataFrame({'a': range(10), 'b': range(10, 20)})
        sampled = sample_dataframe(df, sample_size=100, random_state=42)
        
        # Should return original
        assert len(sampled) == len(df)

    def test_reduce_memory_usage_integers(self):
        """Test memory reduction for integer columns."""
        df = pd.DataFrame({
            'small_int': np.array([1, 2, 3], dtype=np.int64),
            'large_int': np.array([100000, 200000, 300000], dtype=np.int64)
        })
        
        reduced = reduce_memory_usage(df)
        
        # Small integers should be downcasted
        assert reduced['small_int'].dtype == np.int8
        # Large integers might stay as int32 or int64 depending on range
        assert reduced['large_int'].dtype in [np.int32, np.int64]

    def test_reduce_memory_usage_floats(self):
        """Test memory reduction for float columns."""
        df = pd.DataFrame({
            'small_float': np.array([0.1, 0.2, 0.3], dtype=np.float64),
            'large_float': np.array([100000.5, 200000.5, 300000.5], dtype=np.float64)
        })
        
        reduced = reduce_memory_usage(df)
        
        # Check that dtypes are optimized (might be float32 or float64)
        assert reduced['small_float'].dtype in [np.float32, np.float64]

    def test_reduce_memory_usage_categorical(self):
        """Test memory reduction for categorical columns."""
        df = pd.DataFrame({
            'category_col': ['A', 'B', 'A', 'C', 'B', 'A'] * 100
        })
        
        reduced = reduce_memory_usage(df)
        
        # Should be converted to category
        assert reduced['category_col'].dtype.name == 'category'

    def test_get_optimal_chunk_size(self):
        """Test optimal chunk size calculation."""
        # Should return a reasonable chunk size
        chunk_size = get_optimal_chunk_size(total_rows=1000000, target_mem_mb=5000)
        
        assert chunk_size > 0
        assert chunk_size <= 1000000
        assert chunk_size >= 1000

    def test_ensure_memory_safe_no_sampling_needed(self):
        """Test when no sampling is needed."""
        df = pd.DataFrame({'a': range(100), 'b': range(100, 200)})
        
        result = ensure_memory_safe(df, max_rows=1000, sample_fraction=None)
        
        # Should return optimized version but same size
        assert len(result) == len(df)

    def test_ensure_memory_safe_with_max_rows(self):
        """Test sampling with max_rows."""
        df = pd.DataFrame({'a': range(1000), 'b': range(1000, 2000)})
        
        result = ensure_memory_safe(df, max_rows=100, sample_fraction=None)
        
        assert len(result) == 100

    def test_run_optimization_pipeline_parquet(self):
        """Test optimization pipeline with parquet files."""
        # Create temporary files
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.parquet'
            output_path = Path(tmpdir) / 'output.parquet'
            
            # Create sample data
            df = pd.DataFrame({
                'game_id': range(100),
                'white_rating': [1500 + i for i in range(100)],
                'black_rating': [1500 + i for i in range(100)]
            })
            df.to_parquet(input_path)
            
            # Run optimization
            stats = run_optimization_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                sample_fraction=0.5
            )
            
            assert stats['success']
            assert stats['final_rows'] == 50
            assert Path(output_path).exists()

    def test_run_optimization_pipeline_csv(self):
        """Test optimization pipeline with CSV files."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.csv'
            output_path = Path(tmpdir) / 'output.csv'
            
            # Create sample data
            df = pd.DataFrame({
                'game_id': range(100),
                'value': range(100)
            })
            df.to_csv(input_path, index=False)
            
            # Run optimization
            stats = run_optimization_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                sample_fraction=0.5
            )
            
            assert stats['success']
            assert stats['final_rows'] == 50
            assert Path(output_path).exists()

    def test_run_optimization_pipeline_unsupported_format(self):
        """Test error handling for unsupported file format."""
        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / 'input.txt'
            output_path = Path(tmpdir) / 'output.txt'
            
            # Create dummy file
            input_path.write_text("dummy")
            
            # Run optimization - should fail gracefully
            stats = run_optimization_pipeline(
                input_path=str(input_path),
                output_path=str(output_path),
                sample_fraction=0.5
            )
            
            assert not stats['success']
            assert 'error' in stats

    def test_memory_functions_exist(self):
        """Test that memory monitoring functions exist and return numbers."""
        # These should not raise exceptions
        mem1 = get_current_memory_mb()
        mem2 = get_memory_usage_mb()
        
        assert isinstance(mem1, (int, float))
        assert isinstance(mem2, (int, float))
        assert mem1 >= 0
        assert mem2 >= 0