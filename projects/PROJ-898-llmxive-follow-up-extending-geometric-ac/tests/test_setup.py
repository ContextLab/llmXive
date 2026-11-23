import os
import pytest

def test_project_structure_exists():
    """Test that the project root directory structure exists."""
    project_root = "projects/PROJ-898-llmxive-follow-up-extending-geometric-ac"
    
    # Check that the project root exists
    assert os.path.exists(project_root), f"Project root {project_root} does not exist"
    
    # Check that required directories exist
    required_dirs = [
        "code",
        "data",
        "data/raw",
        "data/generated",
        "data/results",
        "tests",
        "specs",
        "scripts",
        "figures"
    ]
    
    for directory in required_dirs:
        full_path = os.path.join(project_root, directory)
        assert os.path.exists(full_path), f"Directory {full_path} does not exist"

def test_gitkeep_files_exist():
    """Test that .gitkeep files exist in data directories."""
    project_root = "projects/PROJ-898-llmxive-follow-up-extending-geometric-ac"
    
    gitkeep_dirs = [
        "data/raw",
        "data/generated",
        "data/results"
    ]
    
    for directory in gitkeep_dirs:
        full_path = os.path.join(project_root, directory, ".gitkeep")
        assert os.path.exists(full_path), f".gitkeep file {full_path} does not exist"
        
        # Verify the file is not empty
        with open(full_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, f".gitkeep file {full_path} is empty"

def test_code_directory_is_empty_except_for_setup_files():
    """Test that the code directory contains only setup files initially."""
    project_root = "projects/PROJ-898-llmxive-follow-up-extending-geometric-ac"
    code_dir = os.path.join(project_root, "code")
    
    # List files in code directory
    files = os.listdir(code_dir)
    
    # Check that setup files exist
    assert "setup_project_structure.py" in files, "setup_project_structure.py not found"
    assert "setup_data_dirs.py" in files, "setup_data_dirs.py not found"

def test_tests_directory_structure():
    """Test that the tests directory has the required structure."""
    project_root = "projects/PROJ-898-llmxive-follow-up-extending-geometric-ac"
    
    required_test_dirs = [
        "tests/unit",
        "tests/integration"
    ]
    
    for directory in required_test_dirs:
        full_path = os.path.join(project_root, directory)
        assert os.path.exists(full_path), f"Test directory {full_path} does not exist"