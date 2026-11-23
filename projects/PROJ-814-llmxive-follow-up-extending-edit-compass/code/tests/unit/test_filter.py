"""
Unit tests for the filter service (T012).
"""
import json
import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add project root to path
project_root = Path(__file__).resolve().parents[2]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.services.filter import filter_by_categories, load_raw_data, save_filtered_data, TARGET_CATEGORIES

class TestFilterLogic:
    """Tests for the core filtering logic."""

    def test_category_filter_logic(self):
        """
        Assert that filtering by ["World Knowledge Reasoning", "Visual Reasoning"] 
        returns only matching records.
        """
        raw_data = [
            {"id": 1, "category": "World Knowledge Reasoning", "text": "A"},
            {"id": 2, "category": "Visual Reasoning", "text": "B"},
            {"id": 3, "category": "Math", "text": "C"},
            {"id": 4, "category": "Science", "text": "D"},
            {"id": 5, "category": "World Knowledge Reasoning", "text": "E"},
            # Edge case: list of categories
            {"id": 6, "category": ["Math", "Visual Reasoning"], "text": "F"},
            # Edge case: missing category
            {"id": 7, "text": "G"},
        ]

        result = filter_by_categories(raw_data, TARGET_CATEGORIES)

        # Expected IDs: 1, 2, 5, 6
        expected_ids = {1, 2, 5, 6}
        result_ids = {item["id"] for item in result}

        assert result_ids == expected_ids, f"Expected IDs {expected_ids}, got {result_ids}"
        assert len(result) == 4

    def test_empty_input(self):
        """Test filtering on empty list returns empty list."""
        result = filter_by_categories([], TARGET_CATEGORIES)
        assert result == []

    def test_no_matches(self):
        """Test filtering when no categories match."""
        raw_data = [
            {"id": 1, "category": "Math"},
            {"id": 2, "category": "Science"},
        ]
        result = filter_by_categories(raw_data, TARGET_CATEGORIES)
        assert result == []

    def test_case_sensitivity(self):
        """Test that category matching is case-sensitive (as per strict requirement)."""
        raw_data = [
            {"id": 1, "category": "world knowledge reasoning"}, # lowercase
            {"id": 2, "category": "World Knowledge Reasoning"}, # correct
        ]
        result = filter_by_categories(raw_data, TARGET_CATEGORIES)
        assert len(result) == 1
        assert result[0]["id"] == 2

class TestFilterIO:
    """Tests for file I/O operations."""

    def test_load_raw_json(self):
        """Test loading a valid JSON file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1}, {"id": 2}], f)
            temp_path = Path(f.name)

        try:
            data = load_raw_data(temp_path)
            assert len(data) == 2
            assert data[0]["id"] == 1
        finally:
            temp_path.unlink()

    def test_load_raw_jsonl(self):
        """Test loading a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"id": 1}\n')
            f.write('{"id": 2}\n')
            temp_path = Path(f.name)

        try:
            data = load_raw_data(temp_path)
            assert len(data) == 2
        finally:
            temp_path.unlink()

    def test_load_missing_file(self):
        """Test that loading a missing file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_raw_data(Path("non_existent_file.json"))

    def test_save_filtered_data(self):
        """Test saving filtered data to a file."""
        data = [{"id": 1, "category": "World Knowledge Reasoning"}]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_path = Path(tmp_dir) / "output.json"
            save_filtered_data(data, output_path)
            
            assert output_path.exists()
            with open(output_path, 'r') as f:
                saved_data = json.load(f)
            
            assert len(saved_data) == 1
            assert saved_data[0]["id"] == 1

    def test_save_creates_directory(self):
        """Test that saving creates the parent directory if it doesn't exist."""
        data = [{"id": 1}]
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            nested_path = Path(tmp_dir) / "subdir" / "output.json"
            save_filtered_data(data, nested_path)
            
            assert nested_path.exists()
            assert nested_path.parent.exists()