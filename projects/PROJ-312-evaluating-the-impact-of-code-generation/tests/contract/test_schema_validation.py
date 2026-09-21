"""
Contract tests for schema validation.
Tests T011 and T018a schema validation logic.
"""
import json
import os
import pytest
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils import validate_json_schema

@pytest.fixture
def valid_pr_data():
    return {
        "pr_id": "PR-123",
        "repo_name": "test/repo",
        "created_at": "2023-01-01T00:00:00Z",
        "merged_at": "2023-01-02T00:00:00Z",
        "labels": ["bug"],
        "commit_messages": ["Fix bug"],
        "turnaround_hours": 24.0
    }

@pytest.fixture
def invalid_pr_data_missing_field():
    return {
        "pr_id": "PR-124",
        "repo_name": "test/repo",
        # Missing turnaround_hours
        "created_at": "2023-01-01T00:00:00Z",
    }

@pytest.fixture
def schema_path():
    return "contracts/pull_request.schema.yaml"

def test_valid_pr_validates(schema_path, valid_pr_data):
    """Test that valid PR data passes schema validation."""
    assert validate_json_schema(valid_pr_data, schema_path) is True

def test_invalid_pr_fails(schema_path, invalid_pr_data_missing_field):
    """Test that PR data missing required fields fails validation."""
    assert validate_json_schema(invalid_pr_data_missing_field, schema_path) is False

def test_schema_file_exists(schema_path):
    """Test that the schema file exists."""
    assert os.path.exists(schema_path), f"Schema file not found: {schema_path}"

def test_pr_data_json_exists():
    """Test that the raw data file exists (T018a output)."""
    output_path = "data/raw/pr_data.json"
    assert os.path.exists(output_path), f"Output file not found: {output_path}"
    
    # Verify it loads as valid JSON
    with open(output_path, 'r') as f:
        data = json.load(f)
        assert isinstance(data, list)
        assert len(data) > 0