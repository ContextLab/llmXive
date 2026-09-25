"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path

# Ensure the code directory is in the Python path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the code directory to sys.path for all tests."""
    project_root = Path(__file__).resolve().parent.parent
    code_path = project_root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    # Cleanup if necessary (though usually not needed for path manipulation)

import pytest
