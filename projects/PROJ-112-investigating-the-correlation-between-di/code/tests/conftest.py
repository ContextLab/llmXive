import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def setup_path():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if necessary (usually not needed for path)

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent.parent

@pytest.fixture
def data_dir(project_root):
    return project_root / "data" / "raw"

@pytest.fixture
def processed_dir(project_root):
    return project_root / "data" / "processed"

@pytest.fixture
def results_dir(project_root):
    return project_root / "data" / "processed" / "results"

@pytest.fixture
def temp_dir(tmp_path):
    return tmp_path
