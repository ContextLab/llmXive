"""
Pytest configuration and shared fixtures.

This file provides common fixtures and configuration for the test suite.
"""
import pytest
import os
from pathlib import Path

@pytest.fixture
def project_root():
    """Return the path to the project root directory."""
    return Path(__file__).resolve().parent.parent

@pytest.fixture
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture
def code_dir(project_root):
    """Return the path to the code directory."""
    return project_root / "code"
