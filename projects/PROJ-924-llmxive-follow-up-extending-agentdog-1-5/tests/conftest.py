"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to sys.path to allow imports from code/
@pytest.fixture(autouse=True)
def add_project_root():
    """Automatically add the project root to sys.path for imports."""
    project_root = Path(__file__).resolve().parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    # Cleanup if necessary (optional, usually not needed for path insertion)
