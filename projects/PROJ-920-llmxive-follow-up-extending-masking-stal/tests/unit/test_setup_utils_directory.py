"""
Unit tests for the setup_utils_directory script.
Verifies that the code/utils/ directory is created correctly.
"""
import os
import shutil
import tempfile
from pathlib import Path
import sys

# Add the code directory to the path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "projects" / "PROJ-920-llmxive-follow-up-extending-masking-stal" / "code"))

from setup_utils_directory import main

def test_utils_directory_creation():
    """Test that the code/utils/ directory is created."""
    # Create a temporary directory to simulate the project root
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "projects" / "PROJ-920-llmxive-follow-up-extending-masking-stal"
        project_root.mkdir(parents=True)
        
        # Change to the temporary project root
        original_cwd = os.getcwd()
        os.chdir(project_root.parent)
        
        try:
            # Run the main function
            main()
            
            # Verify the directory exists
            utils_dir = project_root / "code" / "utils"
            assert utils_dir.exists(), f"Directory {utils_dir} was not created"
            assert utils_dir.is_dir(), f"{utils_dir} is not a directory"
            
            # Verify __init__.py exists
            init_file = utils_dir / "__init__.py"
            assert init_file.exists(), f"__init__.py was not created in {utils_dir}"
            
        finally:
            os.chdir(original_cwd)

def test_utils_directory_already_exists():
    """Test that the script handles existing directory gracefully."""
    with tempfile.TemporaryDirectory() as tmpdir:
        project_root = Path(tmpdir) / "projects" / "PROJ-920-llmxive-follow-up-extending-masking-stal"
        project_root.mkdir(parents=True)
        
        utils_dir = project_root / "code" / "utils"
        utils_dir.mkdir(parents=True)
        (utils_dir / "__init__.py").write_text("")
        
        original_cwd = os.getcwd()
        os.chdir(project_root.parent)
        
        try:
            # Run the main function
            main()
            
            # Verify the directory still exists
            assert utils_dir.exists(), f"Directory {utils_dir} was removed"
            assert utils_dir.is_dir(), f"{utils_dir} is not a directory"
            
        finally:
            os.chdir(original_cwd)
