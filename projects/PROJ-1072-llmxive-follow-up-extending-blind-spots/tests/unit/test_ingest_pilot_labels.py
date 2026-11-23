"""
Unit tests for code/ingest_pilot_labels.py
"""

import json
import os
import tempfile
from pathlib import Path
import pytest
from unittest.mock import patch, MagicMock

# Import the functions to test
# We need to handle the import path carefully
try:
    from code.ingest_pilot_labels import validate_schema, ingest_labels, REQUIRED_FIELDS
except ImportError:
    # Fallback if running from project root without code in path
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from code.ingest_pilot_labels import validate_schema, ingest_labels, REQUIRED_FIELDS


class TestValidateSchema:
    """Tests for the validate_schema function."""

    def test_valid_record(self):
        """Test a valid record passes validation."""
        record = {
            "task_id": "test-123",
            "constraint_mention": "Yes",
            "task_outcome": "Correct"
        }
        result = validate_schema(record, 1)
        assert result is None

    def test_missing_field(self):
        """Test validation fails if a required field is missing."""
        record = {
            "task_id": "test-123",
            "constraint_mention": "Yes"
            # Missing task_outcome
        }
        result = validate_schema(record, 1)
        assert result is not None
        assert "Missing required fields" in result
        assert "task_outcome" in result

    def test_invalid_constraint_mention(self):
        """Test validation fails for invalid constraint_mention value."""
        record = {
            "task_id": "test-123",
            "constraint_mention": "Maybe",
            "task_outcome": "Correct"
        }
        result = validate_schema(record, 1)
        assert result is not None
        assert "Invalid 'constraint_mention' value" in result

    def test_invalid_task_outcome(self):
        """Test validation fails for invalid task_outcome value."""
        record = {
            "task_id": "test-123",
            "constraint_mention": "Yes",
            "task_outcome": "Unknown"
        }
        result = validate_schema(record, 1)
        assert result is not None
        assert "Invalid 'task_outcome' value" in result

    def test_empty_task_id(self):
        """Test validation fails for empty task_id."""
        record = {
            "task_id": "",
            "constraint_mention": "Yes",
            "task_outcome": "Correct"
        }
        result = validate_schema(record, 1)
        assert result is not None
        assert "Invalid 'task_id'" in result

    def test_non_string_task_id(self):
        """Test validation fails for non-string task_id."""
        record = {
            "task_id": 12345,
            "constraint_mention": "Yes",
            "task_outcome": "Correct"
        }
        result = validate_schema(record, 1)
        assert result is not None
        assert "Invalid 'task_id'" in result


class TestIngestLabels:
    """Tests for the ingest_labels function."""

    def test_file_not_found(self):
        """Test that SystemExit is raised if file is missing."""
        # Use a path that definitely doesn't exist
        non_existent_path = Path("/tmp/definitely_does_not_exist_12345.jsonl")
        
        with pytest.raises(SystemExit) as exc_info:
            ingest_labels(non_existent_path)
        
        assert exc_info.value.code == 1

    def test_valid_jsonl_file(self):
        """Test ingestion of a valid JSONL file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"task_id": "1", "constraint_mention": "Yes", "task_outcome": "Correct"}\n')
            f.write('{"task_id": "2", "constraint_mention": "No", "task_outcome": "Incorrect"}\n')
            temp_path = Path(f.name)

        try:
            labels = ingest_labels(temp_path)
            assert len(labels) == 2
            assert labels[0]["task_id"] == "1"
            assert "ingested_at" in labels[0]
        finally:
            os.unlink(temp_path)

    def test_invalid_json_line(self):
        """Test that invalid JSON lines are reported but don't crash ingestion."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"task_id": "1", "constraint_mention": "Yes", "task_outcome": "Correct"}\n')
            f.write('{"invalid json}\n')
            f.write('{"task_id": "2", "constraint_mention": "No", "task_outcome": "Incorrect"}\n')
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                ingest_labels(temp_path)
            assert "Validation failed" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_mixed_valid_invalid(self):
        """Test file with mix of valid and invalid records."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"task_id": "1", "constraint_mention": "Yes", "task_outcome": "Correct"}\n')
            f.write('{"task_id": "2", "constraint_mention": "Invalid", "task_outcome": "Incorrect"}\n')
            temp_path = Path(f.name)

        try:
            with pytest.raises(ValueError) as exc_info:
                ingest_labels(temp_path)
            # Should fail due to the second record
            assert "Validation failed" in str(exc_info.value)
        finally:
            os.unlink(temp_path)

    def test_empty_file(self):
        """Test ingestion of an empty file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            temp_path = Path(f.name)

        try:
            labels = ingest_labels(temp_path)
            assert len(labels) == 0
        finally:
            os.unlink(temp_path)

    def test_empty_lines_ignored(self):
        """Test that empty lines in the file are ignored."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('\n')
            f.write('{"task_id": "1", "constraint_mention": "Yes", "task_outcome": "Correct"}\n')
            f.write('\n')
            f.write('{"task_id": "2", "constraint_mention": "No", "task_outcome": "Incorrect"}\n')
            f.write('\n')
            temp_path = Path(f.name)

        try:
            labels = ingest_labels(temp_path)
            assert len(labels) == 2
        finally:
            os.unlink(temp_path)