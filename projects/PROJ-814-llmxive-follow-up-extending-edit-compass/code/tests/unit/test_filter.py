import json
import pytest
import tempfile
from pathlib import Path
import sys
import os

# Ensure src is in path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "code"))

from src.services.filter import filter_by_category, load_json_file, save_filtered_data, TARGET_CATEGORIES

class TestFilterLogic:
    def test_category_filter_logic(self):
        """Assert that filtering by target categories returns only matching records."""
        data = [
            {"category": "World Knowledge Reasoning", "id": 1},
            {"category": "Visual Reasoning", "id": 2},
            {"category": "Other Category", "id": 3},
            {"category": "World Knowledge Reasoning", "id": 4},
            {"category": "Visual Reasoning", "id": 5},
        ]
        
        result = filter_by_category(data, TARGET_CATEGORIES)
        
        assert len(result) == 4
        for item in result:
            assert item["category"] in TARGET_CATEGORIES
        
        # Check specific IDs
        ids = [item["id"] for item in result]
        assert 1 in ids
        assert 2 in ids
        assert 4 in ids
        assert 5 in ids
        assert 3 not in ids

    def test_empty_result_handling(self):
        """Assert that if no matches are found, a ValueError is raised."""
        data = [
            {"category": "Other Category", "id": 1},
            {"category": "Another Category", "id": 2},
        ]
        
        with pytest.raises(ValueError) as exc_info:
            filter_by_category(data, TARGET_CATEGORIES)
        
        assert "No records found matching categories" in str(exc_info.value)

    def test_mixed_valid_invalid_records(self):
        """Test handling of non-dict records in the list."""
        data = [
            {"category": "World Knowledge Reasoning", "id": 1},
            "not a dict",
            {"category": "Visual Reasoning", "id": 2},
            None,
            {"category": "Other", "id": 3},
        ]
        
        # Should filter out non-dicts and 'Other' category
        result = filter_by_category(data, TARGET_CATEGORIES)
        
        assert len(result) == 2
        assert result[0]["id"] == 1
        assert result[1]["id"] == 2

class TestFilterIO:
    def test_load_json_file_valid(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}], f)
            temp_path = Path(f.name)
        
        try:
            data = load_json_file(temp_path)
            assert len(data) == 2
            assert data[0]["id"] == 1
        finally:
            temp_path.unlink()

    def test_load_json_file_not_found(self):
        """Test loading a non-existent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_json_file(Path("/non/existent/path/file.json"))

    def test_load_json_file_invalid_json(self):
        """Test loading a file with invalid JSON raises JSONDecodeError."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write("{ invalid json }")
            temp_path = Path(f.name)
        
        try:
            with pytest.raises(json.JSONDecodeError):
                load_json_file(temp_path)
        finally:
            temp_path.unlink()

    def test_save_filtered_data(self):
        """Test saving filtered data to a file."""
        data = [{"id": 1, "category": "World Knowledge Reasoning"}]
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            save_filtered_data(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 1
            assert saved_data[0]["id"] == 1

    def test_save_filtered_data_empty_list(self):
        """Test saving an empty list."""
        data = []
        
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "output.json"
            save_filtered_data(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 0