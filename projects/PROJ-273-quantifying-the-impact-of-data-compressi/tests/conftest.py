"""
Pytest configuration and shared fixtures.
"""
import pytest
import sys
from pathlib import Path

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the project root to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def setup_test_environment(tmp_path):
    """
    Create a temporary directory structure mimicking the project's data folders
    for isolated testing.
    """
    data_dirs = [
        "raw",
        "interim",
        "processed",
        "external"
    ]
    for d in data_dirs:
        (tmp_path / "data" / d).mkdir(parents=True, exist_ok=True)
    return tmp_path
