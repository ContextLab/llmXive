"""
Pytest configuration and fixtures for the llmXive pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

# Ensure the project root is in the path for imports
# This helps when running tests from the root directory
@pytest.fixture(autouse=True)
def add_project_root_to_path():
    """Automatically add project root to sys.path for imports."""
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    yield
    # Cleanup not strictly necessary for sys.path but good practice in some contexts
    if str(project_root) in sys.path:
        sys.path.remove(str(project_root))

@pytest.fixture
def mock_env_vars():
    """Fixture to set up mock environment variables for testing."""
    original_env = os.environ.copy()
    os.environ["OPENNEURO_API_KEY"] = "test_api_key_12345"
    os.environ["RAW_DATA_PATH"] = "/tmp/test_raw"
    os.environ["PROCESSED_DATA_PATH"] = "/tmp/test_processed"
    yield
    os.environ.clear()
    os.environ.update(original_env)

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create a temporary directory structure for data processing tests."""
    raw_dir = tmp_path / "data" / "raw"
    processed_dir = tmp_path / "data" / "processed"
    raw_dir.mkdir(parents=True)
    processed_dir.mkdir(parents=True)
    return {
        "root": tmp_path,
        "raw": raw_dir,
        "processed": processed_dir
    }