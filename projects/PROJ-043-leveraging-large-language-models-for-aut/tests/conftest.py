"""
Pytest configuration and shared fixtures.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path to allow imports from 'code/'
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root = Path(__file__).parent.parent
    if str(root / "code") not in sys.path:
        sys.path.insert(0, str(root / "code"))
    yield
    if str(root / "code") in sys.path:
        sys.path.remove(str(root / "code"))

@pytest.fixture
def sample_function_code():
    """Provides a sample Python function string for testing static analysis."""
    return """
def calculate_sum(numbers):
    total = 0
    for num in numbers:
  total += num
    return total
"""