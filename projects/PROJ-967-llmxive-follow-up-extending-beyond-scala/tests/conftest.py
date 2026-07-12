"""
Pytest configuration and fixtures for the llmXive project.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Add the project's code directory to sys.path for imports."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup if necessary, though typically not needed for path insertion
