import os
import pytest
from pathlib import Path
import tempfile
import shutil

def test_directory_structure_creation(tmp_path):
    """
    Test that setup_structure creates the required directory tree.
    """
    # Temporarily override the root path for testing
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    
    try:
        # Import the function
        from code.code.setup_structure import main
        
        # Run the setup
        main()
        
        # Verify directories exist
        required_dirs = [
            "src", "tests", "data", "figures", "logs", "report", "artifacts",
            "data/processed", "data/raw",
            "tests/unit", "tests/integration",
            "src/utils", "src/data", "src/cli", "src/viz"
        ]
        
        for dir_name in required_dirs:
            dir_path = tmp_path / dir_name
            assert dir_path.exists(), f"Directory {dir_name} was not created"
            assert dir_path.is_dir(), f"{dir_name} is not a directory"
        
        # Verify __init__.py files exist in src and tests
        init_files = [
            "src/__init__.py", "tests/__init__.py",
            "src/utils/__init__.py", "src/data/__init__.py",
            "src/cli/__init__.py", "src/viz/__init__.py",
            "tests/unit/__init__.py", "tests/integration/__init__.py"
        ]
        
        for init_file in init_files:
            file_path = tmp_path / init_file
            assert file_path.exists(), f"File {init_file} was not created"
            assert file_path.is_file(), f"{init_file} is not a file"
            
    finally:
        os.chdir(original_cwd)

def test_readme_files_exist():
    """
    Verify that README.md files exist in data/processed and figures.
    This test assumes the project structure has been initialized.
    """
    # Check relative to the project root (where the test is run from)
    # We assume the test is run from the project root or the structure is already there
    # For CI, we check if the files exist in the expected locations relative to the repo root
    repo_root = Path(__file__).resolve().parent.parent.parent
    
    processed_readme = repo_root / "data" / "processed" / "README.md"
    figures_readme = repo_root / "figures" / "README.md"
    
    # If the structure hasn't been run yet, we can't assert existence here in a unit test
    # This is more of an integration check. For the purpose of T011, we verify the logic
    # exists in setup_structure or manual creation.
    # However, since T011 requires the files to EXIST, we assert here if they do.
    # In a real CI run, setup_structure would have run first.
    # If they don't exist, it means the environment wasn't set up, which is a failure of T011.
    assert processed_readme.exists(), "data/processed/README.md does not exist"
    assert figures_readme.exists(), "figures/README.md does not exist"
    
    # Verify content is not empty
    assert processed_readme.stat().st_size > 0, "data/processed/README.md is empty"
    assert figures_readme.stat().st_size > 0, "figures/README.md is empty"