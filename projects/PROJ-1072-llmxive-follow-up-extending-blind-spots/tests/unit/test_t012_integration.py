"""
Integration test for T012: Download and Filter logic.

This test verifies that the filtering logic correctly identifies target categories
and that the integrity check would fail if constraints were missing (simulated).
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the logic to test
# Note: We are testing the functions, not the CLI entry point directly
from utils.filtering_utils import filter_by_categories, is_valid_category
from utils.dataset_integrity import generate_integrity_report

class TestT012FilteringLogic:
    
    def test_is_valid_category(self):
        """Test that category matching works for target categories."""
        assert is_valid_category("Abstract Reasoning", {"Abstract Reasoning", "Object-Centric"}) is True
        assert is_valid_category("Object-Centric", {"Abstract Reasoning", "Object-Centric"}) is True
        assert is_valid_category("Other Category", {"Abstract Reasoning", "Object-Centric"}) is False
        assert is_valid_category(None, {"Abstract Reasoning", "Object-Centric"}) is False

    def test_filter_by_categories(self):
        """Test the filtering function with sample data."""
        mock_data = [
            {"id": "1", "category": "Abstract Reasoning", "constraint": "test"},
            {"id": "2", "category": "Object-Centric", "constraint": "test"},
            {"id": "3", "category": "Unrelated", "constraint": "test"},
            {"id": "4", "category": "Abstract Reasoning", "constraint": ""}, # Invalid constraint
        ]
        
        target_cats = {"Abstract Reasoning", "Object-Centric"}
        
        # Filter by category first
        filtered = filter_by_categories(mock_data, target_cats)
        
        assert len(filtered) == 3 # 1, 2, 4
        assert all(r["category"] in target_cats for r in filtered)

    def test_integrity_report_generation(self):
        """Test that the integrity report is generated correctly."""
        report = generate_integrity_report(
            total_records=100,
            filtered_count=50,
            missing_fields={"constraint": ["id_1", "id_2"]}
        )
        
        assert report["total_records"] == 100
        assert report["filtered_count"] == 50
        assert "constraint" in report["missing_fields"]
        assert len(report["missing_fields"]["constraint"]) == 2
        assert "id_1" in report["missing_fields"]["constraint"]