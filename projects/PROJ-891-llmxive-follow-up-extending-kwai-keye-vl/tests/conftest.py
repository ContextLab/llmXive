"""
Pytest configuration and shared fixtures.
"""
import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the root path of the project."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_root(project_root):
    """Return the data directory path."""
    return project_root / "data"


@pytest.fixture
def src_root(project_root):
    """Return the src directory path."""
    return project_root / "src"


@pytest.fixture
def output_root(project_root):
    """Return the output directory path."""
    return project_root / "output"
