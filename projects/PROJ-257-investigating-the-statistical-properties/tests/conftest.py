"""
Pytest configuration and fixtures.
"""
import os
import sys
from pathlib import Path

import pytest

# Ensure the project root is in the path for imports
@pytest.fixture(autouse=True)
def add_src_to_path():
    """Add src/ directory to sys.path for imports during tests."""
    root = Path(__file__).parent.parent
    src_path = root / "src"
    if str(src_path) not in sys.path:
        sys.path.insert(0, str(src_path))
    yield
    # Optional: cleanup if necessary, though usually not needed for path inserts

@pytest.fixture
def project_root():
    """Return the project root directory path."""
    return Path(__file__).parent.parent

@pytest.fixture
def data_raw_dir(project_root):
    """Return the path to the raw data directory."""
    return project_root / "data" / "raw"

@pytest.fixture
def data_processed_dir(project_root):
    """Return the path to the processed data directory."""
    return project_root / "data" / "processed"

@pytest.fixture
def output_results_dir(project_root):
    """Return the path to the output results directory."""
    return project_root / "output" / "results"

@pytest.fixture
def output_figures_dir(project_root):
    """Return the path to the output figures directory."""
    return project_root / "output" / "figures"
