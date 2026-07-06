"""Shared pytest configuration and fixtures."""
import pytest
from pathlib import Path
import sys

# Ensure code directory is in the path
@pytest.fixture(autouse=True)
def add_code_to_path():
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def sample_data_path():
    """Provide a path to sample data if available."""
    return Path(__file__).parent.parent / "data" / "raw"

@pytest.fixture
def temp_output_dir(tmp_path):
    """Provide a temporary directory for test outputs."""
    return tmp_path
