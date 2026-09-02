"""
Unit tests for setup_data_structure.py (Task T004).

Verifies that:
1. Required directories are created
2. State file is initialized with correct structure
3. Existing directories/files are not overwritten incorrectly
"""
import os
import json
import tempfile
import shutil
from pathlib import Path
import pytest

# Import the module functions (adjusting for relative import context in tests)
# Since the script is in code/, we import it as a module
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from setup_data_structure import ensure_directory, initialize_file


class TestEnsureDirectory:
    def test_creates_new_directory(self, tmp_path):
        """Test that a new directory is created."""
        new_dir = tmp_path / "new_dir"
        assert not new_dir.exists()
        ensure_directory(new_dir)
        assert new_dir.exists()
        assert new_dir.is_dir()

    def test_ignores_existing_directory(self, tmp_path):
        """Test that existing directory is left alone."""
        existing_dir = tmp_path / "existing"
        existing_dir.mkdir()
        ensure_directory(existing_dir)
        assert existing_dir.exists()
        assert existing_dir.is_dir()

    def test_raises_on_file_path(self, tmp_path):
        """Test that error is raised if path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("content")
        
        with pytest.raises(RuntimeError, match="not a directory"):
            ensure_directory(file_path)


class TestInitializeFile:
    def test_creates_new_file(self, tmp_path):
        """Test that a new file is created with initial content."""
        file_path = tmp_path / "test.json"
        content = {"key": "value", "nested": {"a": 1}}
        
        initialize_file(file_path, content)
        
        assert file_path.exists()
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == content

    def test_ignores_existing_valid_file(self, tmp_path):
        """Test that existing valid file is not overwritten."""
        file_path = tmp_path / "existing.json"
        original_content = {"original": True}
        file_path.write_text(json.dumps(original_content))
        
        new_content = {"new": True}
        initialize_file(file_path, new_content)
        
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == original_content

    def test_raises_on_invalid_json(self, tmp_path):
        """Test that error is raised if existing file is not valid JSON."""
        file_path = tmp_path / "invalid.json"
        file_path.write_text("not valid json {{{")
        
        with pytest.raises(RuntimeError, match="not valid JSON"):
            initialize_file(file_path, {"key": "value"})

    def test_creates_parent_directories(self, tmp_path):
        """Test that parent directories are created if missing."""
        file_path = tmp_path / "deep" / "nested" / "file.json"
        content = {"test": 123}
        
        initialize_file(file_path, content)
        
        assert file_path.exists()
        with open(file_path, 'r') as f:
            loaded = json.load(f)
        assert loaded == content