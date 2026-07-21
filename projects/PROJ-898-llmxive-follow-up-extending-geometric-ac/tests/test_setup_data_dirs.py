"""
Tests for data directory structure setup functionality.
"""

import os
import sys
import tempfile
import shutil
import pytest

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import ensure_gitkeep, REQUIRED_DATA_DIRS


class TestEnsureGitkeep:
    """Tests for the ensure_gitkeep function."""

    def test_creates_gitkeep_in_new_directory(self):
        """Test that .gitkeep is created in a new directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_data")
            gitkeep_path = os.path.join(test_dir, ".gitkeep")
            
            # Directory doesn't exist yet
            assert not os.path.exists(test_dir)
            assert not os.path.exists(gitkeep_path)
            
            # Call the function
            result = ensure_gitkeep(test_dir)
            
            # Verify results
            assert result is True
            assert os.path.exists(test_dir)
            assert os.path.exists(gitkeep_path)
            assert os.path.isfile(gitkeep_path)

    def test_preserves_existing_gitkeep(self):
        """Test that existing .gitkeep files are not overwritten."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "test_data")
            gitkeep_path = os.path.join(test_dir, ".gitkeep")
            
            # Create directory and .gitkeep with specific content
            os.makedirs(test_dir, exist_ok=True)
            original_content = "# Original content\n"
            with open(gitkeep_path, 'w') as f:
                f.write(original_content)
            
            # Call the function
            result = ensure_gitkeep(test_dir)
            
            # Verify results
            assert result is True
            assert os.path.exists(gitkeep_path)
            
            # Content should be unchanged
            with open(gitkeep_path, 'r') as f:
                content = f.read()
            assert content == original_content

    def test_handles_nested_directories(self):
        """Test that nested directories are created properly."""
        with tempfile.TemporaryDirectory() as tmpdir:
            test_dir = os.path.join(tmpdir, "data", "raw", "subdir")
            gitkeep_path = os.path.join(test_dir, ".gitkeep")
            
            # Call the function
            result = ensure_gitkeep(test_dir)
            
            # Verify results
            assert result is True
            assert os.path.exists(test_dir)
            assert os.path.exists(gitkeep_path)


class TestRequiredDataDirs:
    """Tests for the REQUIRED_DATA_DIRS constant."""

    def test_required_dirs_listed(self):
        """Test that all required data directories are listed."""
        expected_dirs = ["data/raw", "data/generated", "data/results"]
        assert set(REQUIRED_DATA_DIRS) == set(expected_dirs)

    def test_no_duplicates(self):
        """Test that there are no duplicate directories in the list."""
        assert len(REQUIRED_DATA_DIRS) == len(set(REQUIRED_DATA_DIRS))


class TestIntegration:
    """Integration tests for the full setup process."""

    def test_setup_all_required_dirs(self):
        """Test that all required directories can be set up in a temp project."""
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create a mock project structure
            code_dir = os.path.join(tmpdir, "code")
            os.makedirs(code_dir)
            
            # Copy the module to temp location
            import setup_data_dirs
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "setup_data_dirs",
                os.path.join(os.path.dirname(__file__), '..', 'code', 'setup_data_dirs.py')
            )
            module = importlib.util.module_from_spec(spec)
            
            # Temporarily modify the module to work with our temp dir
            original_makedirs = os.makedirs
            original_join = os.path.join
            
            def mock_makedirs(path, *args, **kwargs):
                # Convert relative paths to absolute
                if not os.path.isabs(path):
                    path = os.path.join(tmpdir, path)
                return original_makedirs(path, *args, **kwargs)
            
            def mock_join(*args):
                result = original_join(*args)
                if not os.path.isabs(result) and len(args) > 1:
                    # If first arg is relative, make it relative to tmpdir
                    if not os.path.isabs(args[0]):
                        return os.path.join(tmpdir, result)
                return result
            
            # Monkey patch
            os.makedirs = mock_makedirs
            os.path.join = mock_join
            
            try:
                # Run the setup
                success = True
                for data_dir in module.REQUIRED_DATA_DIRS:
                    full_path = mock_join(tmpdir, data_dir)
                    if not module.ensure_gitkeep(full_path):
                        success = False
                
                # Verify all directories were created
                for data_dir in module.REQUIRED_DATA_DIRS:
                    full_path = mock_join(tmpdir, data_dir)
                    gitkeep_path = os.path.join(full_path, ".gitkeep")
                    assert os.path.exists(full_path), f"Directory {full_path} not created"
                    assert os.path.exists(gitkeep_path), f".gitkeep not created in {full_path}"
                
                assert success
            finally:
                # Restore original functions
                os.makedirs = original_makedirs
                os.path.join = original_join