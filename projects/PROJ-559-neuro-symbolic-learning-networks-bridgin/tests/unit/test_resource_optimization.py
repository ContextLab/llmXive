"""
Unit tests for resource optimization module (T043).

These tests validate that the optimization strategies work correctly
and that memory limits are enforced.
"""

import os
import sys
import json
import tempfile
import shutil
import pytest
import pandas as pd
import numpy as np

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from performance.resource_optimization import (
    optimize_dataframe_dtypes,
    stream_dataframe_in_batches,
    run_optimization_validation,
    MEMORY_LIMIT_MB
)
from performance.memory_monitor import get_current_memory_mb, force_gc


class TestResourceOptimization:
    """Test suite for resource optimization functions."""

    def setup_method(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.test_csv_path = os.path.join(self.temp_dir, 'test_data.csv')
        
        # Create a test CSV file
        test_data = {
            'id': range(1000),
            'value_float': np.random.rand(1000),
            'value_int': np.random.randint(0, 1000, 1000),
            'category': np.random.choice(['A', 'B', 'C', 'D'], 1000),
            'text': [f"sample text {i}" for i in range(1000)]
        }
        df = pd.DataFrame(test_data)
        df.to_csv(self.test_csv_path, index=False)

    def teardown_method(self):
        """Clean up test fixtures."""
        force_gc()
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_optimize_dataframe_dtypes_float64_to_float32(self):
        """Test that float64 columns are downcast to float32."""
        df = pd.DataFrame({
            'float64_col': [1.1, 2.2, 3.3],
            'int64_col': [1, 2, 3]
        })
        
        assert df['float64_col'].dtype == np.float64
        
        df_optimized = optimize_dataframe_dtypes(df)
        
        # Should be downcast to float32
        assert df_optimized['float64_col'].dtype == np.float32

    def test_optimize_dataframe_dtypes_integer_downcast(self):
        """Test that integer columns are downcast to smallest possible type."""
        df = pd.DataFrame({
            'large_int': [1, 2, 3],
            'small_int': [1, 2, 3]
        })
        
        df_optimized = optimize_dataframe_dtypes(df)
        
        # Should be downcast to int8 or int16
        assert df_optimized['large_int'].dtype in [np.int8, np.int16, np.int32]

    def test_optimize_dataframe_dtypes_category_conversion(self):
        """Test that low-cardinality object columns are converted to category."""
        df = pd.DataFrame({
            'low_card': ['A', 'B', 'A', 'B', 'A'],
            'high_card': ['x1', 'x2', 'x3', 'x4', 'x5']
        })
        
        df_optimized = optimize_dataframe_dtypes(df)
        
        # Low cardinality should be category
        assert df_optimized['low_card'].dtype.name == 'category'
        # High cardinality should remain object
        assert df_optimized['high_card'].dtype == object

    def test_stream_dataframe_in_batches(self):
        """Test streaming of CSV file in batches."""
        batch_count = 0
        total_rows = 0
        
        for batch in stream_dataframe_in_batches(self.test_csv_path, batch_size=100):
            batch_count += 1
            total_rows += len(batch)
            assert len(batch) <= 100
        
        assert batch_count == 10  # 1000 rows / 100 batch size
        assert total_rows == 1000

    def test_run_optimization_validation(self):
        """Test the optimization validation function."""
        report = run_optimization_validation()
        
        assert 'original_memory_mb' in report
        assert 'optimized_memory_mb' in report
        assert 'reduction_percent' in report
        assert 'status' in report
        assert report['status'] == 'passed'
        
        # Should have some memory reduction
        assert report['reduction_percent'] > 0

    def test_memory_limit_enforcement(self):
        """Test that memory limit is checked."""
        current_mem = get_current_memory_mb()
        
        # Current memory should be less than limit (7GB = 7168MB)
        assert current_mem < MEMORY_LIMIT_MB

    def test_optimization_report_generation(self):
        """Test that optimization report is generated correctly."""
        # Run validation
        report = run_optimization_validation()
        
        # Verify report structure
        assert isinstance(report, dict)
        assert 'status' in report
        assert report['status'] in ['passed', 'failed']

    def test_batch_streaming_memory_efficiency(self):
        """Test that batch streaming is more memory efficient than full load."""
        # Create a larger test file
        large_csv_path = os.path.join(self.temp_dir, 'large_data.csv')
        large_data = {
            'id': range(50000),
            'value': np.random.rand(50000)
        }
        pd.DataFrame(large_data).to_csv(large_csv_path, index=False)
        
        # Load full file
        full_df = pd.read_csv(large_csv_path)
        full_memory = full_df.memory_usage(deep=True).sum()
        
        # Stream and aggregate (simulate)
        streamed_memory = 0
        for batch in stream_dataframe_in_batches(large_csv_path, batch_size=1000):
            batch_memory = batch.memory_usage(deep=True).sum()
            streamed_memory = max(streamed_memory, batch_memory)
        
        # Streaming should use less peak memory
        assert streamed_memory < full_memory
