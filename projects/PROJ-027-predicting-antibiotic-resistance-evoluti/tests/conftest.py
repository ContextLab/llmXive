"""
Pytest configuration and shared fixtures for the Antibiotic Resistance Pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure code directory is in path for imports during tests
@pytest.fixture(scope="session", autouse=True)
def add_code_to_path():
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield

@pytest.fixture(scope="session")
def project_root():
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture(scope="session")
def processed_data_dir(project_root):
    return project_root / "data" / "processed"

@pytest.fixture(scope="session")
def raw_data_dir(project_root):
    return project_root / "data" / "raw"

@pytest.fixture(scope="session")
def models_dir(project_root):
    return project_root / "data" / "models"
