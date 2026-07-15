"""
Pytest configuration and fixtures for the project.
"""
import os
import pytest
import sys

# Ensure code/ is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "code")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    if code_dir in sys.path:
        sys.path.remove(code_dir)

@pytest.fixture
def project_root():
    return os.path.dirname(os.path.dirname(__file__))

@pytest.fixture
def data_dir(project_root):
    return os.path.join(project_root, "data")

@pytest.fixture
def code_dir(project_root):
    return os.path.join(project_root, "code")
