"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Ensure code/ directory is in sys.path for imports during tests."""
    root = Path(__file__).parent.parent
    code_dir = root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def project_root():
    """Return the project root path."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_paths(project_root):
    """Return expected data paths."""
    return {
        "raw": project_root / "data" / "raw",
        "processed": project_root / "data" / "processed",
        "results": project_root / "results",
    }
