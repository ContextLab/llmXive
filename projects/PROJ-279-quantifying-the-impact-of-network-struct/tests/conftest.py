"""
Pytest configuration and shared fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Ensure code directory is in path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = Path(__file__).parent.parent / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))
