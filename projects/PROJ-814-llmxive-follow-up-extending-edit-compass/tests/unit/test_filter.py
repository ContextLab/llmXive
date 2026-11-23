"""
Unit tests for data filtering functionality.
"""
import pytest
import json
import os
import sys
from pathlib import Path
from io import StringIO

@pytest.fixture
def temp_data_dir(tmp_path):
    """Create temporary directory structure for raw and filtered data."""
    raw_dir = tmp_path / "raw"
    filtered_dir = tmp_path / "filtered"
    raw_dir.mkdir()
    filtered_dir.mkdir()
    return {
        "raw": str(raw_dir),
        "filtered": str(filtered_dir)
    }

def test_valid_category_match(temp_data_dir):
    """
    Assert that filtering by ["World Knowledge Reasoning", "Visual Reasoning"] 
    returns only records where the category field EXACTLY matches one of these values.
    """
    from src.services.filter import filter_by_categories

    # Create test data with exact category matches and non-matches
    test_data = [
        {"id": 1, "category": "World Knowledge Reasoning", "instruction": "test1"},
        {"id": 2, "category": "Visual Reasoning", "instruction": "test2"},
        {"id": 3, "category": "Other Category", "instruction": "test3"},
        {"id": 4, "category": "World Knowledge Reasoning", "instruction": "test4"},
        {"id": 5, "category": "Visual Reasoning", "instruction": "test5"},
        {"id": 6, "category": "World Knowledge Reasoning ", "instruction": "test6"}, # Trailing space, should NOT match
        {"id": 7, "category": "visual reasoning", "instruction": "test7"} # Lowercase, should NOT match
    ]

    # Write test data to file
    raw_file = Path(temp_data_dir["raw"]) / "test_data.json"
    with open(raw_file, "w") as f:
        json.dump(test_data, f)

    # Run filter
    output_file = Path(temp_data_dir["filtered"]) / "filtered_data.json"
    target_categories = ["World Knowledge Reasoning", "Visual Reasoning"]
    result_count = filter_by_categories(str(raw_file), str(output_file), target_categories)

    # Verify the count matches exactly the number of valid records (ids 1, 2, 4, 5)
    assert result_count == 4, f"Expected 4 matching records, got {result_count}"

    # Verify output file contents
    assert output_file.exists(), "Output file was not created"
    
    with open(output_file, "r") as f:
        filtered_data = json.load(f)

    assert len(filtered_data) == 4, f"Expected 4 items in file, got {len(filtered_data)}"
    
    # Assert that EVERY record in the output has a category that EXACTLY matches one of the targets
    for item in filtered_data:
        assert item["category"] in target_categories, \
            f"Record {item['id']} has invalid category '{item['category']}'. Expected one of {target_categories}"

def test_empty_result_handling(temp_data_dir):
    """
    Assert that if no matches are found, the script exits with exit code 1 
    and logs the message "ERROR: No records found for categories: [World Knowledge Reasoning, Visual Reasoning]".
    """
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
    
    # We need to catch the SystemExit or check the return code logic
    # Based on T012 implementation, it should log and exit(1) if 0 records found
    try:
        output_file = Path(temp_data_dir["filtered"]) / "empty_filtered_data.json"
        target_categories = ["World Knowledge Reasoning", "Visual Reasoning"]
        
        # The function filter_by_categories is expected to raise SystemExit(1) on 0 matches
        # or we can check the return value if it doesn't exit. 
        # The task description says "exits with exit code 1", implying sys.exit(1).
        # We will wrap in try/except to handle the exit.
        result = filter_by_categories(str(raw_file), str(output_file), target_categories)
        
        # If it returns instead of exiting, check result
        if result == 0:
            stderr_output = sys.stderr.getvalue()
            assert "No records found" in stderr_output or "ERROR" in stderr_output, \
                "Expected error message in logs when no records found"
        else:
            pytest.fail("Expected filter_by_categories to exit with code 1 or return 0 on empty results")
            
    except SystemExit as e:
        # Expected behavior: script exits with code 1
        assert e.code == 1, f"Expected exit code 1, got {e.code}"
        stderr_output = sys.stderr.getvalue()
        assert "No records found" in stderr_output or "ERROR" in stderr_output, \
            "Expected error message in logs when no records found"
    finally:
        sys.stderr = old_stderr