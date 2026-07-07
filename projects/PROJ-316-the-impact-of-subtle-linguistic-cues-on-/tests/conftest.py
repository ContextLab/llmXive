"""Pytest configuration and shared fixtures for llmXive research pipeline.

This file configures pytest to work with the project structure, sets up
shared fixtures for test data, and ensures proper path resolution for
importing project modules during testing.
"""
import os
import sys
from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent.parent


@pytest.fixture(scope="session")
def code_root(project_root: Path) -> Path:
    """Return the code directory."""
    return project_root / "code"


@pytest.fixture(scope="session")
def data_root(project_root: Path) -> Path:
    """Return the data directory."""
    return project_root / "data"


@pytest.fixture(scope="session")
def src_path(code_root: Path) -> Path:
    """Return the src directory path."""
    return code_root / "src"


@pytest.fixture(scope="session")
def tests_path(code_root: Path) -> Path:
    """Return the tests directory path."""
    return code_root / "tests"


@pytest.fixture(autouse=True)
def add_project_to_path(code_root: Path):
    """Automatically add code directory to sys.path for imports."""
    original_path = sys.path.copy()
    try:
        if str(code_root) not in sys.path:
            sys.path.insert(0, str(code_root))
        yield
    finally:
        sys.path = original_path
