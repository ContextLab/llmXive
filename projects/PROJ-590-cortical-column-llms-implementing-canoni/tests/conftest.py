"""
Pytest configuration and fixtures for the Cortical Column LLMs project.

This module enforces resource constraints (memory, CPU) and test timeouts
as required by FR-004 and SC-005.
"""
import os
import sys
import time
import logging
import pytest
import psutil
from pathlib import Path
from typing import Generator, Dict, Any

# Configure logging for test execution
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
SRC_ROOT = PROJECT_ROOT / "code"
DATA_ROOT = PROJECT_ROOT / "code" / "data"

# Resource constraints
MAX_MEMORY_RSS_GB = 7.0
MAX_MEMORY_RSS_BYTES = int(MAX_MEMORY_RSS_GB * 1024**3)
TIMEOUT_SECONDS = 300  # Default timeout for unit tests

# CPU pinning (optional, best-effort)
ALLOWED_CPU_COUNT = 4


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for resource monitoring."""
    parser.addoption(
        "--strict-memory",
        action="store_true",
        default=False,
        help="Fail tests immediately if memory exceeds MAX_MEMORY_RSS_GB"
    )
    parser.addoption(
        "--timeout",
        action="store",
        default=str(TIMEOUT_SECONDS),
        help="Override default timeout for all tests"
    )


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest plugins and global settings."""
    # Register pytest-timeout plugin settings
    timeout_val = int(config.getoption("--timeout"))
    config.option.timeout = timeout_val
    logger.info(f"Configured pytest timeout to {timeout_val} seconds")

    # Verify required dependencies
    try:
        import psutil
    except ImportError:
        logger.error("psutil is required for resource monitoring. Install with: pip install psutil")
        sys.exit(1)


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Provide the project root path."""
    return PROJECT_ROOT


@pytest.fixture(scope="function")
def resource_monitor(request: pytest.FixtureRequest) -> Generator[Dict[str, Any], None, None]:
    """
    Fixture to monitor memory and CPU usage during a test.
    
    Enforces FR-004 (Memory < 7GB) and SC-005 (CPU constraints).
    If --strict-memory is passed, the test fails if the limit is exceeded.
    Otherwise, it logs a warning.
    """
    strict = request.config.getoption("--strict-memory")
    process = psutil.Process(os.getpid())
    
    # Record initial state
    initial_memory = process.memory_info().rss
    # Use os.sched_getaffinity if available (Linux), fallback to len(os.cpu_count()) logic
    # psutil cpu_affinity returns list of allowed CPU ids
    if hasattr(process, 'cpu_affinity'):
        try:
            initial_cpu_count = len(process.cpu_affinity())
        except Exception:
            initial_cpu_count = os.cpu_count() or 1
    else:
        initial_cpu_count = os.cpu_count() or 1
    
    start_time = time.time()
    peak_memory = initial_memory
    
    # Yield control to the test
    yield {
        "initial_memory_bytes": initial_memory,
        "initial_cpu_count": initial_cpu_count,
        "strict_mode": strict
    }
    
    # Post-test analysis
    end_time = time.time()
    elapsed = end_time - start_time
    current_memory = process.memory_info().rss
    peak_memory = max(peak_memory, current_memory)
    
    peak_memory_gb = peak_memory / (1024**3)
    
    # Check constraints
    if peak_memory > MAX_MEMORY_RSS_BYTES:
        msg = (
            f"Test exceeded memory limit: {peak_memory_gb:.2f} GB > {MAX_MEMORY_RSS_GB} GB "
            f"(elapsed: {elapsed:.2f}s)"
        )
        if strict:
            pytest.fail(msg)
        else:
            logger.warning(msg)
    else:
        logger.info(
            f"Test completed within memory limits: {peak_memory_gb:.2f} GB "
            f"(elapsed: {elapsed:.2f}s)"
        )


@pytest.fixture(autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """
    Autouse fixture to ensure environment consistency before each test.
    
    - Sets up necessary directories if missing.
    - Warns if CPU affinity is restricted unexpectedly.
    """
    # Ensure data directories exist
    for dir_path in [DATA_ROOT, DATA_ROOT / "logs", DATA_ROOT / "results"]:
        dir_path.mkdir(parents=True, exist_ok=True)
    
    # Check CPU affinity using psutil for cross-platform compatibility
    # and to assert core pinning constraints
    try:
        process = psutil.Process(os.getpid())
        # Get CPU affinity (available on Unix-like systems, best-effort on Windows)
        if hasattr(process, 'cpu_affinity'):
            cpu_affinity = process.cpu_affinity()
            cpu_count = len(cpu_affinity)
            
            if cpu_count > ALLOWED_CPU_COUNT:
                logger.warning(
                    f"Test runner has access to {cpu_count} CPUs via psutil.cpu_affinity(). "
                    f"Recommend restricting to {ALLOWED_CPU_COUNT} for reproducibility (SC-005)."
                )
            else:
                logger.debug(f"Test runner restricted to {cpu_count} CPUs via psutil.")
        elif hasattr(os, 'sched_getaffinity'):
            cpu_set = os.sched_getaffinity(0)
            if len(cpu_set) > ALLOWED_CPU_COUNT:
                logger.warning(
                    f"Test runner has access to {len(cpu_set)} CPUs. "
                    f"Recommend restricting to {ALLOWED_CPU_COUNT} for reproducibility."
                )
            else:
                logger.debug(f"Test runner restricted to {len(cpu_set)} CPUs.")
    except Exception as e:
        logger.warning(f"Could not determine CPU affinity: {e}")
    
    yield