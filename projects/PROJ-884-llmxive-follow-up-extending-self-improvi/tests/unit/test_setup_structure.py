"""
Unit tests for the setup_structure module.
Verifies that the code directory hierarchy is created and writable.
"""
import os
import pytest
import tempfile
from pathlib import Path
import sys

# Add the parent directory to the path to allow importing setup_structure
# This assumes the test is run from the tests/unit directory or similar
# and the code directory is at the repository root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from code.setup_structure import setup_code_directories, CODE_ROOT, REQUIRED_DIRS

class TestSetupCodeDirectories:
    """Tests for the setup_code_directories function."""

    def test_directories_created(self, tmp_path):
        """Test that directories are created if they don't exist."""
        # We need to mock the CODE_ROOT to use a temporary directory
        # Since CODE_ROOT is a global, we'll test the logic by creating a temp structure
        # and checking if the function would work with it.
        
        # Create a temporary directory structure to simulate the project
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_code_root = Path(tmp_dir) / "code"
            temp_code_root.mkdir()
            
            # Verify directories don't exist yet
            for dir_name in REQUIRED_DIRS:
                target = temp_code_root / dir_name
                assert not target.exists(), f"Directory {target} should not exist initially"
            
            # Temporarily patch CODE_ROOT for this test
            import code.setup_structure as setup_module
            original_code_root = setup_module.CODE_ROOT
            setup_module.CODE_ROOT = temp_code_root
            
            try:
                created = setup_code_directories()
                
                # Verify all directories were created
                for dir_name in REQUIRED_DIRS:
                    target = temp_code_root / dir_name
                    assert target.exists(), f"Directory {target} was not created"
                    assert target.is_dir(), f"{target} is not a directory"
                    assert os.access(target, os.W_OK), f"{target} is not writable"
                    
                # Verify the returned list contains the correct paths
                assert len(created) == len(REQUIRED_DIRS)
                for i, dir_name in enumerate(REQUIRED_DIRS):
                    assert str(temp_code_root / dir_name) in created
            finally:
                # Restore original CODE_ROOT
                setup_module.CODE_ROOT = original_code_root

    def test_directories_exist_and_writable(self, tmp_path):
        """Test that existing directories are verified as writable."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_code_root = Path(tmp_dir) / "code"
            temp_code_root.mkdir()
            
            # Create the required directories
            for dir_name in REQUIRED_DIRS:
                (temp_code_root / dir_name).mkdir()
            
            # Patch CODE_ROOT
            import code.setup_structure as setup_module
            original_code_root = setup_module.CODE_ROOT
            setup_module.CODE_ROOT = temp_code_root
            
            try:
                created = setup_code_directories()
                
                # Should still return all directories
                assert len(created) == len(REQUIRED_DIRS)
                
                # Verify they are writable
                for dir_name in REQUIRED_DIRS:
                    target = temp_code_root / dir_name
                    assert os.access(target, os.W_OK)
            finally:
                setup_module.CODE_ROOT = original_code_root

    def test_non_writable_directory_raises_error(self, tmp_path):
        """Test that a non-writable directory raises a RuntimeError."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            temp_code_root = Path(tmp_dir) / "code"
            temp_code_root.mkdir()
            
            # Create one directory and make it read-only
            test_dir = temp_code_root / REQUIRED_DIRS[0]
            test_dir.mkdir()
            test_dir.chmod(0o444)  # Read-only
            
            # Patch CODE_ROOT
            import code.setup_structure as setup_module
            original_code_root = setup_module.CODE_ROOT
            setup_module.CODE_ROOT = temp_code_root
            
            try:
                # This should raise a RuntimeError
                with pytest.raises(RuntimeError) as exc_info:
                    setup_code_directories()
                
                assert "not writable" in str(exc_info.value).lower()
            finally:
                # Restore permissions for cleanup
                test_dir.chmod(0o755)
                setup_module.CODE_ROOT = original_code_root
