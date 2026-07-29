"""
Pytest configuration for the Cortical Column LLMs project.

This module configures:
- pytest-timeout settings for unit tests (120s) and integration tests (600s).
- Resource monitoring hooks using psutil to track CPU and memory usage.
- Deterministic seeding via environment variable injection.
- Core pinning enforcement (FR-004) and RSS memory assertions (SC-005).
"""

import os
import sys
import time
import resource
from typing import Generator, Optional, Dict, Any, Set

import pytest
import psutil

# Configuration constants
# Unit tests: 2 minutes default
UNIT_TEST_TIMEOUT = 120
# Integration tests: 10 minutes default
INTEGRATION_TEST_TIMEOUT = 600
# Max memory per process (in MB) - strict limit for FR-004
MAX_MEMORY_MB = 7168  # 7 GB

# Allowed CPU cores (0-3) for FR-004
ALLOWED_CORES: Set[int] = {0, 1, 2, 3}

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
def enforce_resource_constraints(request) -> Generator[Optional[Dict[str, Any]], None, None]:
    """
    Fixture to enforce FR-004 (Core Pinning) and SC-005 (Memory Limits)
    before and after each test.

    1. Verifies the process is pinned to allowed cores (0-3).
    2. Asserts RSS memory usage stays below 7GB.
    """
    # --- PRE-TEST: Verify Core Pinning ---
    try:
        current_process = psutil.Process(os.getpid())
        affinity_mask = current_process.cpu_affinity()

        # Convert list to set for comparison
        active_cores = set(affinity_mask)

        # Check if active cores are a subset of allowed cores
        if not active_cores.issubset(ALLOWED_CORES):
            # Allow tests to opt-out if they explicitly need more cores (rare)
            if not request.node.get_closest_marker("allow_unpinned"):
                pytest.fail(
                    f"Core Pinning Violation: Test {request.node.name} is running on cores "
                    f"{active_cores}, but must be pinned to subset of {ALLOWED_CORES} "
                    f"per FR-004. Pin via 'taskset -c 0-3 pytest' or use --strict-markers."
                )
    except AttributeError:
        # Windows does not support cpu_affinity in psutil in the same way
        # Skip check on non-Unix platforms for CI compatibility, but warn
        if sys.platform != "win32":
            pytest.warns(
                UserWarning,
                "Could not verify CPU affinity (psutil.cpu_affinity not supported or failed)."
            )

    # --- PRE-TEST: Initialize Monitoring ---
    start_time = time.perf_counter()
    process = psutil.Process(os.getpid())
    start_mem = process.memory_info().rss / (1024 * 1024)  # MB

    yield None

    # --- POST-TEST: Verify Memory Constraints ---
    end_time = time.perf_counter()
    current_mem = process.memory_info().rss / (1024 * 1024)
    peak_mem = current_mem

    # Try to get max RSS if available (Unix)
    try:
        rusage = resource.getrusage(resource.RUSAGE_SELF)
        # Normalize to MB: on Linux ru_maxrss is KB, on macOS it is bytes.
        if sys.platform == "darwin":
            max_rss_mb = rusage.ru_maxrss / (1024 * 1024)
        else:
            max_rss_mb = rusage.ru_maxrss / 1024

        peak_mem = max(start_mem, max_rss_mb, current_mem)
    except Exception:
        pass  # Fallback to current measurement if resource module fails

    # Assert strict memory limit (SC-005)
    if peak_mem > MAX_MEMORY_MB:
        pytest.fail(
            f"Memory Limit Exceeded: Test {request.node.name} peaked at {peak_mem:.2f} MB, "
            f"exceeding the strict limit of {MAX_MEMORY_MB} MB (7GB) per FR-004/SC-005."
        )

    # Log warning if close to limit (optional telemetry)
    if peak_mem > (MAX_MEMORY_MB * 0.9):
        pytest.warns(
            UserWarning,
            f"Test {request.node.name} used {peak_mem:.2f} MB memory, approaching limit of {MAX_MEMORY_MB} MB."
        )

    # Store stats in a custom attribute for potential reporting plugins
    if not hasattr(sys, "pytest_resource_stats"):
        sys.pytest_resource_stats = []

    sys.pytest_resource_stats.append({
        "test_name": request.node.name,
        "elapsed": end_time - start_time,
        "peak_memory_mb": peak_mem,
        "cores_used": set(psutil.Process(os.getpid()).cpu_affinity())
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
            for stat in reversed(sys.pytest_resource_stats):
                if stat["test_name"] == item.name:
                    report.pytest_stats = stat
                    break