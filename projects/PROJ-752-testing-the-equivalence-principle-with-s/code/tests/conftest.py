"""
Pytest configuration and fixtures.
This file is created as part of T001 to prepare for T010,
but the directory structure itself is the primary goal of T001.
"""
import pytest
import os
import sys

# Add the code directory to the path for imports during testing
@pytest.fixture(autouse=True)
def add_code_to_path():
    code_dir = os.path.join(os.path.dirname(__file__), "..")
    if code_dir not in sys.path:
        sys.path.insert(0, code_dir)
    yield
    if code_dir in sys.path:
        sys.path.remove(code_dir)
