"""
Pytest configuration and fixtures for the llmXive follow-up project.

This module configures:
- Fixed random seed (42) for reproducibility across all tests.
- Global fixtures for temporary directories and data paths.
- Integration test scaffolding markers.
"""
import os
import random
import tempfile
from pathlib import Path
from typing import Generator

import numpy as np
import pytest

# Enforce fixed seed for reproducibility
SEED = 42

@pytest.fixture(scope="session", autouse=True)
def set_seed():
    """Automatically set random seeds for numpy and python random on session start."""
    random.seed(SEED)
    np.random.seed(SEED)
    os.environ["PYTHONHASHSEED"] = str(SEED)

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).parent.parent

@pytest.fixture(scope="session")
def data_root(project_root: Path) -> Path:
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def raw_data_path(data_root: Path) -> Path:
    """Return the path to raw data."""
    return data_root / "raw"

@pytest.fixture(scope="session")
def processed_data_path(data_root: Path) -> Path:
    """Return the path to processed data."""
    return data_root / "processed"

@pytest.fixture(scope="function")
def temp_dir() -> Generator[Path, None, None]:
    """Provide a temporary directory that is cleaned up after the test."""
    with tempfile.TemporaryDirectory() as tmpdirname:
        yield Path(tmpdirname)

@pytest.fixture(scope="function")
def temp_data_file(temp_dir: Path) -> Path:
    """Provide a path to a temporary data file."""
    return temp_dir / "test_data.json"

# Markers for test categorization
# Usage: @pytest.mark.integration
# Add to pytest.ini or pass via CLI: -m "not integration"
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test requiring external resources or full pipeline."
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running."
    )
