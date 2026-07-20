"""
Tests for the setup_project_structure script.
Verifies directory creation and verification logic.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest
import sys

# Add the parent directory of 'tests' to the path so we can import the script logic
# We import the functions directly from the script file content
import importlib.util

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as the project root for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def get_script_functions():
    """Dynamically load functions from the setup script."""
    script_path = Path(__file__).parent.parent / "scripts" / "setup_project_structure.py"
    spec = importlib.util.spec_from_file_location("setup_project_structure", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_directory_structure_creation(temp_project_root):
    """Test that the script creates all required directories."""
    module = get_script_functions()
    
    # Initial state: no directories should exist
    required_dirs = [
        "data/raw", "data/processed", "code/src", "code/tests", 
        "code/notebooks", "paper", "state", "contracts"
    ]
    for d in required_dirs:
        assert not (temp_project_root / d).exists()

    # Run creation
    module.create_directory_structure(temp_project_root)

    # Verify creation
    for d in required_dirs:
        full_path = temp_project_root / d
        assert full_path.is_dir(), f"Directory {full_path} was not created"

def test_no_overwrite_existing_files(temp_project_root):
    """Test that the script does not fail if directories already exist."""
    module = get_script_functions()
    
    # Create a dummy file in one of the target directories
    target_dir = temp_project_root / "paper"
    target_dir.mkdir(parents=True, exist_ok=True)
    dummy_file = target_dir / "existing_note.txt"
    dummy_file.write_text("I am existing")

    # Run creation again
    module.create_directory_structure(temp_project_root)

    # Verify file still exists and directory is intact
    assert dummy_file.exists()
    assert dummy_file.read_text() == "I am existing"

def test_verification_success(temp_project_root):
    """Test that verification returns True when all dirs exist."""
    module = get_script_functions()
    
    # Create structure
    module.create_directory_structure(temp_project_root)
    
    # Verify
    assert module.verify_directory_structure(temp_project_root) is True

def test_verification_failure(temp_project_root):
    """Test that verification returns False when a dir is missing."""
    module = get_script_functions()
    
    # Create partial structure (skip 'paper')
    (temp_project_root / "data" / "raw").mkdir(parents=True)
    (temp_project_root / "code" / "src").mkdir(parents=True)
    
    # Verify should fail because 'paper' is missing
    assert module.verify_directory_structure(temp_project_root) is False