"""
Pytest configuration and fixtures for the project.

Provides shared fixtures for test data paths, temporary directories,
and logging configuration during test runs.
"""

import os
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def data_dir(project_root: Path) -> Path:
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def raw_data_dir(data_dir: Path) -> Path:
    """Return the path to the raw data directory."""
    raw_dir = data_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    return raw_dir

@pytest.fixture(scope="session")
def processed_data_dir(data_dir: Path) -> Path:
    """Return the path to the processed data directory."""
    proc_dir = data_dir / "processed"
    proc_dir.mkdir(parents=True, exist_ok=True)
    return proc_dir

@pytest.fixture(scope="session")
def state_dir(project_root: Path) -> Path:
    """Return the path to the state directory."""
    state = project_root / "state"
    state.mkdir(parents=True, exist_ok=True)
    return state

@pytest.fixture(scope="session")
def src_dir(project_root: Path) -> Path:
    """Return the path to the source code directory."""
    return project_root / "src"
