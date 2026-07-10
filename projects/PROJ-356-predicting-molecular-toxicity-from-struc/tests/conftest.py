import os
import sys
import pytest
from pathlib import Path

@pytest.fixture
def add_code_to_path():
    """
    Fixture to add the project's code directory to sys.path for imports.
    """
    # Assuming the test is run from the project root or a parent of 'code'
    # We try to find the 'code' directory relative to the test file location
    current_dir = Path(__file__).parent
    # If running from tests/, code is in parent
    code_dir = current_dir.parent / "code"
    
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    
    yield code_dir

@pytest.fixture
def test_data_dir(tmp_path):
    """
    Fixture providing a temporary data directory for testing.
    """
    data_dir = tmp_path / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture
def project_root(tmp_path):
    """
    Fixture providing a temporary project root directory.
    """
    root = tmp_path / "PROJ-356-predicting-molecular-toxicity-from-struc"
    root.mkdir(parents=True, exist_ok=True)
    return root