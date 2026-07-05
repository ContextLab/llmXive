"""
Pytest configuration for llmXive project.
Configures CPU-only execution environment and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Force CPU-only execution for all libraries
# This must be set before importing tensorflow/pytorch if they were used
os.environ["CUDA_VISIBLE_DEVICES"] = ""

# Disable GPU acceleration in numpy/scipy if applicable
os.environ["OMP_NUM_THREADS"] = "1"
os.environ["MKL_NUM_THREADS"] = "1"

# Project root path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# Ensure data directories exist for tests
@pytest.fixture(scope="session", autouse=True)
def setup_test_directories():
    """Create necessary test directories if they don't exist."""
    dirs = [
        PROJECT_ROOT / "data" / "raw",
        PROJECT_ROOT / "data" / "processed",
        PROJECT_ROOT / "data" / "results",
        PROJECT_ROOT / "logs",
        PROJECT_ROOT / "tests" / "fixtures",
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
    yield

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def sample_date_range():
    """Return a sample date range for testing."""
    return ["2023-01-01", "2023-01-07"]

@pytest.fixture(autouse=True)
def set_cpu_environment():
    """Ensure CPU-only mode for every test."""
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
    yield