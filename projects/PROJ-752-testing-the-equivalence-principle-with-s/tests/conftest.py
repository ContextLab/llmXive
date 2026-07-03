import pytest
import os
import sys
from pathlib import Path

# Add the project root (parent of 'code' directory) to sys.path
# so imports like 'from utils.logging import ...' work correctly.
@pytest.fixture(autouse=True)
def add_code_to_path():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture(scope="session")
def project_root():
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture(scope="session")
def processed_data_dir(data_dir):
    return data_dir / "processed"

@pytest.fixture(scope="session")
def results_dir(project_root):
    return project_root / "data" / "results"

@pytest.fixture(scope="session")
def logs_dir(project_root):
    return project_root / "data" / "logs"