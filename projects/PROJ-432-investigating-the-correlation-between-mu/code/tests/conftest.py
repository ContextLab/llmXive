"""
Pytest configuration and shared fixtures for the muon flux analysis project.

This module configures the test environment to run in a CPU-only mode,
ensuring reproducibility and compatibility with environments lacking GPU resources.
It also provides shared fixtures for temporary data directories and logging.
"""
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
import pytest

# Force CPU-only execution for any libraries that might attempt GPU usage
# This is critical for environments without CUDA or for reproducibility
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["PYTORCH_CUDA_ALLOC_CONF"] = ""

# Ensure numpy uses a fixed seed for reproducibility if randomization is used in tests
import numpy as np
np.random.seed(42)

# Project root path for relative imports and path resolution
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging to capture test output
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

@pytest.fixture(scope="session")
def temp_data_dir():
    """
    Creates a temporary directory structure mimicking the project's data layout.
    Yields the path to the temporary root, then cleans up afterwards.
    
    Structure:
    temp_root/
      data/
        raw/
        processed/
        results/
      logs/
      config/
    """
    temp_root = tempfile.mkdtemp(prefix="muon_test_")
    temp_path = Path(temp_root)
    
    # Create required subdirectories
    (temp_path / "data" / "raw").mkdir(parents=True)
    (temp_path / "data" / "processed").mkdir(parents=True)
    (temp_path / "data" / "results").mkdir(parents=True)
    (temp_path / "logs").mkdir(parents=True)
    (temp_path / "config").mkdir(parents=True)
    
    yield temp_path
    
    # Cleanup after tests
    shutil.rmtree(temp_path)

@pytest.fixture(scope="function")
def sample_config_path(temp_data_dir):
    """
    Creates a minimal valid config file for testing purposes.
    """
    config_file = temp_data_dir / "config" / "test_constants.yaml"
    config_content = """
    t_eff:
      grieder_1985:
        z_peak: 10000.0
        sigma: 2500.0
    thresholds:
      min_pressure: 10.0
      max_pressure: 1000.0
    """
    with open(config_file, "w") as f:
        f.write(config_content)
    return config_file

def pytest_configure(config):
    """
    Pytest hook to configure global test settings.
    """
    # Mark tests that require network access (skipped if --no-network)
    config.addinivalue_line(
        "markers", "network: marks test as requiring network access"
    )
    # Mark tests that are slow (skipped if --no-slow)
    config.addinivalue_line(
        "markers", "slow: marks test as slow running"
    )

def pytest_collection_modifyitems(config, items):
    """
    Pytest hook to skip tests based on markers if specific flags are not passed.
    """
    if config.getoption("--no-network", default=False):
        skip_network = pytest.mark.skip(reason="Network access disabled")
        for item in items:
            if "network" in item.keywords:
                item.add_marker(skip_network)

def pytest_addoption(parser):
    """
    Add custom command-line options to pytest.
    """
    parser.addoption(
        "--no-network",
        action="store_true",
        default=False,
        help="Skip tests that require network access"
    )
    parser.addoption(
        "--no-slow",
        action="store_true",
        default=False,
        help="Skip tests marked as slow"
    )