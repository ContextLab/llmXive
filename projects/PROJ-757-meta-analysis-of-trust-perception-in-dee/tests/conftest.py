"""
Global test configuration and fixtures for the meta-analysis pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root (parent of 'code' and 'tests') is in the path
# so imports from sibling modules work correctly.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

@pytest.fixture(scope="session")
def project_root():
    """Returns the Path to the project root directory."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def code_dir(project_root):
    """Returns the Path to the code directory."""
    return project_root / "code"

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Returns the Path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def results_dir(project_root):
    """Returns the Path to the results directory."""
    return project_root / "results"

@pytest.fixture(scope="session")
def temp_output_dir(tmp_path_factory):
    """Provides a temporary directory for test outputs."""
    return tmp_path_factory.mktemp("test_output")
