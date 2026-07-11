"""
Pytest configuration and fixtures for the BCC Yield Strength prediction project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the Python path so imports work correctly
# when running pytest from the project root.
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Add the project root to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Optional: clean up if needed, though usually not required for tests