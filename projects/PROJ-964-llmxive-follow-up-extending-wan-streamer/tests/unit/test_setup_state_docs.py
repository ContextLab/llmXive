import os
import sys
import pytest
from pathlib import Path
import tempfile
import shutil

# Add code/ to path to allow imports
code_dir = Path(__file__).parent.parent.parent / "code"
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from setup_state_docs import setup_state_docs_directories

class TestSetupStateDocs:
    """
    Unit tests for setup_state_docs_directories.
    Verifies that 'state/' and 'docs/' directories are created and exist.
    """

    def setup_method(self):
        """
        Create a temporary directory structure to simulate the project root.
        """
        self.temp_dir = tempfile.mkdtemp()
        # Create a mock 'code' directory inside temp to test path resolution
        self.mock_code_dir = Path(self.temp_dir) / "code"
        self.mock_code_dir.mkdir()
        # Change current working directory to the mock 'code' directory
        # to test the path resolution logic in the function
        self.original_cwd = os.getcwd()
        os.chdir(self.mock_code_dir)

    def teardown_method(self):
        """
        Restore original working directory and clean up temp directory.
        """
        os.chdir(self.original_cwd)
        shutil.rmtree(self.temp_dir)

    def test_state_directory_created(self):
        """
        Test that the 'state/' directory is created at the project root.
        """
        # Run the setup function
        # The function determines project root relative to cwd
        result = setup_state_docs_directories()
        
        assert result is True, "setup_state_docs_directories should return True on success"
        
        project_root = Path(self.temp_dir)
        state_dir = project_root / "state"
        
        assert state_dir.exists(), f"Directory {state_dir} should exist"
        assert state_dir.is_dir(), f"{state_dir} should be a directory"

    def test_docs_directory_created(self):
        """
        Test that the 'docs/' directory is created at the project root.
        """
        # Run the setup function
        result = setup_state_docs_directories()
        
        assert result is True, "setup_state_docs_directories should return True on success"
        
        project_root = Path(self.temp_dir)
        docs_dir = project_root / "docs"
        
        assert docs_dir.exists(), f"Directory {docs_dir} should exist"
        assert docs_dir.is_dir(), f"{docs_dir} should be a directory"

    def test_os_path_isdir_verification(self):
        """
        Explicitly verify using os.path.isdir as required by the task spec.
        """
        setup_state_docs_directories()
        
        project_root = Path(self.temp_dir)
        state_dir = str(project_root / "state")
        docs_dir = str(project_root / "docs")
        
        assert os.path.isdir(state_dir), f"os.path.isdir('{state_dir}') must be True"
        assert os.path.isdir(docs_dir), f"os.path.isdir('{docs_dir}') must be True"

    def test_idempotency(self):
        """
        Test that running the function multiple times does not raise errors.
        """
        # Run twice
        result1 = setup_state_docs_directories()
        result2 = setup_state_docs_directories()
        
        assert result1 is True
        assert result2 is True
        
        project_root = Path(self.temp_dir)
        assert (project_root / "state").is_dir()
        assert (project_root / "docs").is_dir()