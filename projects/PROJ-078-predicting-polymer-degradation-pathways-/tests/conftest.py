"""
Pytest configuration and fixtures for the llmXive polymer degradation project.
Provides shared fixtures and configuration for unit and integration tests.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the code directory to the path for imports
@pytest.fixture(autouse=True)
def add_code_to_path():
    """Automatically add the code directory to sys.path for all tests."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))
    yield
    # Cleanup not strictly necessary but good practice
    if str(code_dir) in sys.path:
        sys.path.remove(str(code_dir))

@pytest.fixture
def project_paths():
    """Fixture to provide project directory paths."""
    from utils import get_project_paths
    return get_project_paths()

@pytest.fixture
def sample_smiles():
    """Provide a valid sample SMILES string for testing."""
    return "CC(=O)Oc1ccccc1C(=O)O"  # Aspirin-like ester

@pytest.fixture
def invalid_smiles():
    """Provide an invalid SMILES string for testing."""
    return "invalid_smiles_string_12345"

@pytest.fixture
def temp_dir(tmp_path):
    """Create a temporary directory for test artifacts."""
    return tmp_path
