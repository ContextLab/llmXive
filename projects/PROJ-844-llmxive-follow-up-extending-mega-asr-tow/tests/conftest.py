"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

# Add project root to path for all tests
@pytest.fixture(autouse=True)
def add_project_root():
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup if necessary
