"""
Tests for the memory monitoring and optimization utilities.
"""
import os
import sys
import tempfile
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from src.memory_monitor import (
    get_current_memory_mb,
    check_memory_usage,
    force_gc,
    stream_dataframe,
    optimize_dataframe_dtypes,
    get_memory_profile,
    MEMORY_LIMIT_MB,
    MEMORY_WARNING_THRESHOLD_MB
)

class TestMemoryMonitor:
    """Tests for memory monitoring functions."""

    def test_get_current_memory_mb_returns_positive(self):
        """Test that get_current_memory_mb returns a positive value."""
        memory = get_current_memory_mb()
        assert memory > 0, "Memory usage should be positive"

    def test_check_memory_usage_below_threshold(self):
        """Test check_memory_usage returns True when below threshold."""
        # This should pass in normal conditions
        assert check_memory_usage(MEMORY_LIMIT_MB) is True

    def test_check_memory_usage_custom_threshold(self):
        """Test check_memory_usage with a custom threshold."""
        # Use a very high threshold to ensure it passes
        assert check_memory_usage(100000) is True

    def test_force_gc_returns_memory(self):
        """Test that force_gc returns current memory usage."""
        memory_before = get_current_memory_mb()
        memory_after = force_gc()
        # Memory after GC should be <= memory before (or very close)
        assert memory_after <= memory_before + 1, "GC should not increase memory significantly"

    def test_get_memory_profile_has_expected_keys(self):
        """Test that get_memory_profile returns expected keys."""
        profile = get_memory_profile()
        expected_keys = ['rss_mb', 'vms_mb', 'percent', 'num_threads']
        for key in expected_keys:
            assert key in profile, f"Profile should contain {key}"

    def test_stream_dataframe_yields_correct_chunks(self):
        """Test that stream_dataframe yields correct number of chunks."""
        df = pd.DataFrame({'a': range(100), 'b': range(100, 200)})
        chunks = list(stream_dataframe(df, chunk_size=25))
        assert len(chunks) == 4, "Should yield 4 chunks of 25 rows each"
        assert all(len(chunk) == 25 for chunk in chunks[:-1]), "All chunks except last should have 25 rows"

    def test_stream_dataframe_with_columns(self):
        """Test streaming with specific columns."""
        df = pd.DataFrame({'a': range(100), 'b': range(100, 200), 'c': range(200, 300)})
        chunks = list(stream_dataframe(df, chunk_size=50, columns=['a', 'c']))
        assert len(chunks) == 2
        assert all('a' in chunk.columns and 'c' in chunk.columns for chunk in chunks)
        assert all('b' not in chunk.columns for chunk in chunks)

    def test_optimize_dataframe_dtypes_int8(self):
        """Test that optimize_dataframe_dtypes downcasts to int8 when possible."""
        df = pd.DataFrame({'a': range(100)})
        optimized = optimize_dataframe_dtypes(df)
        # Values 0-99 fit in int8
        assert optimized['a'].dtype == np.int8, "Should downcast to int8"

    def test_optimize_dataframe_dtypes_float32(self):
        """Test that optimize_dataframe_dtypes downcasts to float32 when possible."""
        df = pd.DataFrame({'a': [1.0, 2.0, 3.0]})
        optimized = optimize_dataframe_dtypes(df)
        assert optimized['a'].dtype == np.float32, "Should downcast to float32"

    def test_optimize_dataframe_dtypes_categorical(self):
        """Test that optimize_dataframe_dtypes converts categories."""
        df = pd.DataFrame({'a': ['x', 'y', 'z', 'x', 'y'] * 20})
        optimized = optimize_dataframe_dtypes(df)
        assert str(optimized['a'].dtype) == 'category', "Should convert to category"

    def test_optimize_dataframe_dtypes_preserves_large_int(self):
        """Test that large integers are preserved as int64."""
        df = pd.DataFrame({'a': [2**40, 2**40 + 1, 2**40 + 2]})
        optimized = optimize_dataframe_dtypes(df)
        assert optimized['a'].dtype == np.int64, "Large integers should remain int64"

    def test_memory_monitor_integration(self):
        """Integration test: stream a large dataset and monitor memory."""
        # Create a moderately large DataFrame
        df = pd.DataFrame({
            'gene_id': range(10000),
            'expression': np.random.rand(10000),
            'condition': ['A'] * 5000 + ['B'] * 5000
        })
        
        total_rows = 0
        for chunk in stream_dataframe(df, chunk_size=1000):
            total_rows += len(chunk)
        
        assert total_rows == 10000, "Should process all rows"

    def test_memory_limit_constant(self):
        """Test that memory limit constants are set correctly."""
        assert MEMORY_LIMIT_MB == 6000, "Memory limit should be 6GB"
        assert MEMORY_WARNING_THRESHOLD_MB == 5000, "Warning threshold should be 5GB"

    def test_memory_profile_values_are_reasonable(self):
        """Test that memory profile values are within reasonable bounds."""
        profile = get_memory_profile()
        assert profile['rss_mb'] > 0, "RSS should be positive"
        assert profile['vms_mb'] >= profile['rss_mb'], "VMS should be >= RSS"
        assert 0 <= profile['percent'] <= 100, "Percent should be between 0 and 100"
        assert profile['num_threads'] > 0, "Should have at least one thread"