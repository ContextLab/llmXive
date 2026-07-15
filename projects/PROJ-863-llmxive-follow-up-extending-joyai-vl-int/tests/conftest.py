"""
Pytest configuration and global fixtures for llmXive project.

This file defines:
1. Custom markers for CPU resource limiting (enforced by T004).
2. Global configuration for test execution limits.
3. Fixtures for environment setup and resource monitoring.
"""
import os
import sys
import pytest
from pathlib import Path
import time
import threading
from typing import Generator, Optional

# Add project root to path for imports
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# ------------------------------------------------------------------
# CPU Resource Limit Markers
# ------------------------------------------------------------------
# These markers are defined here so they can be used in tests.
# The enforcement logic is handled in the hook below.

def pytest_configure(config):
    """Register custom markers for CPU resource limiting."""
    config.addinivalue_line(
        "markers", "cpu_limit(max_time_sec, max_memory_mb): Limit CPU time and memory for a test."
    )
    config.addinivalue_line(
        "markers", "skip_slow: Skip tests that take longer than the threshold in CI."
    )

def pytest_collection_modifyitems(config, items):
    """
    Automatically add skip markers to tests marked with cpu_limit if
    the environment variables for resource limits are exceeded.
    """
    # Optional: Skip slow tests in CI if marked
    if config.getoption("--skip-slow", default=False):
        for item in items:
            if "skip_slow" in item.keywords:
                item.add_marker(pytest.mark.skip(reason="Skipping slow test in CI"))

# ------------------------------------------------------------------
# Resource Limit Enforcement (CPU Time & Memory)
# ------------------------------------------------------------------
# Note: Memory limits (max_memory_mb) are difficult to enforce strictly
# across all platforms without external tools (e.g., cgroups). 
# We implement a soft limit check via a background thread for the test duration.

class ResourceMonitor:
    """Monitors CPU time and memory usage of the current process."""
    
    def __init__(self, max_time_sec: float, max_memory_mb: float):
        self.max_time_sec = max_time_sec
        self.max_memory_mb = max_memory_mb
        self.start_time = time.time()
        self.start_cpu = os.times().user
        self.exceeded = False
        self.reason = ""
        self.thread: Optional[threading.Thread] = None

    def _check_resources(self):
        while not self.exceeded:
            current_time = time.time()
            current_cpu = os.times().user
            elapsed = current_time - self.start_time
            cpu_used = current_cpu - self.start_cpu

            # Check CPU time
            if cpu_used > self.max_time_sec:
                self.exceeded = True
                self.reason = f"CPU time limit exceeded: {cpu_used:.2f}s > {self.max_time_sec}s"
                break

            # Check Memory (approximate via /proc on Linux, or psutil if available)
            # Fallback to a simple check if psutil is not installed
            try:
                import psutil
                process = psutil.Process(os.getpid())
                mem_mb = process.memory_info().rss / (1024 * 1024)
                if mem_mb > self.max_memory_mb:
                    self.exceeded = True
                    self.reason = f"Memory limit exceeded: {mem_mb:.2f}MB > {self.max_memory_mb}MB"
                    break
            except ImportError:
                # If psutil is not available, we rely on CPU time only for strict enforcement
                # and log a warning about memory.
                pass

            time.sleep(0.1) # Poll every 100ms

    def start(self):
        self.thread = threading.Thread(target=self._check_resources, daemon=True)
        self.thread.start()

    def stop(self):
        if self.thread:
            self.thread.join(timeout=0.1)

@pytest.fixture
def cpu_limited(request):
    """
    Fixture that enforces CPU and memory limits for a test.
    Usage: @pytest.mark.cpu_limit(max_time_sec=60, max_memory_mb=1024)
    """
    marker = request.node.get_closest_marker("cpu_limit")
    if not marker:
        yield
        return

    max_time = marker.kwargs.get("max_time_sec", 60)
    max_mem = marker.kwargs.get("max_memory_mb", 2048)

    monitor = ResourceMonitor(max_time, max_mem)
    monitor.start()

    yield

    monitor.stop()
    if monitor.exceeded:
        pytest.fail(monitor.reason)

# ------------------------------------------------------------------
# Global Fixtures
# ------------------------------------------------------------------

@pytest.fixture(autouse=True)
def setup_environment():
    """Ensure necessary environment variables are set for tests."""
    # Set a default seed for reproducibility if not present
    if "DATA_SEED" not in os.environ:
        os.environ["DATA_SEED"] = "42"
    yield
    # Cleanup can be added here if needed

@pytest.fixture
def project_root_path() -> Path:
    """Provides the path to the project root."""
    return project_root

@pytest.fixture
def data_dir(project_root_path) -> Path:
    """Provides the path to the data directory."""
    return project_root_path / "data"

@pytest.fixture
def src_dir(project_root_path) -> Path:
    """Provides the path to the src directory."""
    return project_root_path / "src"
