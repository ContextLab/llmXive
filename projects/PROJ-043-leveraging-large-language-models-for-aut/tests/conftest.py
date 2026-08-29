"""
Pytest configuration and shared fixtures for the test suite.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure project root is in path for imports
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Add project root to sys.path for imports during tests."""
    root = Path(__file__).parent.parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    yield
    if str(root) in sys.path:
        sys.path.remove(str(root))

@pytest.fixture
def sample_function_code():
    """Provide a sample Python function string for testing."""
    return """
def calculate_fibonacci(n):
    if n <= 1:
  return n
    else:
  return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)
"""

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    output_dir = tmp_path / "test_outputs"
    output_dir.mkdir()
    return output_dir