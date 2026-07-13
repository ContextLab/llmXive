"""
Contract test for dataset schema (T007).
Validates that the cleaned dataset adheres to the schema defined in specs/001-github-issue-resolution/contracts/dataset_schema.yaml.
"""
import pytest
import pandas as pd
import json
from pathlib import Path
import sys

# Add code to path if running from tests root
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from utils.validators import SchemaValidator, ValidationError, get_validator, load_schema

class TestDatasetSchema:
    """Tests for the dataset schema contract."""

    @pytest.fixture
    def valid_sample_record(self):
        return {
            "issue_id": 123456,
            "repository_id": 789012,
            "repository_name": "test-org/test-repo",
            "number": 42,
            "title": "Test Issue",
            "state": "closed",
            "created_at": "2023-01-01T00:00:00Z",
            "closed_at": "2023-01-02T00:00:00Z",
            "author": "testuser",
            "labels": json.dumps(["bug"]),
            "has_pull_request": False,
            "resolution_time_hours": 24.0
        }

    @pytest.fixture
    def invalid_record_missing_required(self):
        return {
            "issue_id": 123456,
            # Missing repository_id
            "repository_name": "test-org/test-repo",
            "number": 42,
            "state": "closed",
            "created_at": "2023-01-01T00:00:00Z",
            "closed_at": "2023-01-02T00:00:00Z",
            "author": "testuser",
            "labels": json.dumps([]),
            "has_pull_request": False,
            "resolution_time_hours": 24.0
        }

    @pytest.fixture
    def invalid_record_negative_time(self):
        return {
            "issue_id": 123456,
            "repository_id": 789012,
            "repository_name": "test-org/test-repo",
            "number": 42,
            "state": "closed",
            "created_at": "2023-01-02T00:00:00Z",
            "closed_at": "2023-01-01T00:00:00Z", # Closed before created
            "author": "testuser",
            "labels": json.dumps([]),
            "has_pull_request": False,
            "resolution_time_hours": -24.0
        }

    def test_schema_file_exists(self):
        """Verify the schema definition file exists."""
        schema_path = Path("specs/001-github-issue-resolution/contracts/dataset_schema.yaml")
        assert schema_path.exists(), "Dataset schema YAML file must exist"

    def test_valid_record_passes(self, valid_sample_record):
        """A valid record should pass schema validation."""
        validator = get_validator("dataset_schema")
        is_valid, msg = validator.validate(valid_sample_record)
        assert is_valid, f"Valid record failed validation: {msg}"

    def test_missing_required_field_fails(self, invalid_record_missing_required):
        """A record missing a required field should fail."""
        validator = get_validator("dataset_schema")
        is_valid, msg = validator.validate(invalid_record_missing_required)
        assert not is_valid
        assert "Missing required field" in msg

    def test_negative_resolution_time_fails(self, invalid_record_negative_time):
        """A record with negative resolution time should fail."""
        validator = get_validator("dataset_schema")
        is_valid, msg = validator.validate(invalid_record_negative_time)
        assert not is_valid
        assert "below minimum" in msg or "positive" in msg.lower() or "negative" in msg.lower()

    def test_repository_name_pattern(self):
        """Repository name must match owner/repo pattern."""
        invalid_record = {
            "issue_id": 1, "repository_id": 1, "repository_name": "invalid_name_no_slash",
            "number": 1, "state": "closed", "created_at": "2023-01-01T00:00:00Z",
            "closed_at": "2023-01-02T00:00:00Z", "author": "u", "labels": "[]",
            "has_pull_request": False, "resolution_time_hours": 1.0
        }
        validator = get_validator("dataset_schema")
        is_valid, msg = validator.validate(invalid_record)
        assert not is_valid
        assert "pattern" in msg.lower() or "format" in msg.lower() or "owner/repo" in msg.lower()

    def test_schema_loads_correctly(self):
        """Ensure the schema can be loaded and has expected structure."""
        schema = load_schema("dataset_schema")
        assert "fields" in schema
        assert "required" in schema
        assert "issue_id" in schema["required"]
        assert "resolution_time_hours" in schema["fields"]
        assert schema["fields"]["resolution_time_hours"]["type"] == "float"
        assert schema["fields"]["resolution_time_hours"]["minimum"] == 0
