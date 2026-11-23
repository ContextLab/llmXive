"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest

# Add the project root to the path for imports during testing
# This ensures we can import from 'code' and 'code.utils' etc.
@pytest.fixture(autouse=True)
def add_src_to_path():
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    yield
    # Cleanup if necessary, though usually not needed for path insertion
