import os
import tempfile
import pytest
import sys

# Add the code directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'code'))

from setup_data_dirs import ensure_gitkeep

class TestSetupDataDirs:
    """Tests for the data directory setup functionality."""

    def test_ensure_gitkeep_creates_directory(self, tmp_path):
        """Test that ensure_gitkeep creates the directory if it doesn't exist."""
        test_dir = tmp_path / "test_subdir"
        assert not test_dir.exists()
        
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_ensure_gitkeep_creates_gitkeep(self, tmp_path):
        """Test that ensure_gitkeep creates the .gitkeep file."""
        test_dir = tmp_path / "test_subdir"
        
        ensure_gitkeep(str(test_dir))
        
        gitkeep_path = test_dir / '.gitkeep'
        assert gitkeep_path.exists()
        assert gitkeep_path.is_file()

    def test_ensure_gitkeep_preserves_existing(self, tmp_path):
        """Test that ensure_gitkeep doesn't overwrite existing .gitkeep."""
        test_dir = tmp_path / "test_subdir"
        test_dir.mkdir()
        
        gitkeep_path = test_dir / '.gitkeep'
        original_content = "# Existing content\n"
        gitkeep_path.write_text(original_content)
        
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert gitkeep_path.read_text() == original_content

    def test_ensure_gitkeep_nested_dirs(self, tmp_path):
        """Test that ensure_gitkeep creates nested directories."""
        test_dir = tmp_path / "level1" / "level2" / "level3"
        assert not test_dir.exists()
        
        result = ensure_gitkeep(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        
        # Check that .gitkeep exists in the deepest directory
        gitkeep_path = test_dir / '.gitkeep'
        assert gitkeep_path.exists()

    def test_ensure_gitkeep_content(self, tmp_path):
        """Test that .gitkeep file contains expected content."""
        test_dir = tmp_path / "test_subdir"
        
        ensure_gitkeep(str(test_dir))
        
        gitkeep_path = test_dir / '.gitkeep'
        content = gitkeep_path.read_text()
        
        assert '# This file ensures the directory is tracked by git' in content

if __name__ == '__main__':
    pytest.main([__file__, '-v'])