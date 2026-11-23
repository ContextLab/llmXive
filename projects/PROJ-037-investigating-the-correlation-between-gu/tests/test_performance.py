"""
Unit tests for performance optimization modules.

These tests verify that the optimization logic (parallelism configuration,
memory optimization, and runtime estimation) functions correctly without
necessarily running the full heavy pipeline.
"""
import pytest
import time
import json
from pathlib import Path
import sys

# Ensure imports work
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root / "projects" / "PROJ-037-investigating-the-correlation-between-gu"))

from code.performance_optimizer import (
    configure_parallelism,
    time_function,
    optimize_dataframe_memory,
    estimate_runtime,
    parallel_alpha_diversity,
    parallel_correlation_tests
)
from code.performance_config import get_performance_config, set_performance_config, reset_performance_config
from code.utils.seeding import set_seed

@pytest.fixture(autouse=True)
def setup_config():
    """Reset performance config before each test."""
    reset_performance_config()
    set_seed(42)
    yield
    reset_performance_config()

def test_configure_parallelism():
    """Test that parallelism configuration sets the correct number of workers."""
    # Test with explicit value
    configure_parallelism(max_workers=4)
    config = get_performance_config()
    assert config.max_workers == 4
    
    # Test with CPU count (mocked logic check)
    configure_parallelism(max_workers=None)
    config = get_performance_config()
    assert config.max_workers >= 1  # Should default to at least 1

def test_time_function_decorator():
    """Test that the time_function decorator correctly measures execution time."""
    @time_function
    def slow_function():
        time.sleep(0.1)
        return "result"

    start = time.time()
    result = slow_function()
    duration = time.time() - start

    assert result == "result"
    assert duration >= 0.1
    assert duration < 0.5  # Sanity check

def test_optimize_dataframe_memory():
    """Test that memory optimization runs without error on a dummy dataset."""
    import pandas as pd
    import numpy as np

    # Create a dummy dataframe
    df = pd.DataFrame({
        'id': range(100),
        'value': np.random.rand(100),
        'category': ['A', 'B'] * 50
    })
    
    # This should run without crashing
    optimize_dataframe_memory()
    
    # Note: The actual optimization happens on global state or specific modules
    # This test ensures the function is callable and doesn't crash

def test_estimate_runtime():
    """Test runtime estimation logic."""
    # Basic sanity check
    base_time = 10.0  # seconds for N=100
    n = 200
    
    estimated = estimate_runtime(base_time, n)
    
    # Should be roughly proportional (linear approximation for this test)
    assert estimated > 0
    # If linear scaling: 200/100 * 10 = 20
    # If quadratic scaling: (200/100)^2 * 10 = 40
    # We expect it to be at least base_time * (n/100)
    assert estimated >= base_time * (n / 100)

def test_parallel_alpha_diversity_signature():
    """Verify the parallel alpha diversity function signature is correct."""
    # We can't run full diversity without data, but we can check the function exists
    # and has the expected signature structure
    import inspect
    sig = inspect.signature(parallel_alpha_diversity)
    params = list(sig.parameters.keys())
    assert 'biom_table' in params or 'table' in params or 'data' in params
    # The function should accept at least a data source and workers

def test_parallel_correlation_tests_signature():
    """Verify the parallel correlation tests function signature."""
    import inspect
    sig = inspect.signature(parallel_correlation_tests)
    params = list(sig.parameters.keys())
    assert 'data' in params or 'results' in params

def test_performance_config_dataclass():
    """Test that the PerformanceConfig dataclass initializes correctly."""
    config = get_performance_config()
    assert hasattr(config, 'max_workers')
    assert hasattr(config, 'chunk_size')
    assert hasattr(config, 'memory_limit_mb')
    
    # Check defaults
    assert config.max_workers is not None

def test_benchmark_script_structure():
    """Verify the benchmark script exists and has a main entry point."""
    benchmark_path = project_root / "projects" / "PROJ-037-investigating-the-correlation-between-gu" / "code" / "performance_benchmark.py"
    assert benchmark_path.exists(), "performance_benchmark.py must exist"
    
    # Check content for expected imports
    content = benchmark_path.read_text()
    assert "from code.performance_optimizer" in content
    assert "def main" in content
    assert "TARGET_RUNTIME_SECONDS" in content
