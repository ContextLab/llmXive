"""
Pytest configuration and shared fixtures for the llmXive project.

This file ensures that the test directory structure is recognized
by pytest and provides common fixtures if needed.
"""
import os
import sys
import pytest

# Ensure the project root (parent of 'tests') is on the path
# so imports from 'code' work correctly during tests.
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if root_dir not in sys.path:
        sys.path.insert(0, root_dir)
    yield
