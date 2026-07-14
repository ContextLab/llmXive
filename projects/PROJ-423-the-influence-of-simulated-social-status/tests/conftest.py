"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
import json
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the 'code' directory to sys.path for imports."""
    root_dir = Path(__file__).parent.parent
    code_dir = root_dir / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Optional: cleanup if needed, though usually not required for path insertion

@pytest.fixture
def project_root():
    """Returns the root directory of the project."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    """Returns the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def processed_data_dir(data_dir):
    """Returns the path to the processed data directory."""
    return data_dir / "processed"

@pytest.fixture
def raw_data_dir(data_dir):
    """Returns the path to the raw data directory."""
    return data_dir / "raw"

@pytest.fixture
def checksums_file(data_dir):
    """Returns the path to the checksums.json file."""
    return data_dir / "checksums.json"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provides a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def sample_config():
    """Returns a sample configuration dictionary for testing."""
    return {
        "n_participants": 800,
        "status_levels": ["High", "Low"],
        "observed_behaviors": ["Risky", "Conservative"],
        "seed": 42
    }
