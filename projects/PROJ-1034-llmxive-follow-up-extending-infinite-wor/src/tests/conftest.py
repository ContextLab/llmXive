"""Pytest configuration and fixtures for the project."""
import pytest
import sys
import os

# Ensure src is in path for imports during tests
@pytest.fixture(autouse=True)
def add_src_to_path():
    src_path = os.path.join(os.path.dirname(__file__), "..")
    if src_path not in sys.path:
        sys.path.insert(0, src_path)
    yield
    if src_path in sys.path:
        sys.path.remove(src_path)
