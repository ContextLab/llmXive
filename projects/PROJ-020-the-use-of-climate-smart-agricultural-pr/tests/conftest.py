"""
Pytest configuration and fixtures for CPU-only execution.
Ensures tests run within the memory and compute constraints of the CI environment.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path for imports
# Assumes tests/ is at the root of the project
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# CPU-only configuration enforcement
# Force matplotlib to use non-interactive backend to prevent GUI errors in CI
import matplotlib
matplotlib.use('Agg')

# Set environment variables to restrict CPU usage if needed by downstream libraries
@pytest.fixture(autouse=True)
def set_cpu_environment():
    """
    Fixture to enforce CPU-only execution constraints.
    Sets environment variables to prevent GPU usage and limit threads.
    """
    # Ensure no GPU usage for libraries like TensorFlow/PyTorch if they were introduced
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
    
    # Limit OpenMP threads to prevent memory oversubscription in CI
    # Default to 2 threads for safety on limited CI runners
    os.environ["OMP_NUM_THREADS"] = "2"
    os.environ["MKL_NUM_THREADS"] = "2"
    os.environ["NUMEXPR_NUM_THREADS"] = "2"
    os.environ["OPENBLAS_NUM_THREADS"] = "2"

    yield

    # Cleanup not strictly necessary for env vars in this scope, but good practice
    # If specific test cleanup is needed, it can be added here

@pytest.fixture(scope="session")
def project_root():
    """Return the project root path."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the data directory path."""
    return project_root / "data"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir):
    """Return the raw data directory path."""
    return data_dir / "raw"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    """Return the processed data directory path."""
    return data_dir / "processed"

@pytest.fixture(scope="session")
def state_dir(project_root):
    """Return the state directory path."""
    return project_root / "state"
