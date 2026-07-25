import os
import sys
import json
import tempfile
import pytest
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / 'code'))

from benchmark import run_phase_benchmark, get_memory_usage_mb, get_peak_memory_mb, save_benchmark_report

def dummy_phase_func(*args, **kwargs):
    """A dummy function for benchmarking."""
    time.sleep(0.1)  # Simulate work
    return True

def test_run_phase_benchmark_success():
    """Test that run_phase_benchmark returns a success result with timing."""
    import time
    result = run_phase_benchmark("test_phase", dummy_phase_func)
    
    assert result['phase'] == 'test_phase'
    assert result['status'] == 'success'
    assert 'duration_ms' in result
    assert result['duration_ms'] >= 100  # Should be at least 100ms due to sleep
    assert 'peak_memory_mb' in result

def test_run_phase_benchmark_failure():
    """Test that run_phase_benchmark handles exceptions gracefully."""
    def failing_func(*args, **kwargs):
        raise ValueError("Simulated error")
    
    result = run_phase_benchmark("fail_phase", failing_func)
    
    assert result['phase'] == 'fail_phase'
    assert result['status'] == 'failed'
    assert 'error' in result
    assert 'Simulated error' in result['error']

def test_save_benchmark_report(tmp_path):
    """Test that save_benchmark_report writes valid JSON."""
    report = {
        "total_runtime": 100.5,
        "phase_timings": {"parser": 50.2},
        "timestamp": "2023-01-01"
    }
    output_path = tmp_path / "benchmark_test.json"
    
    save_benchmark_report(report, str(output_path))
    
    assert output_path.exists()
    with open(output_path) as f:
        data = json.load(f)
    
    assert data['total_runtime'] == 100.5
    assert data['phase_timings']['parser'] == 50.2

def test_memory_functions():
    """Test memory usage functions."""
    # Start tracing
    import tracemalloc
    tracemalloc.start()
    
    mem = get_memory_usage_mb()
    peak = get_peak_memory_mb()
    
    assert isinstance(mem, float)
    assert isinstance(peak, float)
    
    tracemalloc.stop()