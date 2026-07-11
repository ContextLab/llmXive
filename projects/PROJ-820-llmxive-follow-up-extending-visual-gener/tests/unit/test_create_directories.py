import os
import tempfile
import pytest
from pathlib import Path
import sys

# Add the code directory to the path so we can import the module
# Assuming this test runs from the project root or we adjust the path
code_path = Path(__file__).parent.parent.parent / "code"
if str(code_path) not in sys.path:
    sys.path.insert(0, str(code_path))

from setup.create_directories import create_directory

class TestCreateDirectory:
    def test_creates_new_directory(self, tmp_path):
        """Test that create_directory successfully creates a new directory."""
        test_dir = tmp_path / "new_test_dir"
        assert not test_dir.exists()
        
        result = create_directory(str(test_dir))
        
        assert result is True
        assert test_dir.exists()
        assert test_dir.is_dir()

    def test_exists_directory_returns_true(self, tmp_path):
        """Test that create_directory returns True if directory already exists."""
        test_dir = tmp_path / "existing_dir"
        test_dir.mkdir()
        assert test_dir.exists()
        
        result = create_directory(str(test_dir))
        
        assert result is True
        assert test_dir.exists()

    def test_creates_nested_directories(self, tmp_path):
        """Test that create_directory creates parent directories if needed."""
        nested_dir = tmp_path / "level1" / "level2" / "level3"
        assert not nested_dir.exists()
        
        result = create_directory(str(nested_dir))
        
        assert result is True
        assert nested_dir.exists()
        assert nested_dir.is_dir()

    def test_invalid_path_returns_false(self, tmp_path):
        """Test behavior with an invalid path (e.g., file exists where dir is expected)."""
        file_path = tmp_path / "a_file.txt"
        file_path.write_text("content")
        
        # Try to create a directory where a file exists
        result = create_directory(str(file_path))
        
        # The function should return False because it can't create a dir over a file
        # or it might succeed if it just checks existence, but logically it should fail
        # Let's check the implementation: it tries mkdir, which fails if file exists.
        # So result should be False.
        assert result is False

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
