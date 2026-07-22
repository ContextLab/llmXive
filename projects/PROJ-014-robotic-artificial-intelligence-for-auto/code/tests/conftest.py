"""
Pytest configuration and shared fixtures for the project.
Ensures src/ is on the Python path for imports during testing.
"""
import os
import sys
import pytest
from pathlib import Path

# Determine the project root relative to this file
# Assuming structure: code/tests/conftest.py -> project root is code/../
# But based on tasks.md, the project root is where 'code/' lives.
# We need to add 'code' to sys.path so 'from src...' works.
PROJECT_ROOT = Path(__file__).parent.parent
SRC_PATH = PROJECT_ROOT / "src"

@pytest.fixture(scope="session", autouse=True)
def add_src_to_path():
    """Automatically add the src directory to sys.path for all tests."""
    if str(SRC_PATH) not in sys.path:
        sys.path.insert(0, str(SRC_PATH))
    # Also ensure scripts are accessible if needed, though usually imports are from src
    yield

@pytest.fixture(scope="session")
def session_root():
    """Provide the project root path."""
    return PROJECT_ROOT
