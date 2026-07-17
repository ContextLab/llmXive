"""
Tests for T015: Output Serialization
Verifies that the curation script produces a valid JSON file with required fields.
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Ensure code directory is in path
sys.path.insert(0, str(Path(__file__).parent.parent))

OUTPUT_PATH = "data/intermediate/explanations.json"
REQUIRED_FIELDS = ["snippet_id", "code", "complexity", "explanation", "token_count", "model_used", "status"]
VALID_COMPLEXITIES = ["low", "medium", "high"]
VALID_STATUSES = ["success", "skipped"]

@pytest.fixture
def output_file_exists():
    """Fixture to ensure the file exists before running tests."""
    if not os.path.exists(OUTPUT_PATH):
        pytest.skip(f"Output file {OUTPUT_PATH} not found. Run 01_data_curation.py first.")

def test_output_file_structure(output_file_exists):
    """Test that the output file is valid JSON and contains required fields."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    assert isinstance(data, list), "Output must be a list of records."
    assert len(data) >= 20, f"Expected at least 20 records, found {len(data)}."

    for record in data:
        assert isinstance(record, dict), "Each record must be a dictionary."
        for field in REQUIRED_FIELDS:
            assert field in record, f"Missing required field: {field}"

def test_complexity_labels_valid(output_file_exists):
    """Test that all complexity labels are valid."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for record in data:
        assert record["complexity"] in VALID_COMPLEXITIES, \
            f"Invalid complexity label: {record['complexity']}"

def test_token_counts_limit(output_file_exists):
    """Test that token counts are within the limit (<150)."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for record in data:
        if record["status"] == "success":
            # Allow some tolerance, but strict limit per spec
            assert record["token_count"] <= 150, \
                f"Token count {record['token_count']} exceeds limit of 150"

def test_no_null_values(output_file_exists):
    """Test that no critical fields are null."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for record in data:
        assert record["snippet_id"] is not None, "snippet_id cannot be null"
        assert record["code"] is not None, "code cannot be null"
        assert record["complexity"] is not None, "complexity cannot be null"
        # Explanation can be empty string if skipped, but not None
        assert record["explanation"] is not None, "explanation cannot be null"
        assert record["status"] is not None, "status cannot be null"
        assert record["model_used"] is not None, "model_used cannot be null"

def test_status_values(output_file_exists):
    """Test that status values are valid."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for record in data:
        assert record["status"] in VALID_STATUSES, \
            f"Invalid status: {record['status']}"

def test_explanation_length_reasonable(output_file_exists):
    """Test that explanations are not excessively long (sanity check)."""
    with open(OUTPUT_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)
    
    for record in data:
        if record["status"] == "success":
            # Just a sanity check that it's not a massive dump
            assert len(record["explanation"]) < 5000, \
                "Explanation seems unreasonably long"