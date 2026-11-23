"""
Unit tests for the schema validation utilities.
"""
import json
import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest
import yaml

# Import the module under test
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from utils.schema_validator import (
    load_schema,
    validate_record,
    validate_dataset,
    validate_file,
    ensure_schema_exists,
    SCHEMA_PATH
)
from utils.logging import PipelineError

# Mock schema for testing
MOCK_SCHEMA = {
    "type": "object",
    "properties": {
        "task_id": {"type": "string"},
        "gc_content": {"type": "number", "minimum": 0.0, "maximum": 1.0},
        "entropy": {"type": "number", "minimum": 0.0},
        "kmer_entropy_3": {"type": "number"}
    },
    "required": ["task_id", "gc_content"],
    "additionalProperties": False
}


class TestLoadSchema:
    def test_load_schema_success(self, tmp_path):
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            yaml.dump(MOCK_SCHEMA, f)

        result = load_schema(schema_file)
        assert result == MOCK_SCHEMA

    def test_load_schema_not_found(self):
        with pytest.raises(PipelineError, match="Schema file not found"):
            load_schema(Path("/nonexistent/path/schema.yaml"))

    def test_load_schema_invalid_yaml(self, tmp_path):
        schema_file = tmp_path / "schema.yaml"
        with open(schema_file, "w") as f:
            f.write("invalid: yaml: content: [")

        with pytest.raises(PipelineError, match="Failed to parse schema YAML"):
            load_schema(schema_file)


class TestValidateRecord:
    def test_valid_record(self):
        valid_record = {
            "task_id": "task_001",
            "gc_content": 0.5,
            "entropy": 2.5,
            "kmer_entropy_3": 1.2
        }
        is_valid, errors = validate_record(valid_record, MOCK_SCHEMA)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_record_missing_required(self):
        invalid_record = {
            "gc_content": 0.5,
            "entropy": 2.5
        }
        is_valid, errors = validate_record(invalid_record, MOCK_SCHEMA)
        assert not is_valid
        assert len(errors) > 0
        assert any("task_id" in err for err in errors)

    def test_invalid_record_type_mismatch(self):
        invalid_record = {
            "task_id": 123,  # Should be string
            "gc_content": 0.5
        }
        is_valid, errors = validate_record(invalid_record, MOCK_SCHEMA)
        assert not is_valid
        assert len(errors) > 0

    def test_invalid_record_out_of_range(self):
        invalid_record = {
            "task_id": "task_001",
            "gc_content": 1.5  # > 1.0
        }
        is_valid, errors = validate_record(invalid_record, MOCK_SCHEMA)
        assert not is_valid
        assert len(errors) > 0
        assert any("maximum" in err for err in errors)

    def test_invalid_record_extra_property(self):
        invalid_record = {
            "task_id": "task_001",
            "gc_content": 0.5,
            "at_content": 0.3  # Not allowed by additionalProperties: False
        }
        is_valid, errors = validate_record(invalid_record, MOCK_SCHEMA)
        assert not is_valid
        assert len(errors) > 0
        assert any("at_content" in err for err in errors)


class TestValidateDataset:
    def test_valid_dataset(self):
        records = [
            {"task_id": "t1", "gc_content": 0.5, "entropy": 2.0},
            {"task_id": "t2", "gc_content": 0.6, "entropy": 2.1}
        ]
        is_valid, errors = validate_dataset(records, MOCK_SCHEMA)
        assert is_valid
        assert len(errors) == 0

    def test_invalid_dataset_fail_fast(self):
        records = [
            {"task_id": "t1", "gc_content": 0.5, "entropy": 2.0},
            {"task_id": "t2", "gc_content": 1.5},  # Invalid
            {"task_id": "t3", "gc_content": 0.7, "entropy": 2.2}
        ]
        is_valid, errors = validate_dataset(records, MOCK_SCHEMA, fail_fast=True)
        assert not is_valid
        # Should only report the first error
        assert len([e for e in errors if "t2" in e]) > 0

    def test_invalid_dataset_no_fail_fast(self):
        records = [
            {"task_id": "t1", "gc_content": 1.5},  # Invalid
            {"task_id": "t2", "gc_content": 1.6}   # Invalid
        ]
        is_valid, errors = validate_dataset(records, MOCK_SCHEMA, fail_fast=False)
        assert not is_valid
        assert len(errors) >= 2


class TestValidateFile:
    def test_validate_csv_file(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        with open(csv_file, "w") as f:
            f.write("task_id,gc_content,entropy\n")
            f.write("t1,0.5,2.0\n")
            f.write("t2,0.6,2.1\n")

        is_valid, errors = validate_file(csv_file, MOCK_SCHEMA)
        assert is_valid
        assert len(errors) == 0

    def test_validate_invalid_csv_file(self, tmp_path):
        csv_file = tmp_path / "data.csv"
        with open(csv_file, "w") as f:
            f.write("task_id,gc_content,entropy\n")
            f.write("t1,1.5,2.0\n")  # Invalid gc_content

        is_valid, errors = validate_file(csv_file, MOCK_SCHEMA)
        assert not is_valid
        assert len(errors) > 0

    def test_validate_json_file(self, tmp_path):
        json_file = tmp_path / "data.json"
        data = [
            {"task_id": "t1", "gc_content": 0.5, "entropy": 2.0},
            {"task_id": "t2", "gc_content": 0.6, "entropy": 2.1}
        ]
        with open(json_file, "w") as f:
            json.dump(data, f)

        is_valid, errors = validate_file(json_file, MOCK_SCHEMA)
        assert is_valid
        assert len(errors) == 0

    def test_validate_file_not_found(self):
        with pytest.raises(PipelineError, match="File not found"):
            validate_file(Path("/nonexistent/file.csv"))

    def test_validate_file_unsupported_extension(self, tmp_path):
        txt_file = tmp_path / "data.txt"
        txt_file.touch()
        with pytest.raises(PipelineError, match="Unsupported file extension"):
            validate_file(txt_file, MOCK_SCHEMA)


class TestEnsureSchemaExists:
    def test_schema_exists(self, tmp_path, monkeypatch):
        # Mock the SCHEMA_PATH to point to a temp file
        schema_file = tmp_path / "schema.yaml"
        schema_file.write_text("{}")
        monkeypatch.setattr("utils.schema_validator.SCHEMA_PATH", schema_file)

        assert ensure_schema_exists() is True

    def test_schema_not_exists(self, tmp_path, monkeypatch):
        non_existent = tmp_path / "non_existent.yaml"
        monkeypatch.setattr("utils.schema_validator.SCHEMA_PATH", non_existent)

        assert ensure_schema_exists() is False
