"""
Tests for ensure_raw_dir.py module.
Verifies that the data/raw/ directory is created and verified correctly.
"""
import os
import tempfile
import shutil
from pathlib import Path
import pytest

# Add the code directory to the path for imports
sys_path_backup = __import__('sys').path.copy()
try:
    code_dir = Path(__file__).parent.parent / "projects" / "PROJ-924-llmxive-follow-up-extending-agentdog-1-5" / "code"
    if str(code_dir) not in __import__('sys').path:
        __import__('sys').path.insert(0, str(code_dir))
    
    from ensure_raw_dir import ensure_raw_directory
finally:
    __import__('sys').path = sys_path_backup

class TestEnsureRawDirectory:
    """Test cases for ensure_raw_directory function."""

    def test_creates_directory_if_not_exists(self, tmp_path):
        """Test that the function creates the data/raw/ directory if it doesn't exist."""
        data_dir = tmp_path / "data"
        raw_dir = data_dir / "raw"
        
        assert not raw_dir.exists()
        
        result = ensure_raw_directory(tmp_path)
        
        assert result is True
        assert raw_dir.exists()
        assert raw_dir.is_dir()

    def test_returns_true_if_directory_exists(self, tmp_path):
        """Test that the function returns True if the directory already exists."""
        raw_dir = tmp_path / "data" / "raw"
        raw_dir.mkdir(parents=True)
        
        result = ensure_raw_directory(tmp_path)
        
        assert result is True
        assert raw_dir.exists()

    def test_creates_parent_directories(self, tmp_path):
        """Test that the function creates parent directories if they don't exist."""
        # Don't create 'data' directory, only ensure 'raw' is created
        assert not (tmp_path / "data").exists()
        
        result = ensure_raw_directory(tmp_path)
        
        assert result is True
        assert (tmp_path / "data" / "raw").exists()

    def test_creates_multiple_levels(self, tmp_path):
        """Test that the function creates multiple levels of parent directories."""
        # Ensure no parent exists
        assert not (tmp_path / "data").exists()
        
        result = ensure_raw_directory(tmp_path)
        
        assert result is True
        assert (tmp_path / "data" / "raw").exists()

    def test_returns_false_on_permission_error(self, tmp_path):
        """Test that the function returns False on permission errors."""
        # Create a read-only directory to simulate permission issues
        data_dir = tmp_path / "data"
        data_dir.mkdir()
        data_dir.chmod(0o444)  # Read-only
        
        try:
            result = ensure_raw_directory(tmp_path)
            # On some systems, root can still write, so we might get True
            # But generally, we expect False or an exception handled internally
            # The function catches exceptions and returns False
            assert result is False
        finally:
            # Restore permissions for cleanup
            data_dir.chmod(0o755)

if __name__ == "__main__":
    pytest.main([__file__, "-v"])