"""
Unit tests for performance utilities.
"""
import pytest
import numpy as np
import pandas as pd
import tempfile
import os
from pathlib import Path

from code.utils.performance_utils import (
    MemoryMonitor, load_parquet_chunked, batch_process,
    optimized_shuffle, vectorized_correlation, gc_collect_if_needed
)

class TestMemoryMonitor:
    def test_init(self):
        monitor = MemoryMonitor(limit_gb=1.0)
        assert monitor.limit_mb == 1024
        assert monitor.log_entries == []

    def test_start_stop(self):
        monitor = MemoryMonitor()
        monitor.start()
        # Do nothing
        monitor.stop()
        # Should not raise

class TestOptimizedShuffle:
    def test_shuffle_changes_order(self):
        arr = np.arange(100)
        shuffled = optimized_shuffle(arr, random_state=42)
        assert not np.array_equal(arr, shuffled)

    def test_shuffle_preserves_values(self):
        arr = np.array([1, 2, 3, 4, 5])
        shuffled = optimized_shuffle(arr, random_state=123)
        assert sorted(shuffled) == sorted(arr)

class TestVectorizedCorrelation:
    def test_perfect_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([2, 4, 6, 8, 10])
        corr = vectorized_correlation(x, y)
        assert np.isclose(corr, 1.0)

    def test_no_correlation(self):
        x = np.array([1, 2, 3, 4, 5])
        y = np.array([5, 1, 4, 2, 3])
        # Not necessarily zero, but testing function runs
        corr = vectorized_correlation(x, y)
        assert -1.0 <= corr <= 1.0

class TestBatchProcess:
    def test_batch_process(self):
        def double(x):
            return x * 2
        
        items = [1, 2, 3, 4, 5]
        results = batch_process(items, double, batch_size=2)
        assert results == [2, 4, 6, 8, 10]

class TestLoadParquetChunked:
    def test_load_parquet(self):
        # Create a temporary parquet file
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "test.parquet"
            df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
            df.to_parquet(path)
            
            loaded_df = load_parquet_chunked(path)
            assert len(loaded_df) == 3
            assert "a" in loaded_df.columns
            assert "b" in loaded_df.columns
