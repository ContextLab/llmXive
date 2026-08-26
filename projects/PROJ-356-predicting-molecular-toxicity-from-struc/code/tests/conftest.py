"""
Pytest configuration and shared fixtures for the project.
"""
import os
import sys
import pytest
from pathlib import Path

# Determine project root based on typical directory structure
# Assumes code/tests/conftest.py exists
@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the root directory of the project."""
    return Path(__file__).parent.parent.parent

@pytest.fixture(scope="session")
def code_dir(project_root: Path) -> Path:
    """Return the code directory."""
    return project_root / "code"

@pytest.fixture(scope="session")
def src_dir(code_dir: Path) -> Path:
    """Return the src directory."""
    return code_dir / "src"

@pytest.fixture(scope="session")
def test_data_dir(project_root: Path) -> Path:
    """Return the test data directory."""
    data_dir = project_root / "code" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@pytest.fixture(autouse=True)
def add_code_to_path(code_dir: Path):
    """Add code directory to sys.path to allow imports."""
    sys.path.insert(0, str(code_dir))
    yield
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))
