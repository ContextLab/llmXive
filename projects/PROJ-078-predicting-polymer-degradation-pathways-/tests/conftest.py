import os
import sys
import pytest
from pathlib import Path

# Ensure the code directory is in the Python path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    root_dir = Path(__file__).parent.parent
    code_dir = root_dir / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def project_root():
    return Path(__file__).parent.parent

@pytest.fixture
def data_dir(project_root):
    return project_root / "data"

@pytest.fixture
def state_dir(project_root):
    return project_root / "state"
