"""
Pytest configuration and fixtures for integration tests.
"""
import pytest
import sys
from pathlib import Path

# Ensure the project root is in the path
@pytest.fixture(autouse=True)
def add_project_root():
    project_root = Path(__file__).parent.parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))
