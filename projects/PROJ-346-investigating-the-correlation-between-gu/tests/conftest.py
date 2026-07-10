"""
Pytest configuration and fixtures for the project.
Ensures the project root and code paths are correctly set up for imports.
"""
import os
import sys
import pytest
from pathlib import Path

@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add project root and code directory to sys.path for imports."""
    # Determine project root based on this file's location
    current_file = Path(__file__).resolve()
    # Assuming tests/ is at root or code/tests/ is inside code/
    # The tasks.md says tests/ is at root, but conftest.py is listed in code/conftest.py in API surface.
    # We will handle both cases to be safe.
    
    if "code" in str(current_file):
        project_root = current_file.parent.parent
        code_dir = current_file.parent
    else:
        project_root = current_file.parent
        code_dir = project_root / "code"

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

    yield

def pytest_configure(config):
    """Configure pytest markers and global settings."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )