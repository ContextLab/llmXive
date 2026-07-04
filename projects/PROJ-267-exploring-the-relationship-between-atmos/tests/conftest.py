"""
Pytest configuration and shared fixtures for the test suite.

Provides fixtures for temporary data directories, mock datasets, and
project path resolution.
"""
import os
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).parent.parent


@pytest.fixture
def data_dir(project_root: Path) -> Path:
    """Return the data directory path."""
    return project_root / "data"


@pytest.fixture
def processed_dir(project_root: Path) -> Path:
    """Return the processed data directory path."""
    return project_root / "data" / "processed"


@pytest.fixture
def raw_dir(project_root: Path) -> Path:
    """Return the raw data directory path."""
    return project_root / "data" / "raw"


@pytest.fixture
def code_dir(project_root: Path) -> Path:
    """Return the code directory path."""
    return project_root / "code"


@pytest.fixture
def temp_dir() -> Path:
    """Create a temporary directory for test outputs."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)