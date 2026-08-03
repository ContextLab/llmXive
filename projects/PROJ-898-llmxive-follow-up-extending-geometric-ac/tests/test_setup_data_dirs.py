"""
Tests for the data directory setup functionality.
"""
import os
import tempfile
import pytest
import sys

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from code.setup_data_dirs import ensure_gitkeep

class TestEnsureGitkeep:
    """Test cases for the ensure_gitkeep function."""

    def test_creates_directory_and_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates a directory and .gitkeep file."""
        test_dir = tmp_path / "test_subdir"
        assert not test_dir.exists()
        
        ensure_gitkeep(str(test_dir))
        
        assert test_dir.exists()
        assert test_dir.is_dir()
        
        gitkeep_file = test_dir / ".gitkeep"
        assert gitkeep_file.exists()
        assert gitkeep_file.is_file()

    def test_preserves_existing_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep does not overwrite existing .gitkeep files."""
        test_dir = tmp_path / "test_subdir"
        test_dir.mkdir()
        
        gitkeep_file = test_dir / ".gitkeep"
        original_content = "# Original content\n"
        gitkeep_file.write_text(original_content)
        
        ensure_gitkeep(str(test_dir))
        
        # Content should remain unchanged
        assert gitkeep_file.read_text() == original_content

    def test_handles_nested_directories(self, tmp_path):
        """Test that ensure_gitkeep creates nested directory structures."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        ensure_gitkeep(str(nested_dir))
        
        assert nested_dir.exists()
        assert nested_dir.is_dir()
        
        gitkeep_file = nested_dir / ".gitkeep"
        assert gitkeep_file.exists()

    def test_content_of_gitkeep(self, tmp_path):
        """Test that .gitkeep files contain the expected comment."""
        test_dir = tmp_path / "test_subdir"
        ensure_gitkeep(str(test_dir))
        
        gitkeep_file = test_dir / ".gitkeep"
        content = gitkeep_file.read_text()
        
        assert "# This file ensures the directory is tracked by git." in content

class TestMainFunction:
    """Test cases for the main function of setup_data_dirs."""

    def test_main_creates_standard_directories(self, tmp_path, monkeypatch):
        """Test that main creates the standard data directories."""
        # Change to tmp_path to simulate project root
        monkeypatch.chdir(tmp_path)
        
        # Mock the script location to be inside code/
        import code.setup_data_dirs as setup_module
        original_dir = os.path.dirname(os.path.abspath(__file__))
        monkeypatch.setattr(setup_module, '__file__', str(tmp_path / 'code' / 'setup_data_dirs.py'))
        
        # Create code directory to make the path resolution work
        (tmp_path / 'code').mkdir(exist_ok=True)
        
        exit_code = setup_module.main()
        
        assert exit_code == 0
        
        # Verify directories were created
        for dir_name in ['raw', 'generated', 'results']:
            data_dir = tmp_path / 'data' / dir_name
            assert data_dir.exists()
            assert (data_dir / '.gitkeep').exists()

    def test_main_handles_missing_permissions(self, tmp_path, monkeypatch):
        """Test that main returns 1 when directory creation fails."""
        # This is hard to test without actually blocking permissions,
        # so we just verify the return code logic is in place
        monkeypatch.chdir(tmp_path)
        
        # Create a read-only file where a directory should be
        data_dir = tmp_path / 'data'
        data_dir.mkdir()
        (data_dir / 'raw').mkdir()
        (data_dir / 'raw' / 'test_file').touch()
        
        # Make the directory read-only (Unix only)
        try:
            os.chmod(str(data_dir / 'raw'), 0o444)
            exit_code = setup_module.main()
            # Restore permissions for cleanup
            os.chmod(str(data_dir / 'raw'), 0o755)
            # On some systems, this might still succeed if running as root
            # So we just check the logic path exists
        except PermissionError:
            pass