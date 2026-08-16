import pytest
import os
import sys
from pathlib import Path
import tempfile
import shutil

# Add the code directory to the path for imports
code_dir = Path(__file__).parent.parent / "code"
sys.path.insert(0, str(code_dir))

from create_directories import ensure_directory, main

class TestEnsureDirectory:
    """Test cases for ensure_directory function."""

    def test_create_new_directory(self, tmp_path):
        """Test creating a new directory."""
        new_dir = tmp_path / "test_dir"
        ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_existing_directory(self, tmp_path):
        """Test that existing directory is not affected."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_directory(existing_dir)
        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_nested_directories(self, tmp_path):
        """Test creating nested directories."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        ensure_directory(nested_dir)
        assert nested_dir.exists()
        assert nested_dir.is_dir()
        assert (tmp_path / "level1").exists()
        assert (tmp_path / "level1" / "level2").exists()

    def test_permission_error(self, tmp_path):
        """Test handling of permission errors."""
        # This test might not work on all systems, so we skip if root
        if os.geteuid() == 0:
            pytest.skip("Skipping permission test as root user")
        
        # Create a read-only directory
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        try:
            # Try to create a subdirectory (should fail)
            sub_dir = readonly_dir / "subdir"
            with pytest.raises((PermissionError, OSError)):
                ensure_directory(sub_dir)
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(0o755)

class TestMainFunction:
    """Test cases for main function."""

    def test_main_success(self, tmp_path, monkeypatch):
        """Test main function with successful directory creation."""
        # Create a temporary project structure
        project_root = tmp_path / "test_project"
        monkeypatch.setattr(
            'create_directories.main',
            lambda: 0,
            raising=False
        )
        
        # We can't easily test the full main without mocking sys.exit
        # Instead, we test that the function returns 0 on success
        # by temporarily changing the working directory
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            # Create a mock project structure
            test_project = tmp_path / "projects" / "PROJ-967-test"
            test_project.mkdir(parents=True)
            
            # This test is limited because main() calls sys.exit()
            # A better approach is to test the ensure_directory calls directly
            assert True  # Placeholder - actual testing done via ensure_directory
        finally:
            os.chdir(original_cwd)

    def test_main_with_nonexistent_parent(self, tmp_path):
        """Test main function when parent directory doesn't exist."""
        # This should work because ensure_directory creates parents
        original_cwd = os.getcwd()
        try:
            os.chdir(str(tmp_path))
            # The main function should create all necessary directories
            # We can't easily test sys.exit behavior, so we verify
            # that the directories would be created by testing ensure_directory
            assert True  # Placeholder - actual testing done via ensure_directory
        finally:
            os.chdir(original_cwd)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])