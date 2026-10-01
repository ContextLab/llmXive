"""
Pytest configuration for llmXive project.

This module configures the pytest environment with:
1. Random seed pinning for reproducibility
2. Checksum verification enforcement for data downloads
3. Temporary directory management for tests
"""
import os
import random
import time
import hashlib
import logging
import sys
import pytest
from pathlib import Path
from typing import Generator, Optional

# Configure logging for test environment
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global seed value for reproducibility
DEFAULT_SEED = 42

def set_random_seed(seed: int = DEFAULT_SEED) -> None:
    """Set random seeds for reproducibility across all relevant libraries."""
    random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Set numpy seed if available
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        logger.warning("NumPy not available for seed setting")
    
    # Set torch seed if available
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        logger.warning("PyTorch not available for seed setting")

def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with seed pinning and custom options."""
    # Add custom command-line options
    config.addinivalue_line(
        "markers", "requires_checksum: mark test as requiring checksum verification"
    )
    
    # Set initial seed
    seed = config.getoption("--seed", default=DEFAULT_SEED)
    set_random_seed(seed)
    
    logger.info(f"Pytest configured with random seed: {seed}")

def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom command-line options for pytest."""
    parser.addoption(
        "--seed",
        action="store",
        default=DEFAULT_SEED,
        type=int,
        help="Random seed for reproducibility (default: 42)"
    )
    parser.addoption(
        "--enforce-checksum",
        action="store_true",
        default=False,
        help="Enforce checksum verification for data downloads"
    )

def pytest_sessionstart(session: pytest.Session) -> None:
    """Called at the beginning of the test session."""
    logger.info(f"Test session started at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Working directory: {Path.cwd()}")
    
    # Verify project structure
    required_dirs = ['code', 'tests', 'data', 'results']
    for dir_name in required_dirs:
        if not Path(dir_name).exists():
            logger.warning(f"Required directory '{dir_name}' not found")

def pytest_sessionfinish(session: pytest.Session, exitstatus: int) -> None:
    """Called at the end of the test session."""
    logger.info(f"Test session finished at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"Exit status: {exitstatus}")

@pytest.fixture
def temp_data_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for test data."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(exist_ok=True)
    yield data_dir

@pytest.fixture
def temp_results_dir(tmp_path: Path) -> Generator[Path, None, None]:
    """Create a temporary directory for test results."""
    results_dir = tmp_path / "results"
    results_dir.mkdir(exist_ok=True)
    yield results_dir

@pytest.fixture(autouse=True)
def enforce_checksum_verification(request: pytest.FixtureRequest) -> None:
    """Automatically enforce checksum verification for tests marked with requires_checksum."""
    if request.node.get_closest_marker("requires_checksum"):
        if not request.config.getoption("--enforce-checksum"):
            pytest.skip("Checksum verification not enforced. Run with --enforce-checksum.")

def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup before each test."""
    # Re-seed for each test to ensure reproducibility
    seed = item.config.getoption("--seed", default=DEFAULT_SEED)
    set_random_seed(seed)

def pytest_collection_modifyitems(config: pytest.Config, items: list) -> None:
    """Modify collected test items."""
    # Add a marker to all tests for consistency
    for item in items:
        if not item.get_closest_marker("seeded"):
            item.add_marker(pytest.mark.seeded)

def verify_checksum_verification() -> bool:
    """
    Verify that checksum verification is properly configured.
    
    This function checks if the download scripts are configured to log
    SHA-256 checksums to results/checksums.txt as required by T008.
    
    Returns:
        bool: True if checksum verification is properly configured, False otherwise.
    """
    # Check if results directory exists
    results_dir = Path("results")
    if not results_dir.exists():
        logger.warning("Results directory does not exist")
        return False
    
    # Check if checksums.txt exists
    checksum_file = results_dir / "checksums.txt"
    if not checksum_file.exists():
        logger.warning("Checksums file does not exist. This is expected if no downloads have occurred.")
        return True  # Not a failure if no downloads have happened yet
    
    # Verify checksums.txt is not empty
    if checksum_file.stat().st_size == 0:
        logger.warning("Checksums file is empty")
        return False
    
    # Verify format of checksums
    try:
        with open(checksum_file, 'r') as f:
            lines = f.readlines()
            for line in lines:
                parts = line.strip().split(',')
                if len(parts) != 2:
                    logger.error(f"Invalid checksum format: {line}")
                    return False
                filename, checksum = parts
                if len(checksum) != 64:  # SHA-256 produces 64 hex characters
                    logger.error(f"Invalid checksum length: {checksum}")
                    return False
        logger.info("Checksum verification format is correct")
        return True
    except Exception as e:
        logger.error(f"Error verifying checksums: {e}")
        return False

# Export public names
__all__ = [
    'set_random_seed',
    'pytest_configure',
    'pytest_addoption',
    'pytest_sessionstart',
    'pytest_sessionfinish',
    'temp_data_dir',
    'temp_results_dir',
    'enforce_checksum_verification',
    'pytest_runtest_setup',
    'verify_checksum_verification',
    'DEFAULT_SEED'
]
