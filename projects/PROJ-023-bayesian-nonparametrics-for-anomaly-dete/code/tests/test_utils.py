"""
code/tests/test_utils.py

Unit tests for code/lib/utils.py
"""

import pytest
import numpy as np
import pandas as pd
from pathlib import Path
import tempfile
import os

# Import the module under test
from lib.utils import (
    set_seed,
    normalize_series,
    handle_missing_values,
    MemoryProfiler,
    get_memory_usage_mb,
    ensure_output_dir,
    DEFAULT_SEED,
    MEMORY_LIMIT_GB
)


class TestSeedPinning:
    def test_set_seed_reproducibility(self):
        """Test that setting the seed produces reproducible random numbers."""
        set_seed(42)
        val1 = np.random.random()
        
        set_seed(42)
        val2 = np.random.random()
        
        assert val1 == val2

    def test_set_seed_different_seeds(self):
        """Test that different seeds produce different random numbers."""
        set_seed(42)
        val1 = np.random.random()
        
        set_seed(123)
        val2 = np.random.random()
        
        assert val1 != val2


class TestNormalization:
    def test_standard_normalization(self):
        """Test standard (z-score) normalization."""
        data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        normalized, params = normalize_series(data, method='standard')
        
        # Mean should be approx 0, std approx 1
        assert np.isclose(normalized.mean(), 0.0, atol=1e-6)
        assert np.isclose(normalized.std(), 1.0, atol=1e-6)
        assert 'mean' in params
        assert 'std' in params

    def test_minmax_normalization(self):
        """Test min-max normalization."""
        data = pd.Series([10.0, 20.0, 30.0, 40.0, 50.0])
        normalized, params = normalize_series(data, method='minmax')
        
        # Min should be 0, max should be 1
        assert np.isclose(normalized.min(), 0.0, atol=1e-6)
        assert np.isclose(normalized.max(), 1.0, atol=1e-6)
        assert 'min' in params
        assert 'max' in params

    def test_standardization_with_precomputed_params(self):
        """Test normalization using pre-computed parameters."""
        train_data = pd.Series([1.0, 2.0, 3.0, 4.0, 5.0])
        _, train_params = normalize_series(train_data, method='standard')
        
        test_data = pd.Series([2.0, 4.0])
        normalized_test, _ = normalize_series(test_data, method='standard', fit_params=train_params)
        
        # Verify scaling is consistent
        expected_mean = train_params['mean']
        expected_std = train_params['std']
        expected_val = (2.0 - expected_mean) / expected_std
        assert np.isclose(normalized_test.iloc[0], expected_val)

    def test_constant_series_standard(self):
        """Test normalization of a constant series (std=0)."""
        data = pd.Series([5.0, 5.0, 5.0])
        normalized, params = normalize_series(data, method='standard')
        # Should not crash, std should be 1.0 in params, result 0.0
        assert params['std'] == 1.0
        assert all(normalized == 0.0)

    def test_constant_series_minmax(self):
        """Test normalization of a constant series (max=min)."""
        data = pd.Series([5.0, 5.0, 5.0])
        normalized, params = normalize_series(data, method='minmax')
        # Should not crash
        assert all(normalized == 0.0)


class TestMissingValueHandling:
    def test_interpolate_linear(self):
        """Test linear interpolation."""
        data = pd.Series([1.0, np.nan, np.nan, 4.0])
        cleaned = handle_missing_values(data, policy='interpolate', method='linear')
        assert not cleaned.isnull().any()
        assert cleaned.iloc[1] == 2.0
        assert cleaned.iloc[2] == 3.0

    def test_ffill(self):
        """Test forward fill."""
        data = pd.Series([1.0, np.nan, np.nan, 4.0])
        cleaned = handle_missing_values(data, policy='ffill')
        assert not cleaned.isnull().any()
        assert cleaned.iloc[1] == 1.0
        assert cleaned.iloc[2] == 1.0

    def test_bfill(self):
        """Test backward fill."""
        data = pd.Series([1.0, np.nan, np.nan, 4.0])
        cleaned = handle_missing_values(data, policy='bfill')
        assert not cleaned.isnull().any()
        assert cleaned.iloc[1] == 4.0
        assert cleaned.iloc[2] == 4.0

    def test_drop(self):
        """Test dropping NaNs."""
        data = pd.Series([1.0, np.nan, 3.0, np.nan])
        cleaned = handle_missing_values(data, policy='drop')
        assert len(cleaned) == 2
        assert list(cleaned) == [1.0, 3.0]

    def test_zero_fill(self):
        """Test filling with zeros."""
        data = pd.Series([1.0, np.nan, 3.0])
        cleaned = handle_missing_values(data, policy='zero')
        assert not cleaned.isnull().any()
        assert cleaned.iloc[1] == 0.0

    def test_no_missing_values(self):
        """Test that clean data passes through unchanged."""
        data = pd.Series([1.0, 2.0, 3.0])
        cleaned = handle_missing_values(data, policy='interpolate')
        assert list(cleaned) == [1.0, 2.0, 3.0]

    def test_interpolate_edge_cases(self):
        """Test interpolation with NaNs at edges."""
        data = pd.Series([np.nan, 2.0, 3.0, np.nan])
        cleaned = handle_missing_values(data, policy='interpolate', method='linear')
        # Edges should be filled with 0 as per implementation fallback
        assert not cleaned.isnull().any()


class TestMemoryProfiler:
    def test_context_manager(self):
        """Test MemoryProfiler as a context manager."""
        with MemoryProfiler(verbose=False) as profiler:
            _ = [i for i in range(10000)]
            current, peak = profiler.stop()
            assert peak >= current
            assert current > 0

    def test_limit_enforcement(self):
        """Test that MemoryProfiler raises on limit exceed (mocked limit)."""
        # Set a tiny limit to trigger failure
        profiler = MemoryProfiler(limit_gb=0.0000001, verbose=False) # ~0.1KB
        profiler.start()
        
        # Allocate some memory
        _ = [i for i in range(100000)]
        
        with pytest.raises(MemoryError):
            profiler.stop()

    def test_check_current(self):
        """Test current memory check."""
        profiler = MemoryProfiler(verbose=False)
        profiler.start()
        # Should not raise
        mem = profiler.check_current()
        assert mem >= 0
        profiler.stop()

    def test_reentrant_start_stop(self):
        """Test that calling start twice doesn't break things."""
        profiler = MemoryProfiler(verbose=False)
        profiler.start()
        profiler.start() # Should be no-op
        profiler.stop()
        profiler.stop() # Should be no-op or handled gracefully


class TestOutputDir:
    def test_ensure_output_dir_creates(self):
        """Test that ensure_output_dir creates missing directories."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "subdir" / "file.csv"
            result_dir = ensure_output_dir(path)
            assert result_dir.exists()
            assert result_dir == Path(tmpdir) / "subdir"

    def test_ensure_output_dir_exists(self):
        """Test that ensure_output_dir works if dir exists."""
        with tempfile.TemporaryDirectory() as tmpdir:
            path = Path(tmpdir) / "file.csv"
            result_dir = ensure_output_dir(path)
            assert result_dir.exists()
            assert result_dir == Path(tmpdir)

class TestGetMemoryUsage:
    def test_get_memory_usage_returns_number(self):
        """Test that get_memory_usage_mb returns a float."""
        mem = get_memory_usage_mb()
        assert isinstance(mem, float)
        assert mem >= 0.0