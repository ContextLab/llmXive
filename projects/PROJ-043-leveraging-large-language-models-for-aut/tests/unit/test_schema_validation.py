"""
Unit tests for schema validation module.
"""
import pytest
from unittest.mock import patch
from code.utils.schema_validation import (
    validate_config,
    validate_output,
    ConfigSchema,
    OutputSchema,
    MetricRecord,
    DeltaRecord,
    OutputRecord,
    OutputMetadata
)
from pydantic import ValidationError
import json

class TestConfigValidation:
    """Tests for configuration schema validation."""

    def test_valid_config(self):
        """Test that a valid configuration passes validation."""
        valid_data = {
            "HF_API_KEY": "test-key-123",
            "RANDOM_SEED": 42,
            "MAX_ATTEMPTS": 10,
            "MIN_VALID_FUNCTIONS": 50,
            "BATCH_SIZE": 5
        }
        result = validate_config(valid_data)
        assert result.HF_API_KEY == "test-key-123"
        assert result.RANDOM_SEED == 42

    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        invalid_data = {
            "RANDOM_SEED": 42,
            "MAX_ATTEMPTS": 10,
            "MIN_VALID_FUNCTIONS": 50,
            "BATCH_SIZE": 5
        }
        with pytest.raises(ValidationError):
            validate_config(invalid_data)

    def test_invalid_seed_type(self):
        """Test that non-integer seed raises ValidationError."""
        invalid_data = {
            "HF_API_KEY": "key",
            "RANDOM_SEED": "not-an-int",
            "MAX_ATTEMPTS": 10,
            "MIN_VALID_FUNCTIONS": 50,
            "BATCH_SIZE": 5
        }
        with pytest.raises(ValidationError):
            validate_config(invalid_data)

    def test_negative_seed(self):
        """Test that negative seed raises ValidationError."""
        invalid_data = {
            "HF_API_KEY": "key",
            "RANDOM_SEED": -1,
            "MAX_ATTEMPTS": 10,
            "MIN_VALID_FUNCTIONS": 50,
            "BATCH_SIZE": 5
        }
        with pytest.raises(ValidationError):
            validate_config(invalid_data)

class TestOutputValidation:
    """Tests for output schema validation."""

    def get_minimal_valid_record(self):
        """Helper to create a minimal valid record dict."""
        return {
            "function_hash": "abc123",
            "original_code": "def foo(): pass",
            "metrics": {
                "loc": 1,
                "max_nesting": 0,
                "param_count": 0,
                "has_docstring": False,
                "cyclomatic_complexity": 1.0,
                "pylint_score": 10.0
            },
            "status": "success"
        }

    def get_minimal_valid_output(self):
        """Helper to create a minimal valid output dict."""
        return {
            "metadata": {
                "version": "1.0.0",
                "timestamp": "2023-01-01T00:00:00Z",
                "source_dataset": "bigcode/the-stack-dedup"
            },
            "records": [self.get_minimal_valid_record()]
        }

    def test_valid_output(self):
        """Test that a valid output structure passes validation."""
        data = self.get_minimal_valid_output()
        result = validate_output(data)
        assert result.metadata.version == "1.0.0"
        assert len(result.records) == 1
        assert result.records[0].function_hash == "abc123"

    def test_empty_records_list(self):
        """Test that empty records list raises ValidationError."""
        data = self.get_minimal_valid_output()
        data["records"] = []
        with pytest.raises(ValidationError):
            validate_output(data)

    def test_invalid_status_value(self):
        """Test that invalid status value raises ValidationError."""
        record = self.get_minimal_valid_record()
        record["status"] = "invalid_status"
        data = self.get_minimal_valid_output()
        data["records"] = [record]
        with pytest.raises(ValidationError):
            validate_output(data)

    def test_missing_metrics_field(self):
        """Test that missing metrics field raises ValidationError."""
        record = self.get_minimal_valid_record()
        del record["metrics"]
        data = self.get_minimal_valid_output()
        data["records"] = [record]
        with pytest.raises(ValidationError):
            validate_output(data)

    def test_delta_validation(self):
        """Test that delta fields are validated correctly when present."""
        record = self.get_minimal_valid_record()
        record["deltas"] = {
            "complexity_delta": -1.0,
            "pylint_delta": 2.0,
            "maintainability_delta": 0.5
        }
        data = self.get_minimal_valid_output()
        data["records"] = [record]
        result = validate_output(data)
        assert result.records[0].deltas.complexity_delta == -1.0
        assert result.records[0].deltas.pylint_delta == 2.0