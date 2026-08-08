import os
import shutil
import tempfile
from pathlib import Path
import pytest
import sys

# Add the code directory to the path to import the script
code_dir = Path(__file__).parent.parent.parent / "code"
sys.path.insert(0, str(code_dir))

from create_t001_root import main

class TestT001RootCreation:
    def setup_method(self):
        """Create a temporary directory to simulate the project root."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
    
    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_root_directory_created(self):
        """Verify that the main project root and code directory are created."""
        project_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin")
        code_path = project_path / "code"
        
        # Run the main function
        result = main()
        
        assert result is True
        assert project_path.exists()
        assert code_path.exists()
        assert code_path.is_dir()

    def test_standard_subdirectories_created(self):
        """Verify that standard subdirectories (src, tests, data) are created."""
        project_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin")
        code_path = project_path / "code"
        
        main()
        
        required_dirs = ["src", "tests", "data", "logs", "models", "figures", "configs"]
        
        for dir_name in required_dirs:
            dir_path = code_path / dir_name
            assert dir_path.exists(), f"Directory {dir_path} was not created"
            assert dir_path.is_dir(), f"{dir_path} is not a directory"

    def test_marker_file_created(self):
        """Verify that the initialization marker file is created."""
        project_path = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin")
        code_path = project_path / "code"
        
        main()
        
        marker = code_path / ".t001_initialized"
        assert marker.exists(), "Initialization marker file not found"
        assert marker.is_file(), "Marker is not a file"