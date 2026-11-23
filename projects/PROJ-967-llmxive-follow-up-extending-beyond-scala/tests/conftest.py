"""
Pytest configuration and shared fixtures for the llmXive project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to sys.path so imports from code/ work in tests
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield

@pytest.fixture
def project_root():
    """Return the root path of the project."""
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
def results_dir(project_root):
    """Return the path to the results directory."""
    return project_root / "results"

@pytest.fixture
def mock_cleaned_data_path(data_processed_dir):
    """Path to the cleaned_data.parquet file (may not exist yet)."""
    return data_processed_dir / "cleaned_data.parquet"

@pytest.fixture
def mock_raw_data_path(data_processed_dir):
    """Path to the raw_data.parquet file (may not exist yet)."""
    return data_processed_dir / "raw_data.parquet"
