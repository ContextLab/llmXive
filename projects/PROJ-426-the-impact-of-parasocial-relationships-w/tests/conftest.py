"""
Pytest configuration and fixtures.
"""
import pytest
import sys
from pathlib import Path

@pytest.fixture(autouse=True)
def add_src_to_path():
    """Automatically add the 'code' directory to sys.path for imports."""
    root = Path(__file__).parent.parent
    code_path = root / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield
    if str(code_path) in sys.path:
        sys.path.remove(str(code_path))

@pytest.fixture
def sample_data_path():
    """Fixture providing a path to sample data for testing."""
    root = Path(__file__).parent.parent
    return root / "data" / "raw"