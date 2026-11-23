"""
Pytest configuration and fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent

@pytest.fixture
def data_dir(project_root):
    """Return the data directory."""
    return project_root / "data"

@pytest.fixture
def state_dir(project_root):
    """Return the state directory."""
    return project_root / "state"
