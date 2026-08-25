"""
Pytest configuration and fixtures for the llmXive muon-temp-correlation project.

This module configures the test environment to run on CPU-only hardware,
ensuring reproducibility and compatibility with environments lacking GPU access.
It also provides shared fixtures for temporary directories and logging setup.
"""
import os
import sys
import tempfile
import shutil
import logging
from pathlib import Path
from typing import Generator

import pytest

# Force CPU-only execution for any potential ML libraries (e.g., PyTorch, TensorFlow)
# Set environment variables before any heavy imports occur
os.environ["CUDA_VISIBLE_DEVICES"] = ""
os.environ["XLA_IR_DEBUG"] = "0"  # Disable XLA debug if using JAX/TF

# Attempt to configure specific backend CPU limits if available
try:
    import torch
    torch.set_num_threads(1)
    torch.set_num_interop_threads(1)
    if torch.cuda.is_available():
        # Ensure CUDA is not used even if detected
        torch.cuda.is_available = lambda: False
except ImportError:
    pass

try:
    import tensorflow as tf
    tf.config.set_visible_devices([], 'GPU')
except ImportError:
    pass

try:
    import jax
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
except ImportError:
    pass


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment() -> Generator[None, None, None]:
    """
    Setup fixture to ensure a clean test environment.
    Runs once per session.
    """
    # Ensure project root is in path for imports
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

    # Create a temporary directory for test artifacts if not specified
    # This is handled by the temp_data_dir fixture, but we ensure logs dir exists
    logs_dir = project_root / "logs"
    logs_dir.mkdir(exist_ok=True)

    yield

    # Teardown: Optional cleanup if needed
    pass


@pytest.fixture
def temp_data_dir() -> Generator[Path, None, None]:
    """
    Creates a temporary directory for test data artifacts.
    Ensures cleanup after the test completes.
    """
    temp_dir = tempfile.mkdtemp(prefix="llmxive_test_")
    temp_path = Path(temp_dir)
    
    # Create standard subdirectories expected by the ingestion pipeline
    (temp_path / "raw").mkdir(exist_ok=True)
    (temp_path / "processed").mkdir(exist_ok=True)
    (temp_path / "results").mkdir(exist_ok=True)
    
    yield temp_path

    # Cleanup
    if temp_path.exists():
        shutil.rmtree(temp_path)


@pytest.fixture
def sample_config_path(temp_data_dir: Path) -> Path:
    """
    Creates a minimal configuration file for testing.
    """
    config_file = temp_data_dir / "test_config.yaml"
    config_content = """
    parameters:
      z_peak: 15.0
      sigma: 2.5
      t_eff_threshold: 200.0
    """
    config_file.write_text(config_content)
    return config_file


def pytest_configure(config):
    """
    Pytest hook to add custom markers or configuration.
    """
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )

def pytest_collection_modifyitems(config, items):
    """
    Automatically skip slow tests if not explicitly requested.
    """
    if config.getoption("--run-slow", default=False):
        return

    skip_slow = pytest.mark.skip(reason="need --run-slow option to run")
    for item in items:
        if "slow" in item.keywords:
            item.add_marker(skip_slow)

# Add command line option for slow tests
def pytest_addoption(parser):
    parser.addoption(
        "--run-slow",
        action="store_true",
        default=False,
        help="run slow tests",
    )