"""
Pytest configuration and fixtures for the Molecular Toxicity Prediction Pipeline.
"""
import os
import sys
import pytest
from pathlib import Path

@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the absolute path to the project root."""
    # Assume the project root is two levels up from this file:
    # code/tests/conftest.py -> code -> root
    return Path(__file__).resolve().parent.parent.parent

@pytest.fixture(scope="session")
def code_dir(project_root: Path) -> Path:
    """Return the path to the 'code' directory."""
    return project_root / "code"

@pytest.fixture(scope="session")
def src_dir(code_dir: Path) -> Path:
    """Return the path to the 'src' directory."""
    return code_dir / "src"

@pytest.fixture(scope="session")
def test_data_dir(code_dir: Path) -> Path:
    """Return the path to the test data directory."""
    data_dir = code_dir / "data"
    data_dir.mkdir(exist_ok=True)
    return data_dir

@pytest.fixture(autouse=True)
def add_code_to_path(code_dir: Path):
    """
    Automatically add the 'code' directory to sys.path for all tests.
    This allows importing modules like 'src.pipeline.run' directly.
    """
    sys.path.insert(0, str(code_dir))
    yield
    # Optional: cleanup if strictly necessary, though usually not needed for test sessions
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))