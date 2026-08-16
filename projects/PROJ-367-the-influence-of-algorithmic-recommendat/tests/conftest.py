"""
Pytest configuration and fixtures for the PROJ-367 pipeline.

This module provides shared fixtures and configuration to ensure
consistent test execution across all unit and integration tests.
"""
import os
import sys
import logging
from pathlib import Path
import pytest

# Ensure the project code directory is on the path for imports
# This assumes tests are run from the project root or via pytest discovery
PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT / "code"

if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

# Configure logging for tests to capture INFO/DEBUG logs if needed
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

@pytest.fixture(scope="session")
def project_root():
    """Return the root path of the project."""
    return PROJECT_ROOT

@pytest.fixture(scope="session")
def code_dir(project_root):
    """Return the path to the code directory."""
    return project_root / "code"

@pytest.fixture(scope="session")
def data_dir(project_root):
    """Return the path to the data directory."""
    return project_root / "data"

@pytest.fixture(scope="session")
def output_dir(project_root):
    """Return the path to the output directory (for test artifacts)."""
    return project_root / "data" / "test_output"

@pytest.fixture(autouse=True)
def setup_test_environment(output_dir):
    """Ensure test output directory exists and is clean before each test session."""
    output_dir.mkdir(parents=True, exist_ok=True)
    yield
    # Cleanup could be added here if necessary, but often pytest temp dirs are used.
    # For now, we leave the directory to allow inspection of artifacts if needed.
