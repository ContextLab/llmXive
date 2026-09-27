"""
Tests for the directory setup functionality (T008a).
"""
import os
import tempfile
from pathlib import Path
import pytest
import sys

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from code.data.setup_directories import create_directories, verify_directories
from utils.config import get_project_root

def test_directory_creation_and_verification():
    """
    Test that the required directories are created and can be verified.
    This test mocks the project root to a temporary directory to avoid side effects.
    """
    # We rely on the actual implementation which uses get_project_root().
    # In a real CI environment, we would ensure the project root is correct.
    # For this test, we assume the script is run from the project root.
    
    # We cannot easily mock get_project_root without patching the module,
    # so we will test the logic by ensuring the paths exist after running the main logic
    # if we were to run it. Instead, we test the helper functions directly if we can inject a path.
    # However, the current implementation hardcodes the usage of get_project_root() inside.
    
    # To properly test, we would need to refactor to accept a path argument or mock get_project_root.
    # Given the constraint to extend, we will write a test that runs the main logic in a temp dir
    # by temporarily patching get_project_root.
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        original_get_project_root = get_project_root
        
        # Patch get_project_root to return our temp directory
        import utils.config
        utils.config.get_project_root = lambda: Path(tmp_dir)
        
        try:
            # Import logger setup
            from utils.logging import configure_root_logger, get_logger
            configure_root_logger()
            logger = get_logger("test_setup")
            
            # Run the logic
            create_directories(logger)
            
            # Verify the directories exist
            base_path = Path(tmp_dir)
            assert (base_path / "data" / "raw").is_dir()
            assert (base_path / "data" / "processed").is_dir()
            assert (base_path / "state" / "projects").is_dir()
            assert (base_path / "state" / "pending").is_dir()
            
            # Run the verification function to ensure it doesn't raise
            verify_directories(logger)
            
        finally:
            # Restore original function
            utils.config.get_project_root = original_get_project_root