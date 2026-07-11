"""
Pytest configuration and shared fixtures.
"""
import pytest
from pathlib import Path

@pytest.fixture
def project_root():
    return Path(__file__).resolve().parent.parent

@pytest.fixture
def data_raw_dir(project_root):
    dir_path = project_root / "data" / "raw"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path

@pytest.fixture
def data_processed_dir(project_root):
    dir_path = project_root / "data" / "processed"
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path
