"""
Unit tests for the filter service.
"""
import json
import pytest
import tempfile
from pathlib import Path
import sys
import os

# Add code directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from src.services.filter import filter_records, load_raw_data, save_filtered_data
from src.utils.logging import setup_logging

# Sample data for testing
SAMPLE_RAW_DATA = [
    {"id": 1, "category": "World Knowledge Reasoning", "instruction": "Test 1"},
    {"id": 2, "category": "Visual Reasoning", "instruction": "Test 2"},
    {"id": 3, "category": "Mathematical Reasoning", "instruction": "Test 3"},
    {"id": 4, "category": "World Knowledge Reasoning", "instruction": "Test 4"},
    {"id": 5, "category": "Other Category", "instruction": "Test 5"},
    {"id": 6, "category": "Visual Reasoning", "instruction": "Test 6"},
]

class TestFilterLogic:
    def test_category_filter_logic(self):
        """Assert that filtering by specific categories returns only matching records."""
        target_categories = ["World Knowledge Reasoning", "Visual Reasoning"]
        
        result = filter_records(SAMPLE_RAW_DATA, target_categories)
        
        # Should have 4 matching records (IDs 1, 2, 4, 6)
        assert len(result) == 4
        
        # Verify all returned records match the target categories
        for record in result:
            assert record["category"] in target_categories
        
        # Verify specific content
        categories_found = {r["category"] for r in result}
        assert categories_found == set(target_categories)

    def test_empty_result_handling(self):
        """Assert that filtering with non-matching categories returns an empty list."""
        target_categories = ["Non Existent Category"]
        
        result = filter_records(SAMPLE_RAW_DATA, target_categories)
        
        assert len(result) == 0
        assert result == []

    def test_missing_category_field(self):
        """Assert that records without a category field are excluded."""
        data_with_missing = [
            {"id": 1, "category": "World Knowledge Reasoning"},
            {"id": 2, "instruction": "Missing category"},
            {"id": 3, "category": None},
        ]
        
        result = filter_records(data_with_missing, ["World Knowledge Reasoning"])
        
        assert len(result) == 1
        assert result[0]["id"] == 1

class TestFilterIO:
    def test_save_and_load_filtered_data(self):
        """Assert that save and load functions work correctly together."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            tmp_path = Path(tmp_dir)
            input_file = tmp_path / "input.json"
            output_file = tmp_path / "output.json"
            
            # Save sample data
            with open(input_file, "w") as f:
                json.dump(SAMPLE_RAW_DATA, f)
            
            # Load raw data
            loaded_data = load_raw_data(input_file)
            assert len(loaded_data) == len(SAMPLE_RAW_DATA)
            
            # Filter data
            filtered = filter_records(loaded_data, ["World Knowledge Reasoning"])
            assert len(filtered) == 2
            
            # Save filtered data
            save_filtered_data(filtered, output_file)
            
            # Verify file exists
            assert output_file.exists()
            
            # Load and verify content
            with open(output_file, "r") as f:
                reloaded = json.load(f)
            
            assert len(reloaded) == 2
            assert all(r["category"] == "World Knowledge Reasoning" for r in reloaded)

    def test_empty_list_save(self):
        """Assert that saving an empty list creates a valid JSON file."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            output_file = Path(tmp_dir) / "empty.json"
            
            save_filtered_data([], output_file)
            
            assert output_file.exists()
            with open(output_file, "r") as f:
                data = json.load(f)
            assert data == []
            assert isinstance(data, list)