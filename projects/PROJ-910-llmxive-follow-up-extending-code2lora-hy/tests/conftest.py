"""
Pytest configuration and fixtures for the project.
"""
import pytest
import sys
from pathlib import Path

# Add the project root to the path so imports work
@pytest.fixture(autouse=True)
def add_to_path(monkeypatch):
    project_root = Path(__file__).parent.parent
    sys.path.insert(0, str(project_root))
    yield
    sys.path.remove(str(project_root))
