"""
Pytest configuration and shared fixtures for the llmXive meta-analysis pipeline.
"""
import os
import pytest
import sys
from pathlib import Path

# Add the project root to the path to ensure imports work regardless of cwd
@pytest.fixture(autouse=True)
def setup_project_path():
    project_root = Path(__file__).parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Optional: cleanup if needed

@pytest.fixture
def data_dir():
    """Path to the data directory."""
    return Path(__file__).parent.parent / "data"

@pytest.fixture
def results_dir():
    """Path to the results directory."""
    return Path(__file__).parent.parent / "results"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs to avoid polluting data/."""
    return tmp_path
