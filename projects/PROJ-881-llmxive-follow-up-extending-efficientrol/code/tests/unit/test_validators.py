"""
Unit tests for src.utils.validators module.
"""
import pytest
import json
import tempfile
from pathlib import Path
from typing import List, Dict, Any
from src.utils.validators import (
    validate_token_sequence,
    validate_validity_label,
    validate_entropy_profile,
    validate_merged_record,
    validate_json_schema,
    load_and_validate_jsonl
)

class TestTokenSequenceValidation:
    def test_valid_token_sequence(self):
        record = {
            "prompt_id": "test-123",
            "sequence": ["Hello", "world"],
            "task_type": "gsm8k",
            "sequence_length": 2
        }
        is_valid, error = validate_token_sequence(record)
        assert is_valid is True
        assert error is None

    def test_missing_prompt_id(self):
        record = {
            "sequence": ["Hello"],
            "task_type": "gsm8k",
            "sequence_length": 1
        }
        is_valid, error = validate_token_sequence(record)
        assert is_valid is False
        assert "Missing required field: prompt_id" in error

    def test_invalid_task_type(self):
        record = {
            "prompt_id": "test-123",
            "sequence": ["Hello"],
            "task_type": "invalid_type",
            "sequence_length": 1
        }
        is_valid, error = validate_token_sequence(record)
        assert is_valid is False
        assert "Invalid task_type" in error

    def test_length_mismatch(self):
        record = {
            "prompt_id": "test-123",
            "sequence": ["Hello", "World"],
            "task_type": "minigrid",
            "sequence_length": 1
        }
        is_valid, error = validate_token_sequence(record)
        assert is_valid is False
        assert "sequence_length does not match" in error


class TestValidityLabelValidation:
    def test_valid_validity_label(self):
        record = {
            "prompt_id": "test-123",
            "token_index": 0,
            "validity": True
        }
        is_valid, error = validate_validity_label(record)
        assert is_valid is True
        assert error is None

    def test_invalid_token_index(self):
        record = {
            "prompt_id": "test-123",
            "token_index": -1,
            "validity": True
        }
        is_valid, error = validate_validity_label(record)
        assert is_valid is False
        assert "token_index must be a non-negative integer" in error

    def test_validity_not_bool(self):
        record = {
            "prompt_id": "test-123",
            "token_index": 0,
            "validity": "yes"
        }
        is_valid, error = validate_validity_label(record)
        assert is_valid is False
        assert "validity must be a boolean" in error


class TestEntropyProfileValidation:
    def test_valid_entropy_profile(self):
        record = {
            "prompt_id": "test-123",
            "token_index": 0,
            "sequence_length": 10,
            "layer_entropy_map": {0: 1.5, 1: 1.2},
            "task_type": "gsm8k"
        }
        is_valid, error = validate_entropy_profile(record)
        assert is_valid is True
        assert error is None

    def test_missing_layer_entropy_map(self):
        record = {
            "prompt_id": "test-123",
            "token_index": 0,
            "sequence_length": 10,
            "task_type": "gsm8k"
        }
        is_valid, error = validate_entropy_profile(record)
        assert is_valid is False
        assert "Missing required field: layer_entropy_map" in error

    def test_negative_entropy_value(self):
        record = {
            "prompt_id": "test-123",
            "token_index": 0,
            "sequence_length": 10,
            "layer_entropy_map": {0: -1.0},
            "task_type": "minigrid"
        }
        is_valid, error = validate_entropy_profile(record)
        assert is_valid is False
        assert "entropy_value cannot be negative" in error

    def test_empty_layer_entropy_map(self):
        record = {
            "prompt_id": "test-123",
            "token_index": 0,
            "sequence_length": 10,
            "layer_entropy_map": {},
            "task_type": "gsm8k"
        }
        is_valid, error = validate_entropy_profile(record)
        assert is_valid is False
        assert "layer_entropy_map cannot be empty" in error


class TestMergedRecordValidation:
    def test_valid_merged_record(self):
        record = {
            "prompt_id": "test-123",
            "sequence": ["A", "B"],
            "task_type": "gsm8k",
            "sequence_length": 2,
            "token_index": 0,
            "validity": True,
            "layer_entropy_map": {0: 0.5}
        }
        is_valid, error = validate_merged_record(record)
        assert is_valid is True
        assert error is None

    def test_merged_missing_core(self):
        record = {
            "prompt_id": "test-123"
        }
        is_valid, error = validate_merged_record(record)
        assert is_valid is False
        assert "Merged record must contain either 'sequence' or 'layer_entropy_map'" in error


class TestJsonSchemaValidation:
    def test_dispatch_token_sequence(self):
        record = {
            "prompt_id": "test",
            "sequence": ["a"],
            "task_type": "gsm8k",
            "sequence_length": 1
        }
        is_valid, _ = validate_json_schema(record, "token_sequence")
        assert is_valid is True

    def test_dispatch_invalid_type(self):
        is_valid, error = validate_json_schema({}, "unknown_type")
        assert is_valid is False
        assert "Unknown schema type" in error


class TestLoadAndValidateJsonl:
    def test_load_valid_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"prompt_id": "1", "sequence": ["a"], "task_type": "gsm8k", "sequence_length": 1}) + "\n")
            f.write(json.dumps({"prompt_id": "2", "sequence": ["b"], "task_type": "minigrid", "sequence_length": 1}) + "\n")
            temp_path = f.name

        try:
            records = load_and_validate_jsonl(temp_path, "token_sequence")
            assert len(records) == 2
            assert records[0]["prompt_id"] == "1"
        finally:
            Path(temp_path).unlink()

    def test_load_invalid_jsonl(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write(json.dumps({"prompt_id": "1", "sequence": ["a"], "task_type": "invalid"}) + "\n")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_and_validate_jsonl(temp_path, "token_sequence")
            assert "Invalid task_type" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()

    def test_load_nonexistent_file(self):
        with pytest.raises(FileNotFoundError):
            load_and_validate_jsonl("/nonexistent/path/file.jsonl", "token_sequence")

    def test_load_empty_file(self):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write("")
            temp_path = f.name

        try:
            with pytest.raises(ValueError) as exc_info:
                load_and_validate_jsonl(temp_path, "token_sequence")
            assert "empty or contains no valid records" in str(exc_info.value)
        finally:
            Path(temp_path).unlink()