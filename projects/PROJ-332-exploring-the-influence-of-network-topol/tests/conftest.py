"""
Pytest configuration and shared fixtures for PROJ-332.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path

import pytest

# Ensure code directory is on path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Add the code directory to sys.path for imports."""
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def temp_project_root():
    """Create a temporary directory structure mimicking the project root."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    
    # Create necessary directories
    dirs = ["data/raw", "data/processed", "tests/unit", "tests/contract"]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)
    
    yield temp_dir
    
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_config_dict():
    """Return a sample configuration dictionary for testing."""
    return {
        "N": 100,
        "p": 0.1,
        "d": 50.0,  # nm
        "l": 1000.0,  # nm
        "seed": 42,
        "material": "Si",
        "lambda_phonon": 10.0,  # nm
        "specularity": 0.5,
        "max_degree": 10,
        "min_degree": 2,
        "target_degree": 4.0
    }

@pytest.fixture
def sample_network_params():
    """Return sample parameters for network generation tests."""
    return {
        "N": 50,
        "p": 0.05,
        "target_degree": 4.0,
        "seed": 12345
    }

@pytest.fixture
def csv_output_path(temp_project_root):
    """Return a path to a temporary CSV file for output testing."""
    return Path(temp_project_root) / "data" / "processed" / "test_results.csv"