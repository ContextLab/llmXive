import os
import pytest
from code.setup_state_directories import create_directories

class TestStateDirectoryCreation:
    """Tests for T001c: Create project directory structure: `state/`."""

    def test_state_directory_exists(self):
        """Verify that the state/ directory is created."""
        # Ensure directories exist by running the setup function
        create_directories()
        
        assert os.path.isdir("state"), "The 'state/' directory must exist."

    def test_project_specific_state_directory_exists(self):
        """Verify that state/PROJ-485/ is created."""
        # Ensure directories exist by running the setup function
        create_directories()
        
        assert os.path.isdir("state/PROJ-485"), "The 'state/PROJ-485/' directory must exist."

    def test_directory_structure_persistent(self):
        """Verify directories persist after creation."""
        create_directories()
        
        # Check again to ensure they weren't temporary
        assert os.path.exists("state")
        assert os.path.exists("state/PROJ-485")