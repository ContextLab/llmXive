"""
Pytest configuration and fixtures for the llmXive CSA Food Security project.
Configures CPU-only execution and sets up paths relative to the project root.
"""
import os
import sys
import logging
from pathlib import Path
import pytest

# Add the project root (parent of 'tests') to sys.path to allow imports
# from code/ modules (e.g., code/data/download)
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Configure logging for tests to avoid cluttering output unless requested
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# CPU-Only Execution Configuration
# Force environment variables that prevent GPU usage for libraries that might try to use them
os.environ['CUDA_VISIBLE_DEVICES'] = ''
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'  # Suppress TensorFlow warnings if imported

# Ensure matplotlib uses a non-interactive backend for headless CI environments
import matplotlib
matplotlib.use('Agg')


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Returns the root directory of the project."""
    return PROJECT_ROOT


@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Returns the path to the data directory."""
    return project_root / "data"


@pytest.fixture(scope="session")
def raw_data_dir(data_dir: Path) -> Path:
    """Returns the path to the raw data directory."""
    return data_dir / "raw"


@pytest.fixture(scope="session")
def processed_data_dir(data_dir: Path) -> Path:
    """Returns the path to the processed data directory."""
    return data_dir / "processed"


@pytest.fixture(scope="session")
def code_dir(project_root: Path) -> Path:
    """Returns the path to the code directory."""
    return project_root / "code"


@pytest.fixture(scope="session")
def cpu_only() -> bool:
    """
    Fixture to explicitly mark a test as CPU-only.
    This is primarily for documentation/filtering purposes.
    """
    return True


@pytest.fixture(scope="function")
def caplog_handler(caplog):
    """
    Helper to ensure caplog captures logs correctly in different environments.
    """
    caplog.set_level(logging.DEBUG)
    return caplog
