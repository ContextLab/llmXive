import os
import pytest
from pathlib import Path
import sys
import tempfile
import shutil

# Add the code directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_project_structure import create_structure

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    original_cwd = os.getcwd()
    os.chdir(temp_dir)
    yield Path(temp_dir)
    os.chdir(original_cwd)
    shutil.rmtree(temp_dir)

def test_contract_project_structure(temp_project_root):
    """
    Contract test: Verifies that the project structure meets the specifications
    defined in T001a.
    
    This test ensures that all required directories exist and are directories.
    """
    required_structure = {
        "data/raw": {"type": "directory"},
        "data/processed": {"type": "directory"},
        "code": {"type": "directory"},
        "code/utils": {"type": "directory"},
        "tests": {"type": "directory"},
        "tests/contract": {"type": "directory"},
        "tests/unit": {"type": "directory"},
        "tests/integration": {"type": "directory"},
        "docs": {"type": "directory"},
        "state": {"type": "directory"},
    }

    # Execute the setup
    create_structure()

    # Validate each component
    for path, specs in required_structure.items():
        full_path = temp_project_root / path
        
        assert full_path.exists(), f"Contract failed: {path} does not exist"
        
        if specs["type"] == "directory":
            assert full_path.is_dir(), f"Contract failed: {path} exists but is not a directory"
        
        # Additional contract checks can be added here (e.g., specific files inside)