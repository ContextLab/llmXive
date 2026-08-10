import os
import sys
import pytest
from pathlib import Path

@pytest.fixture
def setup_path():
    return Path(__file__).parent.parent

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

@pytest.fixture
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture
def processed_dir(data_dir):
    return data_dir / "processed"

@pytest.fixture
def results_dir(processed_dir):
    return processed_dir / "results"
