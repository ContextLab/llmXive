"""
pytest configuration for integration tests.
"""
import pytest
import sys
from pathlib import Path

# Ensure code directory is in path
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_path = Path(__file__).parent.parent.parent / "code"
    if str(code_path) not in sys.path:
        sys.path.insert(0, str(code_path))
    yield