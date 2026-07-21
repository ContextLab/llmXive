import pytest
import json
import os
from pathlib import Path
import pandas as pd
import numpy as np

from perf_optimizer import (
    ensure_cache_dir,
    get_cache_path,
    compute_input_hash,
    cached_operation,
    process_trajectories_chunked,
    vectorized_statistical_tests
)

@pytest.fixture
def sample_trajectories():
    """Generate sample trajectory data for testing."""
    return [
        {
            "id": f"traj_{i}",
            "turns": [{"entropy": np.random.rand(), "moves": ["a", "b", "c"]}]
        }
        for i in range(10)
    ]

class TestCacheFunctions:
    def test_ensure_cache_dir(self):
        """Test that cache directory is created."""
        path = ensure_cache_dir()
        assert path.exists()
        assert path.is_dir()

    def test_get_cache_path(self):
        """Test getting specific cache subdirectory."""
        path = get_cache_path("test_subdir")
        assert "test_subdir" in str(path)
        assert path.exists()

    def test_compute_input_hash(self):
        """Test hash computation consistency."""
        data1 = {"key": "value", "num": 42}
        data2 = {"key": "value", "num": 42}
        data3 = {"key": "value", "num": 43}
        
        hash1 = compute_input_hash(data1)
        hash2 = compute_input_hash(data2)
        hash3 = compute_input_hash(data3)
        
        assert hash1 == hash2
        assert hash1 != hash3
        assert len(hash1) == 64  # SHA256 hex length

class TestChunkedProcessing:
    def test_chunked_processing(self, sample_trajectories):
        """Test that chunked processing works correctly."""
        def dummy_processor(t):
            return t["id"]
        
        results = process_trajectories_chunked(sample_trajectories, dummy_processor, chunk_size=3)
        
        assert len(results) == len(sample_trajectories)
        assert all(isinstance(r, str) for r in results)

    def test_chunked_processing_empty(self):
        """Test chunked processing with empty list."""
        def dummy_processor(t):
            return t["id"]
        
        results = process_trajectories_chunked([], dummy_processor, chunk_size=3)
        assert results == []

class TestVectorizedStats:
    def test_vectorized_statistical_tests(self):
        """Test vectorized statistical test implementation."""
        win_rates_dyn = [0.8, 0.7, 0.9, 0.6]
        win_rates_stat = [0.5, 0.6, 0.5, 0.5]
        tokens_dyn = [100, 150, 120, 110]
        tokens_stat = [200, 250, 220, 210]
        
        results = vectorized_statistical_tests(
            win_rates_dyn, win_rates_stat, tokens_dyn, tokens_stat
        )
        
        assert 'win_rate' in results
        assert 'token_usage' in results
        assert 'bonferroni_corrected' in results
        assert results['win_rate']['mean_diff'] > 0  # Dynamic should be better
        assert results['token_usage']['mean_diff'] < 0  # Dynamic should use fewer tokens

    def test_vectorized_statistical_tests_empty(self):
        """Test vectorized stats with empty lists."""
        results = vectorized_statistical_tests([], [], [], [])
        
        assert 'win_rate' in results
        assert 'token_usage' in results
        assert 'bonferroni_corrected' in results

class TestPerformanceConstraints:
    def test_cache_performance(self, sample_trajectories, tmp_path):
        """Test that caching improves performance."""
        # Change cache dir for test
        original_cache = Path("data/.cache")
        test_cache = tmp_path / "test_cache"
        
        # Mock the cache path
        import perf_optimizer
        original_get_cache_path = perf_optimizer.get_cache_path
        
        def mock_get_cache_path(subdir="default"):
            return test_cache / subdir
        
        perf_optimizer.get_cache_path = mock_get_cache_path
        ensure_cache_dir()
        
        try:
            @cached_operation("test_perf", force_refresh=False)
            def slow_operation(x):
                time.sleep(0.1)
                return x * 2
            
            import time
            
            # First call (no cache)
            start = time.time()
            result1 = slow_operation(5)
            time1 = time.time() - start
            
            # Second call (with cache)
            start = time.time()
            result2 = slow_operation(5)
            time2 = time.time() - start
            
            assert result1 == result2
            assert time2 < time1 * 0.5  # Cached should be significantly faster
        finally:
            perf_optimizer.get_cache_path = original_get_cache_path
