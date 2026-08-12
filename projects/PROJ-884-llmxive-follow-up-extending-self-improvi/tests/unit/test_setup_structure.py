import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add code to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_structure import main

def test_structure_creation(tmp_path):
    """
    Test that the setup_structure script creates the required directory tree.
    Since the script writes to a hardcoded path relative to CWD, we change CWD
    to a temp directory for this test.
    """
    original_cwd = os.getcwd()
    try:
        # Change to temp directory so the 'projects' folder is created inside it
        os.chdir(tmp_path)
        
        # Run the main function
        result = main()
        
        assert result == 0, "Setup script should return 0 on success"
        
        project_root = Path(tmp_path) / "projects/PROJ-884-llmxive-follow-up-extending-self-improvi"
        
        # Verify the root exists
        assert project_root.exists(), "Project root directory must exist"
        
        # Verify subdirectories
        required_dirs = [
            "data/raw",
            "data/processed",
            "code/dataset",
            "code/symbolic",
            "code/bes",
            "code/analysis",
            "code/utils",
            "tests/unit",
            "tests/integration",
        ]
        
        for dir_name in required_dirs:
            full_path = project_root / dir_name
            assert full_path.exists(), f"Directory {full_path} was not created"
            assert full_path.is_dir(), f"{full_path} is not a directory"
    
    finally:
        # Restore original working directory
        os.chdir(original_cwd)
