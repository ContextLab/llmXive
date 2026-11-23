"""
Pytest configuration and fixtures for llmXive project.
Enforces CPU resource limits and provides test utilities.
"""
import pytest
import os
import sys
from pathlib import Path
import tempfile
import json
import threading
import time
from typing import Generator, Any, Dict

# Configure CPU limits for all tests
# Ensure we only use 1 thread to simulate CPU-constrained environment
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["OPENBLAS_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"
os.environ["VECLIB_MAXIMUM_THREADS"] = "1"
os.environ["NUMEXPR_NUM_THREADS"] = "1"

# Define CPU limit marker
cpu_limit_marker = "cpu_limit"

@pytest.fixture(scope="session", autouse=True)
def enforce_cpu_limits():
    """
    Autouse fixture to enforce CPU resource limits for the entire test session.
    Ensures tests run within memory and thread constraints.
    """
    # Log CPU limit enforcement
    print("\n[CPU LIMIT ENFORCEMENT]")
    print(f"  OMP_NUM_THREADS: {os.environ.get('OMP_NUM_THREADS')}")
    print(f"  OPENBLAS_NUM_THREADS: {os.environ.get('OPENBLAS_NUM_THREADS')}")
    print(f"  MKL_NUM_THREADS: {os.environ.get('MKL_NUM_THREADS')}")
    print("  Enforcing 1 thread for CPU-bound operations\n")

    yield

    print("[CPU LIMIT ENFORCEMENT] Session complete\n")

@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """
    Creates a temporary directory for data files during tests.
    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory(prefix="llmxive_test_data_") as tmpdir:
        data_path = Path(tmpdir)
        # Create required subdirectories
        (data_path / "raw").mkdir(parents=True, exist_ok=True)
        (data_path / "features").mkdir(parents=True, exist_ok=True)
        (data_path / "baseline").mkdir(parents=True, exist_ok=True)
        (data_path / "evaluation").mkdir(parents=True, exist_ok=True)
        yield data_path

@pytest.fixture
def temp_model_dir() -> Generator[Path, None, None]:
    """
    Creates a temporary directory for model checkpoints during tests.
    Automatically cleaned up after test completion.
    """
    with tempfile.TemporaryDirectory(prefix="llmxive_test_model_") as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_manifest() -> Dict[str, Any]:
    """
    Provides a sample manifest.json structure for testing.
    """
    return {
        "version": "1.0",
        "total_frames": 1000,
        "total_duration_seconds": 33.33,
        "chunks": [
            {
                "id": "chunk_001",
                "start_frame": 0,
                "end_frame": 500,
                "duration_seconds": 16.67,
                "path": "data/raw/chunk_001.jsonl"
            },
            {
                "id": "chunk_002",
                "start_frame": 500,
                "end_frame": 1000,
                "duration_seconds": 16.66,
                "path": "data/raw/chunk_002.jsonl"
            }
        ],
        "metadata": {
            "generator_version": "1.0.0",
            "timestamp": "2024-01-01T00:00:00Z"
        }
    }

@pytest.fixture(autouse=True)
def setup_test_environment():
    """
    Setup and teardown for each test.
    Ensures clean environment for every test case.
    """
    # Save original environment
    original_env = os.environ.copy()
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)

def pytest_configure(config):
    """
    Configure pytest markers and settings.
    """
    config.addinivalue_line(
        "markers", "cpu_limit: mark test to enforce CPU resource limits"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running (>30s)"
    )
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "ci_subset: mark test to run data subset for CI"
    )

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """
    Hook to enforce CPU limits on tests marked with cpu_limit marker.
    """
    if item.get_closest_marker(cpu_limit_marker):
        # Additional checks for CPU-limited tests
        import psutil
        process = psutil.Process(os.getpid())
        
        # Log current memory usage
        mem_info = process.memory_info()
        print(f"\n[TEST START] {item.name}")
        print(f"  Current RSS Memory: {mem_info.rss / 1024 / 1024:.2f} MB")
        
        # Assert we're within limits (6GB = 6144 MB)
        assert mem_info.rss < 6 * 1024 * 1024 * 1024, \
            f"Memory limit exceeded: {mem_info.rss / 1024 / 1024:.2f} MB > 6GB"