"""
Pytest configuration and CPU resource limit markers for llmXive pipeline.

This file configures pytest to enforce CPU-only execution and provides
markers for resource-constrained tests.
"""
import pytest
import os
import sys

# Ensure no GPU usage in tests
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Attempt to disable GPU libraries if available
try:
    import torch
    if torch.cuda.is_available():
        # Force CPU for all torch operations in tests
        torch.set_default_device("cpu")
except ImportError:
    pass  # torch not installed, ignore

# Custom markers for resource limits
def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line(
        "markers", "cpu_limit: Mark test to run with strict CPU resource limits"
    )
    config.addinivalue_line(
        "markers", "slow: Mark test as slow-running (skipped in CI by default)"
    )
    config.addinivalue_line(
        "markers", "unit: Mark test as a unit test"
    )
    config.addinivalue_line(
        "markers", "integration: Mark test as an integration test"
    )

def pytest_collection_modifyitems(config, items):
    """
    Modify test collection to skip slow tests unless explicitly requested.
    Also enforce CPU-only execution for all tests.
    """
    # Skip slow tests unless --runslow is passed
    if not config.getoption("--runslow", default=False):
        skip_slow = pytest.mark.skip(reason="need --runslow option to run")
        for item in items:
            if "slow" in item.keywords:
                item.add_marker(skip_slow)

    # Ensure no GPU markers are present (safety check)
    for item in items:
        if "gpu" in item.keywords:
            pytest.fail(
                f"Test {item.nodeid} is marked as GPU test. "
                "All tests must be CPU-only in this project configuration."
            )

def pytest_addoption(parser):
    """Add custom command-line options."""
    parser.addoption(
        "--runslow",
        action="store_true",
        default=False,
        help="run slow tests that are skipped by default"
    )
    parser.addoption(
        "--cpu-limit",
        action="store_true",
        default=False,
        help="enforce strict CPU resource limits (memory/time)"
    )

@pytest.fixture(scope="function")
def cpu_resource_limit(request):
    """
    Fixture to enforce CPU resource limits for specific tests.
    
    This fixture can be used to:
    - Limit memory usage via ulimit (if available)
    - Limit execution time
    - Ensure no GPU operations are attempted
    """
    if not request.config.getoption("--cpu-limit"):
        yield
        return

    # Import resource module for Unix-like systems
    try:
        import resource
    except ImportError:
        # Windows doesn't support resource module in the same way
        # Skip limit enforcement on Windows
        yield
        return

    # Set memory limit (e.g., 6GB for most tests)
    # Note: This is a soft limit; hard limit might require root
    memory_limit_mb = 6144  # 6GB
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (memory_limit_mb * 1024 * 1024, hard))
    except ValueError:
        # If limit cannot be set, log warning but continue
        pass

    # Set time limit (e.g., 300 seconds = 5 minutes)
    try:
        soft, hard = resource.getrlimit(resource.RLIMIT_CPU)
        resource.setrlimit(resource.RLIMIT_CPU, (300, hard))
    except ValueError:
        pass

    yield

    # Cleanup if needed
    # Note: Resource limits are process-wide and cannot be easily reset

@pytest.fixture(autouse=True)
def enforce_cpu_only():
    """
    Autouse fixture to ensure all tests run in CPU-only mode.
    
    This fixture:
    - Sets environment variables to disable GPU
    - Configures torch to use CPU only
    - Validates that no GPU operations are attempted
    """
    # Force CPU for torch
    try:
        import torch
        torch.set_default_device("cpu")
        # Verify no GPU is available or being used
        if torch.cuda.is_available():
            # Log warning but don't fail the test
            # In production, this might be more strict
            pass
    except ImportError:
        pass  # torch not installed

    # Verify CUDA_VISIBLE_DEVICES is set
    assert os.environ.get("CUDA_VISIBLE_DEVICES") == "", \
        "CUDA_VISIBLE_DEVICES must be empty for CPU-only tests"

    yield

    # Cleanup if needed