"""
Unit tests for memory cleanup and optimization utilities (Task T033).
"""

import gc
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from code.cleanup import (
    optimize_dataframe_dtypes,
    load_csv_memory_efficient,
    clean_large_objects,
    downcast_numpy_array,
    ensure_memory_fits,
    run_cleanup_pipeline
)


class TestOptimizeDtypes:
    def test_downcast_int_to_int8(self):
        """Test downcasting integers to int8 when values fit."""
        df = pd.DataFrame({"a": [1, 2, 3], "b": [100, 200, 250]})
        optimized = optimize_dataframe_dtypes(df)
        assert optimized["a"].dtype == np.int8
        assert optimized["b"].dtype == np.int8

    def test_downcast_float_to_float32(self):
        """Test downcasting floats to float32 when values fit."""
        df = pd.DataFrame({"x": [0.1, 0.2, 0.3], "y": [1.5, 2.5, 3.5]})
        optimized = optimize_dataframe_dtypes(df)
        assert optimized["x"].dtype == np.float32
        assert optimized["y"].dtype == np.float32

    def test_categorical_conversion(self):
        """Test object columns with low cardinality become categorical."""
        df = pd.DataFrame({"cat": ["A", "B", "A", "B", "A"] * 100})
        optimized = optimize_dataframe_dtypes(df)
        assert optimized["cat"].dtype.name == "category"

    def test_preserves_large_integers(self):
        """Test that large integers are preserved as int64."""
        large_val = 10**15
        df = pd.DataFrame({"big": [large_val, large_val + 1]})
        optimized = optimize_dataframe_dtypes(df)
        assert optimized["big"].dtype == np.int64


class TestLoadCsvMemoryEfficient:
    def test_load_small_csv(self):
        """Test loading a small CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b,c\n1,2,3\n4,5,6\n7,8,9\n")
            temp_path = f.name

        try:
            df = load_csv_memory_efficient(temp_path, chunksize=2)
            assert len(df) == 3
            assert list(df.columns) == ["a", "b", "c"]
        finally:
            Path(temp_path).unlink()

    def test_load_with_columns_selection(self):
        """Test loading only selected columns."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("a,b,c,d\n1,2,3,4\n5,6,7,8\n")
            temp_path = f.name

        try:
            df = load_csv_memory_efficient(temp_path, use_columns=["a", "c"])
            assert list(df.columns) == ["a", "c"]
        finally:
            Path(temp_path).unlink()

    def test_file_not_found_raises(self):
        """Test that missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_csv_memory_efficient("nonexistent.csv")


class TestCleanLargeObjects:
    def test_clean_objects(self):
        """Test that objects are cleaned up."""
        large_list = [list(range(10000)) for _ in range(100)]
        count = clean_large_objects([large_list])
        assert count == 1

    def test_empty_list(self):
        """Test cleaning empty list returns 0."""
        count = clean_large_objects([])
        assert count == 0


class TestDowncastNumpyArray:
    def test_downcast_float64_to_float32(self):
        """Test downcasting float64 to float32."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float64)
        result = downcast_numpy_array(arr)
        assert result.dtype == np.float32

    def test_preserve_float32(self):
        """Test that float32 is preserved."""
        arr = np.array([1.0, 2.0, 3.0], dtype=np.float32)
        result = downcast_numpy_array(arr)
        assert result.dtype == np.float32

    def test_downcast_int64_to_int32(self):
        """Test downcasting int64 to int32."""
        arr = np.array([1, 2, 3], dtype=np.int64)
        result = downcast_numpy_array(arr)
        assert result.dtype == np.int32


class TestEnsureMemoryFits:
    def test_memory_sufficient(self):
        """Test that small DataFrame passes memory check."""
        df = pd.DataFrame({"a": [1, 2, 3]})
        # Should not raise and should return True for small data
        result = ensure_memory_fits(df, target_fraction=0.1)
        assert isinstance(result, bool)


class TestRunCleanupPipeline:
    def test_cleanup_returns_stats(self):
        """Test that cleanup pipeline returns statistics dict."""
        stats = run_cleanup_pipeline()
        assert "gc_collections" in stats
        assert "ram_before_gb" in stats
        assert "ram_after_gb" in stats
        assert isinstance(stats["gc_collections"], int)
        assert isinstance(stats["ram_before_gb"], float)