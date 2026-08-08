"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
import pytest

# Ensure the code directory is in the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(__file__), '..', 'code')
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    if code_dir in sys.path:
        sys.path.remove(code_dir)

@pytest.fixture
def sample_function_code():
    """Provides a sample Python function string for testing static analysis."""
    return """
def calculate_sum(numbers):
    \"""Calculate the sum of a list of numbers.\"""
    total = 0
    for num in numbers:
  total += num
    return total
"""

@pytest.fixture
def sample_complex_code():
    """Provides a sample complex Python function string for testing nesting depth."""
    return """
def complex_processor(data):
    \"""Process data with nested logic.\"""
    results = []
    if data:
  for item in data:
      if isinstance(item, dict):
          for key, value in item.items():
              if key.startswith('valid'):
                  results.append(value)
    return results
"""