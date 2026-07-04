"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the code root is in the path for imports
@pytest.fixture(autouse=True)
def add_code_root_to_path():
    code_root = Path(__file__).parent.parent / "code"
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield
    # Optional: cleanup if needed, though usually not required for path insertion
