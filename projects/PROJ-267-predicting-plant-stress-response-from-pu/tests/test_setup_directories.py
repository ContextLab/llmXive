"""
Tests for the setup_directories module.
"""
import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "code"))

from setup_directories import main

def test_directory_structure_creation(tmp_path):
    """Test that the directory structure is created correctly."""
    # Create a temporary directory to simulate the project root
    project_root = tmp_path / "project_root"
    project_root.mkdir()
    
    # Mock the base_dir by changing the working directory
    original_cwd = os.getcwd()
    os.chdir(str(project_root))
    
    # Create a mock setup_directories.py in the code directory
    code_dir = project_root / "code"
    code_dir.mkdir()
    setup_script = code_dir / "setup_directories.py"
    
    # Read the actual script content
    actual_script_path = Path(__file__).resolve().parent.parent / "code" / "setup_directories.py"
    with open(actual_script_path, "r") as f:
        script_content = f.read()
    
    # Modify the script to use the temp directory as base
    # We need to override the base_dir calculation
    modified_content = script_content.replace(
        "base_dir = Path(__file__).resolve().parent.parent",
        f'base_dir = Path(r"{project_root}")'
    )
    
    with open(setup_script, "w") as f:
        f.write(modified_content)
    
    try:
        # Import and run the modified script
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_directories", setup_script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run the main function
        result = module.main()
        
        # Verify directories were created
        expected_dirs = [
            "code/data_ingestion",
            "code/modeling",
            "code/reporting",
            "code/utils",
            "tests",
            "data/raw",
            "data/processed",
            "results",
            "logs",
            "docs"
        ]
        
        for dir_path in expected_dirs:
            full_path = project_root / dir_path
            assert full_path.exists(), f"Directory {dir_path} was not created"
            assert full_path.is_dir(), f"{dir_path} is not a directory"
        
        assert result == 0, "main() did not return 0"
        
    finally:
        # Restore original working directory
        os.chdir(original_cwd)

def test_idempotency(tmp_path):
    """Test that running the script twice doesn't cause errors."""
    project_root = tmp_path / "project_root"
    project_root.mkdir()
    
    original_cwd = os.getcwd()
    os.chdir(str(project_root))
    
    code_dir = project_root / "code"
    code_dir.mkdir()
    setup_script = code_dir / "setup_directories.py"
    
    actual_script_path = Path(__file__).resolve().parent.parent / "code" / "setup_directories.py"
    with open(actual_script_path, "r") as f:
        script_content = f.read()
    
    modified_content = script_content.replace(
        "base_dir = Path(__file__).resolve().parent.parent",
        f'base_dir = Path(r"{project_root}")'
    )
    
    with open(setup_script, "w") as f:
        f.write(modified_content)
    
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location("setup_directories", setup_script)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Run twice
        result1 = module.main()
        result2 = module.main()
        
        assert result1 == 0
        assert result2 == 0
        
    finally:
        os.chdir(original_cwd)