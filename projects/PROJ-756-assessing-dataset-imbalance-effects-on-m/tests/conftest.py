"""
Pytest configuration and shared fixtures for the project.

Provides common fixtures for test data paths, temporary directories,
and mock configurations.
"""
import os
import pytest
from pathlib import Path


@pytest.fixture
def project_root():
    """Return the root directory of the project."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_root(project_root):
    """Return the data directory."""
    return project_root / "data"


@pytest.fixture
def results_root(project_root):
    """Return the results directory."""
    return project_root / "results"


@pytest.fixture
def code_root(project_root):
    """Return the code directory."""
    return project_root / "code"


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for test artifacts."""
    return tmp_path