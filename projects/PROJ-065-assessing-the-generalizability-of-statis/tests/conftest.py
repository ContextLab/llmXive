"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path to allow imports from sibling modules
# assuming tests are run from the project root or via pytest discovery
PROJECT_ROOT = Path(__file__).parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture
def project_root():
    """Return the path to the project root."""
    return PROJECT_ROOT

@pytest.fixture
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def raw_data_dir(data_dir):
    """Return the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture
def processed_data_dir(data_dir):
    """Return the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture
def outputs_dir(project_root):
    """Return the path to the outputs directory."""
    return project_root / "outputs"

@pytest.fixture
def figures_dir(outputs_dir):
    """Return the path to the figures directory."""
    return outputs_dir / "figures"

@pytest.fixture
def reports_dir(outputs_dir):
    """Return the path to the reports directory."""
    return outputs_dir / "reports"

@pytest.fixture
def code_dir(project_root):
    """Return the path to the code directory."""
    return project_root / "code"

@pytest.fixture
def temp_dir(tmp_path):
    """Return a temporary directory for test artifacts."""
    return tmp_path
