"""
Pytest configuration and fixtures for the cognitive decline prediction project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path so we can import code modules
# assuming this file is at tests/conftest.py
project_root = Path(__file__).parent.parent
code_dir = project_root / "code"

if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

@pytest.fixture(scope="session")
def test_data_dir():
    """Path to the test data directory."""
    return project_root / "tests" / "data"

@pytest.fixture(scope="session")
def output_dir():
    """Path to temporary output directory for tests."""
    output = project_root / "tests" / "output"
    output.mkdir(exist_ok=True)
    return output

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test artifacts."""
    return tmp_path
