"""
Pytest configuration and shared fixtures for the polymer degradation project.
"""
import os
import sys
import pytest
from pathlib import Path

# Add the project root to the path to allow imports from 'code/'
# Assumes tests are run from the project root or via pytest discovery
@pytest.fixture(scope="session", autouse=True)
def configure_python_path():
    """Ensure code/ is in sys.path for imports."""
    project_root = Path(__file__).parent.parent
    code_dir = project_root / "code"
    if str(code_dir) not in sys.path:
        sys.path.insert(0, str(code_dir))

@pytest.fixture
def sample_smiles():
    """Return a list of sample SMILES strings for testing."""
    return [
        "CC(=O)O",  # Acetic acid (simple ester-like)
        "COC(=O)C", # Methyl acetate
        "CCO",      # Ethanol (not an ester)
        "invalid_smiles_123" # Invalid
    ]

@pytest.fixture
def sample_env_data():
    """Return sample environmental data dictionary."""
    return {
        "temperature": 25.0,
        "ph": 7.0,
        "uv_intensity": 100.0,
        "humidity": 50.0
    }

@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for file I/O tests."""
    return tmp_path
