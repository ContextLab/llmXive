"""
Pytest configuration and fixtures for the project.
"""
import pytest
from pathlib import Path
import sys

# Add the code directory to the path for all tests
@pytest.fixture(autouse=True)
def add_code_to_path():
    project_root = Path(__file__).parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    # Cleanup if necessary
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))
