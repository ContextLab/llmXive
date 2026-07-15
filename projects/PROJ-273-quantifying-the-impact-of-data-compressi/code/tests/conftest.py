"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

@pytest.fixture
def add_code_to_path():
    """
    Fixture to ensure the code directory is in the Python path for imports.
    """
    code_root = Path(__file__).parent.parent / "code"
    if str(code_root) not in sys.path:
        sys.path.insert(0, str(code_root))
    yield
    # Optional: cleanup path if needed, but usually not required in tests

@pytest.fixture(autouse=True)
def setup_test_environment(add_code_to_path):
    """
    Auto-use fixture to ensure path is set for every test.
    """
    pass
