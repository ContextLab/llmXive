import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Adjust path to import the module if running from tests/
# In the actual project structure, this import assumes the test runner is configured correctly
# or we are running from the root. For this artifact, we assume standard PYTHONPATH setup.
try:
    from code.setup_project import get_project_root, setup_directories, REQUIRED_DIRS
except ImportError:
    # Fallback for direct execution testing if needed, though the agent expects standard layout
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.setup_project import get_project_root, setup_directories, REQUIRED_DIRS

class TestSetupProject:
    
    def test_get_project_root_returns_path(self):
        """Verify that get_project_root returns a valid Path object."""
        root = get_project_root()
        assert isinstance(root, Path)
        assert root.name == "PROJ-355-predicting-the-impact-of-impurity-cluste"
        assert root.parent.name == "projects"

    def test_setup_directories_creates_structure(self, tmp_path):
        """
        Verify that setup_directories creates the required subdirectories.
        We mock the get_project_root to point to a temporary directory 
        to avoid polluting the actual file system during tests.
        """
        # Temporarily override the root for this test
        original_root_func = get_project_root
        
        # Create a temp project root
        temp_projects = tmp_path / "projects" / "PROJ-355-predicting-the-impact-of-impurity-cluste"
        
        # We need to patch the function or the module's internal reference.
        # Since we can't easily patch the module-level call inside setup_directories 
        # without monkeypatching the module, we will rely on the fact that 
        # the function uses `__file__` to determine base.
        # To make this test robust, we will execute the logic manually against tmp_path
        # and verify the structure matches REQUIRED_DIRS.
        
        import code.setup_project as sp
        
        # Save original function
        original_get_root = sp.get_project_root
        
        # Mock get_project_root to return our temp path
        def mock_root():
            return temp_projects
        
        sp.get_project_root = mock_root
        
        try:
            success, created_paths = sp.setup_directories()
            
            assert success is True
            assert len(created_paths) > 1
            
            # Verify all required dirs exist
            for dir_name in sp.REQUIRED_DIRS:
                target = temp_projects / dir_name
                assert target.exists(), f"Directory {target} was not created"
                assert target.is_dir(), f"{target} is not a directory"
                
                # Check for .gitkeep
                gitkeep = target / ".gitkeep"
                assert gitkeep.exists(), f".gitkeep missing in {target}"
        finally:
            # Restore original function
            sp.get_project_root = original_get_root

    def test_idempotency(self, tmp_path):
        """Verify that running setup twice does not cause errors."""
        import code.setup_project as sp
        original_get_root = sp.get_project_root
        
        temp_projects = tmp_path / "projects" / "PROJ-355-predicting-the-impact-of-impurity-cluste"
        
        def mock_root():
            return temp_projects
        
        sp.get_project_root = mock_root
        
        try:
            # First run
            success1, _ = sp.setup_directories()
            assert success1
            
            # Second run
            success2, _ = sp.setup_directories()
            assert success2
            
            # Verify structure still intact
            for dir_name in sp.REQUIRED_DIRS:
                assert (temp_projects / dir_name).exists()
        finally:
            sp.get_project_root = original_get_root
