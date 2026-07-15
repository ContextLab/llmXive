"""
Pytest configuration for the Cortical Column LLMs project.

This module configures:
- pytest-timeout settings for unit tests (120s) and integration tests (600s).
- Resource monitoring hooks using psutil to track CPU and memory usage.
- Deterministic seeding via environment variable injection.
"""

import os
import sys
import time
import resource
from typing import Generator, Optional

import pytest
import psutil

# Configuration constants
# Unit tests: 2 minutes default
UNIT_TEST_TIMEOUT = 120
# Integration tests: 10 minutes default
INTEGRATION_TEST_TIMEOUT = 600
# Max memory per process (in MB) - soft limit for warning, hard limit for abort
MAX_MEMORY_MB = 8192

# Ensure deterministic behavior if a seed is provided via env
if "PYTEST_RANDOM_SEED" in os.environ:
    import random
    import numpy as np
    seed = int(os.environ["PYTEST_RANDOM_SEED"])
    random.seed(seed)
    np.random.seed(seed)
    os.environ["PYTHONHASHSEED"] = str(seed)


def pytest_configure(config):
    """
    Register custom markers and configure timeouts.
    """
    config.addinivalue_line(
        "markers", "timeout: override default timeout for a specific test."
    )
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')."
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests (longer timeout)."
    )


def pytest_collection_modifyitems(config, items):
    """
    Automatically apply timeouts based on markers or file path.
    """
    for item in items:
        # Check for explicit timeout marker
        timeout_mark = item.get_closest_marker("timeout")
        if timeout_mark:
            timeout = int(timeout_mark.args[0]) if timeout_mark.args else 60
            item.add_marker(pytest.mark.timeout(timeout))
            continue

        # Check for integration marker
        if item.get_closest_marker("integration"):
            # Default 10 minutes for integration tests
            item.add_marker(pytest.mark.timeout(INTEGRATION_TEST_TIMEOUT))
        else:
            # Default 2 minutes for unit tests
            item.add_marker(pytest.mark.timeout(UNIT_TEST_TIMEOUT))


@pytest.fixture(autouse=True)
def setup_resource_monitoring() -> Generator[Optional[dict], None, None]:
    """
    Fixture to monitor resource usage (CPU time, memory) for each test.
    Records peak memory usage in the test context.
    """
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)  # MB
    start_time = time.perf_counter()

    yield None

    # Teardown: Check resources
    end_time = time.perf_counter()
    current_mem = process.memory_info().rss / (1024 * 1024)
    peak_mem = process.memory_info().rss / (1024 * 1024)  # Approximation via rss

    # Try to get max RSS if available (Unix)
    try:
        # resource module gives max RSS in bytes
        max_rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024  # KB to MB
        peak_mem = max(max_mem, max_rss)
    except Exception:
        pass  # Fallback to current measurement if resource module fails

    # Log warning if memory exceeds threshold
    if peak_mem > MAX_MEMORY_MB:
        pytest.warns(
            UserWarning,
            f"Test used {peak_mem:.2f} MB memory, exceeding limit of {MAX_MEMORY_MB} MB."
        )

    # Store stats in a custom attribute for potential reporting plugins
    if hasattr(sys, "pytest_resource_stats"):
        sys.pytest_resource_stats.append({
            "test_name": str(request.node.name) if "request" in locals() else "unknown",
            "elapsed": end_time - start_time,
            "peak_memory_mb": peak_mem
        })


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """
    Hook to capture test execution time and resource usage in the report.
    """
    outcome = yield
    report = outcome.get_result()

    if report.when == "call":
        # Attach custom stats if available
        if hasattr(sys, "pytest_resource_stats"):
            # Find the last entry for this test
            # In a real robust implementation, we'd map test IDs to stats
            pass