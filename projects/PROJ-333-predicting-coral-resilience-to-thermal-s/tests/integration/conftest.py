"""
Pytest configuration for integration tests.
Ensures the mock data directory is set up before tests run.
"""
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent

@pytest.fixture(scope="session")
def mock_data_dir(project_root):
    """Return the path to the mock data directory."""
    return project_root / "tests" / "integration" / "data" / "mock_fastq"