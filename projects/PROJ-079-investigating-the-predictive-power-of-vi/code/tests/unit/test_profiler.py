"""
Unit tests for the profiler module.
"""
import pytest
import time
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.profiler import profile_function, cache_results, log_timing_results, _timing_store, _call_counts

@profile_function
def mock_slow_function(x):
    time.sleep(0.1)
    return x * 2

@cache_results
def mock_cached_function(x):
    return x * 2

def test_profile_function_tracks_time():
    _timing_store.clear()
    _call_counts.clear()
    
    result = mock_slow_function(5)
    assert result == 10
    assert "mock_slow_function" in _timing_store
    assert _call_counts["mock_slow_function"] == 1
    assert _timing_store["mock_slow_function"] >= 0.1

def test_cache_results_caches():
    with patch("src.profiler.logger") as mock_logger:
        result1 = mock_cached_function(10)
        result2 = mock_cached_function(10)
        
        assert result1 == 20
        assert result2 == 20
        # Should have one cache miss and one hit
        calls = [call[0][0] for call in mock_logger.debug.call_args_list]
        assert any("Cache miss" in c for c in calls)
        assert any("Cache hit" in c for c in calls)

def test_log_timing_results_creates_file():
    _timing_store.clear()
    _call_counts.clear()
    _timing_store["test_func"] = 1.0
    _call_counts["test_func"] = 1

    with tempfile.TemporaryDirectory() as tmpdir:
        # Temporarily override ARTIFACTS_PATH for the test
        with patch("src.profiler.ARTIFACTS_PATH", Path(tmpdir)):
            with patch("src.profiler.TIMING_LOG_PATH", Path(tmpdir) / "timing.log"):
                success = log_timing_results()
                assert success is True
                
                log_path = Path(tmpdir) / "timing.log"
                assert log_path.exists()
                
                with open(log_path) as f:
                    data = json.load(f)
                
                assert "timestamp" in data
                assert "total_runtime_seconds" in data
                assert "functions" in data
                assert "test_func" in data["functions"]
                assert data["functions"]["test_func"]["total_seconds"] == 1.0
                assert data["functions"]["test_func"]["call_count"] == 1

def test_log_timing_results_warns_on_exceed():
    _timing_store.clear()
    _call_counts.clear()
    _timing_store["slow"] = 10000.0 # > 4 hours
    _call_counts["slow"] = 1

    with tempfile.TemporaryDirectory() as tmpdir:
        with patch("src.profiler.ARTIFACTS_PATH", Path(tmpdir)):
            with patch("src.profiler.TIMING_LOG_PATH", Path(tmpdir) / "timing.log"):
                with patch("src.profiler.MAX_RUNTIME_HOURS", 1):
                    success = log_timing_results()
                    assert success is False