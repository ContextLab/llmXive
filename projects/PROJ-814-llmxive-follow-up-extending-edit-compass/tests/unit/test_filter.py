"""
Unit tests for data filtering functionality.
"""
import pytest
import json
import os
from pathlib import Path

def test_category_filter_logic(temp_data_dir):
    """Assert that filtering by ['World Knowledge Reasoning', 'Visual Reasoning'] returns only matching records."""
    from src.services.filter import filter_by_categories
    
    # Create test data
    test_data = [
        {"id": 1, "category": "World Knowledge Reasoning", "instruction": "test1"},
        {"id": 2, "category": "Visual Reasoning", "instruction": "test2"},
        {"id": 3, "category": "Other Category", "instruction": "test3"},
        {"id": 4, "category": "World Knowledge Reasoning", "instruction": "test4"}
    ]
    
    # Write test data to file
    raw_file = Path(temp_data_dir["raw"]) / "test_data.json"
    with open(raw_file, "w") as f:
        json.dump(test_data, f)
    
    # Run filter
    output_file = Path(temp_data_dir["filtered"]) / "filtered_data.json"
    result = filter_by_categories(str(raw_file), str(output_file), ["World Knowledge Reasoning", "Visual Reasoning"])
    
    # Verify results
    assert result == 2  # Only 2 records should match
    
    # Verify output file contents
    with open(output_file, "r") as f:
        filtered_data = json.load(f)
    
    assert len(filtered_data) == 2
    assert all(item["category"] in ["World Knowledge Reasoning", "Visual Reasoning"] for item in filtered_data)

def test_empty_result_handling(temp_data_dir):
    """Assert that if no matches are found, the script exits with a clear error message."""
    from src.services.filter import filter_by_categories
    import sys
    from io import StringIO
    
    # Create test data with no matching categories
    test_data = [
        {"id": 1, "category": "Other Category 1", "instruction": "test1"},
        {"id": 2, "category": "Other Category 2", "instruction": "test2"}
    ]
    
    # Write test data to file
    raw_file = Path(temp_data_dir["raw"]) / "empty_test_data.json"
    with open(raw_file, "w") as f:
        json.dump(test_data, f)
    
    # Capture stderr
    old_stderr = sys.stderr
    sys.stderr = StringIO()
    
    try:
        output_file = Path(temp_data_dir["filtered"]) / "empty_filtered_data.json"
        result = filter_by_categories(str(raw_file), str(output_file), ["Nonexistent Category"])
        
        # Should return 0 matches
        assert result == 0
        
        # Check if error message was logged
        stderr_output = sys.stderr.getvalue()
        assert "No records found" in stderr_output or "Warning" in stderr_output
    finally:
        sys.stderr = old_stderr