"""
Pytest configuration and shared fixtures for the test suite.
"""
import pytest
import sys
import os

# Add code directory to path for imports
@pytest.fixture(autouse=True)
def add_code_path():
    code_path = os.path.join(os.path.dirname(__file__), '..', 'code')
    if code_path not in sys.path:
        sys.path.insert(0, code_path)
    yield
    if code_path in sys.path:
        sys.path.remove(code_path)

# You can add global fixtures here if needed
# Example: mock_config, mock_logger, etc.
