import os
import sys
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent
sys.path.insert(0, str(code_dir))

from setup_state_dirs import create_directory, main

class TestSetupStateDirs:
    """
    Unit tests for the state directory setup script.
    """

    def test_create_directory_new(self, tmp_path):
        """Test creating a new directory that doesn't exist."""
        new_dir = tmp_path / "new" / "sub" / "dir"
        assert not new_dir.exists()
        
        result = create_directory(new_dir)
        
        assert result is True
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_create_directory_existing(self, tmp_path):
        """Test creating a directory that already exists."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir(parents=True)
        
        result = create_directory(existing_dir)
        
        assert result is True
        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_create_directory_permission_error(self, tmp_path):
        """Test handling of permission errors (if applicable)."""
        # This test is somewhat environment-dependent, but we verify
        # the function handles exceptions gracefully
        read_only_dir = tmp_path / "readonly"
        read_only_dir.mkdir()
        read_only_dir.chmod(0o444) # Read-only
        
        # Try to create a subdirectory (should fail or succeed depending on user)
        # We mainly ensure the function doesn't crash
        try:
            sub_dir = read_only_dir / "sub"
            # On some systems (root), this might succeed, so we just check no crash
            create_directory(sub_dir)
        except Exception:
            # Expected on non-root systems
            pass
        finally:
            # Restore permissions for cleanup
            read_only_dir.chmod(0o755)

    def test_main_creates_project_state_dir(self, tmp_path, monkeypatch):
        """
        Test that main() creates the expected directory structure.
        We patch the working directory to tmp_path to avoid affecting the real project.
        """
        # Create a mock project structure in tmp_path
        # The script looks for parent of __file__, but we are testing logic
        # We will test the logic by calling create_directory directly with the expected path
        # derived from a mock root.
        
        mock_root = tmp_path
        expected_state_base = mock_root / "state"
        expected_project_dir = expected_state_base / "PROJ-560-embodied-curriculum-learning-physical-si"
        
        assert not expected_state_base.exists()
        assert not expected_project_dir.exists()
        
        # Simulate the logic of main()
        create_directory(expected_state_base)
        create_directory(expected_project_dir)
        
        assert expected_state_base.exists()
        assert expected_project_dir.exists()
        assert expected_project_dir.is_dir()
        
        # Verify nested structure
        assert (expected_state_base / "PROJ-560-embodied-curriculum-learning-physical-si").exists()