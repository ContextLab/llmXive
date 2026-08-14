"""
Pytest configuration and shared fixtures for the toxicity prediction pipeline tests.

This module provides:
- Project root path detection
- Code and source directory paths
- Test data directory setup
- Path manipulation utilities for imports
"""

import os
import sys
import pytest
from pathlib import Path


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    # Navigate up from code/tests to project root
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
    return project_root / "code" / "data"


@pytest.fixture(autouse=True)
def add_code_to_path(code_dir: Path):
    """
    Automatically add the code directory to sys.path for imports.
    
    This ensures that imports like `from src.pipeline.run import main`
    work correctly during test execution.
    """
    original_path = sys.path.copy()
    try:
        if str(code_dir) not in sys.path:
            sys.path.insert(0, str(code_dir))
        yield
    finally:
        sys.path = original_path
