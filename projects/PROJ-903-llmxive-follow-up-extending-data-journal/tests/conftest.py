"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest
import pandas as pd

# Add the project root to the path so imports work correctly during tests
# We assume tests are run from the project root or the runner sets the path.
# This ensures `from code.data import loader` works.
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Import project config to ensure it's available
try:
    from code.config import get_config
except ImportError:
    # Fallback if config isn't ready yet
    get_config = None


@pytest.fixture(scope="session")
def project_root():
    """Return the Path to the project root."""
    return PROJECT_ROOT


@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory for data files that persists for the test function."""
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir


@pytest.fixture
def sample_dataset_csv(temp_data_dir):
    """
    Create a small, valid sample CSV dataset for testing.
    This is used for unit tests that require a file on disk but don't need real external data.
    The data is deterministic to ensure stable test results.
    """
    file_path = temp_data_dir / "sample_data.csv"
    data = {
        "id": range(1, 51),  # 50 rows to pass n >= 30 check
        "feature_a": [float(i) for i in range(1, 51)],
        "feature_b": [float(i * 2 + 1) for i in range(1, 51)],
        "feature_c": [float(i * 0.5) for i in range(1, 51)],
        "category": ["X" if i % 2 == 0 else "Y" for i in range(1, 51)],
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path


@pytest.fixture
def low_power_dataset_csv(temp_data_dir):
    """
    Create a small dataset with < 30 rows to trigger LowPowerError.
    """
    file_path = temp_data_dir / "low_power_data.csv"
    data = {
        "id": range(1, 10),  # Only 9 rows
        "feature_a": [float(i) for i in range(1, 10)],
        "feature_b": [float(i * 2) for i in range(1, 10)],
    }
    df = pd.DataFrame(data)
    df.to_csv(file_path, index=False)
    return file_path
