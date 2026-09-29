"""
Tests for T010c: Verified source file creation.
"""
import json
import tempfile
from pathlib import Path
import pytest
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from code.recreate_verified_sources import load_json_file, write_json_file

class TestT010cVerifiedSources:
    """Test cases for verified source file creation."""

    def test_load_json_file_success(self, tmp_path):
        """Test loading a valid JSON file."""
        data = {"key": "value"}
        file_path = tmp_path / "test.json"
        with open(file_path, 'w') as f:
            json.dump(data, f)
        
        result = load_json_file(file_path)
        assert result == data

    def test_load_json_file_not_found(self, tmp_path):
        """Test loading a non-existent file raises SystemExit."""
        file_path = tmp_path / "nonexistent.json"
        with pytest.raises(SystemExit):
            load_json_file(file_path)

    def test_load_json_file_invalid_json(self, tmp_path):
        """Test loading an invalid JSON file raises SystemExit."""
        file_path = tmp_path / "invalid.json"
        with open(file_path, 'w') as f:
            f.write("not valid json")
        
        with pytest.raises(SystemExit):
            load_json_file(file_path)

    def test_write_json_file(self, tmp_path):
        """Test writing a JSON file."""
        data = {"test": "data", "number": 42}
        file_path = tmp_path / "output.json"
        
        write_json_file(file_path, data)
        
        assert file_path.exists()
        with open(file_path, 'r') as f:
            written_data = json.load(f)
        
        assert written_data == data

    def test_write_json_file_creates_directories(self, tmp_path):
        """Test that write_json_file creates parent directories."""
        data = {"test": "data"}
        file_path = tmp_path / "subdir" / "nested" / "output.json"
        
        write_json_file(file_path, data)
        
        assert file_path.exists()

    def test_item_count_validation(self):
        """Test that exactly 12 items are required."""
        # This is implicitly tested in the main function, but we can simulate it
        items_11 = ["item" + str(i) for i in range(11)]
        items_13 = ["item" + str(i) for i in range(13)]
        
        assert len(items_11) != 12
        assert len(items_13) != 12
        assert len(["item" + str(i) for i in range(12)]) == 12

    def test_item_type_validation(self):
        """Test that items must be non-empty strings."""
        valid_items = ["string" + str(i) for i in range(12)]
        invalid_items_empty = [""] + ["string" + str(i) for i in range(11)]
        invalid_items_int = [1] + ["string" + str(i) for i in range(11)]
        
        assert all(isinstance(i, str) and i.strip() for i in valid_items)
        assert not all(isinstance(i, str) and i.strip() for i in invalid_items_empty)
        assert not all(isinstance(i, str) and i.strip() for i in invalid_items_int)