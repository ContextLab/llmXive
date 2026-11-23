import os
import sys
from pathlib import Path
import pytest
import tempfile
import shutil

from scripts.setup_project_structure import create_directories, generate_tree_manifest

@pytest.fixture
def temp_project_root():
    """Create a temporary directory to act as project root."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)

def test_create_directories(temp_project_root):
    """Test that all required directories are created."""
    # Change to temp root for testing
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        # Create a mock __init__.py to make it look like a package
        (temp_project_root / "code").mkdir()
        (temp_project_root / "code" / "__init__.py").touch()
        
        # Run the directory creation
        created_count = create_directories()
        
        # Verify directories exist
        required_dirs = [
            "code/simulation",
            "code/models",
            "code/metrics",
            "code/validation",
            "code/plots",
            "code/scripts",
            "data/raw",
            "data/simulated",
            "data/results",
            "tests/unit",
            "tests/integration",
            "docs/paper",
        ]
        
        for dir_path in required_dirs:
            full_path = temp_project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
        
        # Verify .gitkeep files exist in data directories
        data_dirs = ["data/raw", "data/simulated", "data/results"]
        for dir_path in data_dirs:
            gitkeep_path = temp_project_root / dir_path / ".gitkeep"
            assert gitkeep_path.exists(), f".gitkeep not found in {dir_path}"
            
    finally:
        os.chdir(original_cwd)

def test_generate_tree_manifest(temp_project_root):
    """Test that tree manifest is generated correctly."""
    # Setup directories first
    original_cwd = os.getcwd()
    os.chdir(temp_project_root)
    
    try:
        (temp_project_root / "code").mkdir()
        (temp_project_root / "code" / "__init__.py").touch()
        create_directories()
        
        # Generate manifest
        tree_output = generate_tree_manifest(temp_project_root)
        
        # Verify output contains expected directories
        assert "code" in tree_output
        assert "data" in tree_output
        assert "tests" in tree_output
        assert "docs" in tree_output
        assert "simulation" in tree_output
        assert "models" in tree_output
        
        # Verify it's a non-empty string
        assert len(tree_output) > 0
        
    finally:
        os.chdir(original_cwd)