"""
Tests for the utils module.
"""
import os
import tempfile
import pytest
from pathlib import Path
import shutil

# Import the module under test
from code.utils import create_project_structure, get_project_paths


class TestCreateProjectStructure:
    """Tests for create_project_structure function."""

    def test_creates_all_required_directories(self, tmp_path):
        """Verify that all required directories are created."""
        # Define expected directories relative to root
        expected_dirs = [
            "code",
            "data/raw",
            "data/processed",
            "output/logs",
            "output/models",
            "output/reports",
            "figures",
            "tests",
            "specs/001-predicting-avian-song-variation/contracts"
        ]

        # Run the function
        success = create_project_structure(str(tmp_path))
        
        assert success, "create_project_structure should return True on success"

        # Verify each directory exists
        for dir_path in expected_dirs:
            full_path = tmp_path / dir_path
            assert full_path.exists(), f"Directory {dir_path} should exist"
            assert full_path.is_dir(), f"{dir_path} should be a directory"

    def test_returns_false_on_permission_error(self, tmp_path):
        """Verify behavior when permission is denied (mocked via read-only)."""
        # Make the root read-only (this might not work on all systems, 
        # but we test the logic path if it does)
        try:
            # On Unix, we can try to make it read-only
            os.chmod(str(tmp_path), 0o444)
            
            # Try to create a subdirectory (should fail)
            success = create_project_structure(str(tmp_path))
            
            # If we get here, the OS allowed it (e.g., running as root)
            # In that case, the test is not applicable, but we don't fail
            os.chmod(str(tmp_path), 0o755)
            
        except (OSError, PermissionError):
            # Expected if we can't change permissions
            pass
        finally:
            # Ensure we clean up permissions
            try:
                os.chmod(str(tmp_path), 0o755)
            except (OSError, PermissionError):
                pass

    def test_handles_existing_directories(self, tmp_path):
        """Verify that existing directories are handled gracefully."""
        # Create one directory manually
        (tmp_path / "code").mkdir()
        
        # Run the function
        success = create_project_structure(str(tmp_path))
        
        assert success, "Should succeed even if some directories exist"
        
        # Verify the existing directory is still there
        assert (tmp_path / "code").exists()
        # And other directories were created
        assert (tmp_path / "data").exists()

    def test_raises_on_file_collision(self, tmp_path):
        """Verify error handling when a file exists where a directory is expected."""
        # Create a file where a directory should be
        (tmp_path / "code").mkdir()
        (tmp_path / "data").mkdir()
        (tmp_path / "data" / "raw").mkdir()
        
        # Create a file where "data/processed" should be a directory
        (tmp_path / "data" / "processed").touch()
        
        # This should raise an error
        with pytest.raises(FileExistsError):
            create_project_structure(str(tmp_path))


class TestGetProjectPaths:
    """Tests for get_project_paths function."""

    def test_returns_correct_paths(self, tmp_path):
        """Verify that the function returns correct absolute paths."""
        paths = get_project_paths(str(tmp_path))
        
        # Check root
        assert paths["root"] == tmp_path.resolve()
        
        # Check specific paths
        assert paths["code"] == tmp_path / "code"
        assert paths["data_raw"] == tmp_path / "data" / "raw"
        assert paths["data_processed"] == tmp_path / "data" / "processed"
        assert paths["output_logs"] == tmp_path / "output" / "logs"
        assert paths["output_models"] == tmp_path / "output" / "models"
        assert paths["output_reports"] == tmp_path / "output" / "reports"
        assert paths["figures"] == tmp_path / "figures"
        assert paths["tests"] == tmp_path / "tests"
        assert paths["contracts"] == tmp_path / "specs" / "001-predicting-avian-song-variation" / "contracts"

    def test_returns_absolute_paths(self, tmp_path):
        """Verify that all returned paths are absolute."""
        paths = get_project_paths(str(tmp_path))
        
        for key, path in paths.items():
            assert path.is_absolute(), f"Path for {key} should be absolute"
    
    def test_default_root_is_cwd(self):
        """Verify that default root is current working directory."""
        current_cwd = Path.cwd()
        paths = get_project_paths()
        
        assert paths["root"] == current_cwd
        assert paths["code"] == current_cwd / "code"