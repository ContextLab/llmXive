"""
Pytest configuration and shared fixtures for the research pipeline.
"""

import os
import pytest

@pytest.fixture(scope="session")
def project_root():
    """Return the root directory of the project."""
    return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the path to the data directory."""
    return os.path.join(project_root, "data")

@pytest.fixture(scope="session")
def src_dir(project_root):
    """Return the path to the source directory."""
    return os.path.join(project_root, "src")
