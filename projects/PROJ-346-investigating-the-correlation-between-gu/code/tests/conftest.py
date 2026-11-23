"""
Global pytest configuration and fixtures for the project.
This file overrides the project root conftest.py to ensure
the tests directory is treated as the source of truth for
test discovery and path manipulation.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the Python path to allow imports from code/
# when running tests from the tests/ directory.
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

@pytest.fixture
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture
def raw_data_dir(data_dir):
    return data_dir / "raw"

@pytest.fixture
def processed_data_dir(data_dir):
    return data_dir / "processed"

@pytest.fixture
def qc_data_dir(data_dir):
    return data_dir / "qc"

@pytest.fixture
def figures_dir(project_root):
    return project_root / "figures"
