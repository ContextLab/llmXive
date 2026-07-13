"""
Pytest configuration and fixtures for the project.
"""
import os
import sys
from pathlib import Path
import tempfile
import pytest

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

@pytest.fixture(scope="session")
def test_data_dir(tmp_path_factory):
    """Create a temporary directory for test data."""
    return tmp_path_factory.mktemp("data")

@pytest.fixture(scope="function")
def temp_output_dir(tmp_path):
    """Create a temporary directory for test outputs."""
    return tmp_path

@pytest.fixture
def mock_config(tmp_path):
    """Create a mock configuration file for testing."""
    config_path = tmp_path / "config.yaml"
    config_content = """
    paths:
      data_raw: data/raw
      data_processed: data/processed
      roi_output: data/processed/roi
    """
    config_path.write_text(config_content)
    return str(config_path)

@pytest.fixture(autouse=True)
def setup_env(monkeypatch):
    """Set up environment variables for testing."""
    monkeypatch.setenv("PYTHONPATH", str(project_root))
    # Prevent logging to console during tests to reduce noise
    monkeypatch.setenv("LOG_LEVEL", "ERROR")

def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line(
        "markers", "integration: mark test as an integration test"
    )
    config.addinivalue_line(
        "markers", "contract: mark test as a contract test"
    )
