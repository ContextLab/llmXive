"""
Pytest configuration and shared fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to the path for imports during testing
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))