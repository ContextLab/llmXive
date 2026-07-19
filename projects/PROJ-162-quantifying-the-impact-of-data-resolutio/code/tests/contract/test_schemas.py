"""
Contract tests to verify JSON schema enforcement for data artifacts.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

from src.schema_validator import validate_json, validate_file, SchemaValidationError


class TestSchemaEnforcement:
    """Tests for schema validation logic."""

    def test_validate_json_valid_injection(self):
        """Test validation of a valid injection record against injection schema."""
        schema = {
            "type": "object",
            "properties": {
                "resolution": {"type": "integer"},
                "snr": {"type": "number"},
                "re_weighted_snr": {"type": "number"},
                "timestamp": {"type": "string"},
                "noise_segment_id": {"type": "string"}
            },
            "required": ["resolution", "snr", "re_weighted_snr", "timestamp", "noise_segment_id"]
        }
        
        valid_data = {
            "resolution": 4096,
            "snr": 12.5,
            "re_weighted_snr": 11.8,
            "timestamp": "2023-01-01T00:00:00Z",
            "noise_segment_id": "H1-12345"
        }
        
        # Should not raise
        result = validate_json(valid_data, schema)
        assert result is True

    def test_validate_json_missing_field(self):
        """Test validation fails when required field is missing."""
        schema = {
            "type": "object",
            "properties": {
                "id": {"type": "string"},
                "value": {"type": "number"}
            },
            "required": ["id", "value"]
        }
        
        invalid_data = {"id": "test"}
        
        with pytest.raises(SchemaValidationError):
            validate_json(invalid_data, schema)

    def test_validate_json_wrong_type(self):
        """Test validation fails when field type is incorrect."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"}
            }
        }
        
        invalid_data = {"count": "not_a_number"}
        
        with pytest.raises(SchemaValidationError):
            validate_json(invalid_data, schema)

    def test_validate_file_valid(self):
        """Test file validation with a valid JSON file."""
        schema = {
            "type": "object",
            "properties": {
                "key": {"type": "string"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"key": "value"}, f)
            temp_path = f.name
        
        try:
            result = validate_file(temp_path, schema)
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_validate_file_invalid(self):
        """Test file validation with an invalid JSON file."""
        schema = {
            "type": "object",
            "properties": {
                "count": {"type": "integer"}
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"count": "string"}, f)
            temp_path = f.name
        
        try:
            with pytest.raises(SchemaValidationError):
                validate_file(temp_path, schema)
        finally:
            os.unlink(temp_path)

    def test_validate_detection_metric_schema(self):
        """Test validation against the detection_metric schema structure."""
        schema = {
            "type": "object",
            "properties": {
                "p_value": {"type": "number"},
                "method": {"type": "string"},
                "detection_probability": {"type": "number"},
                "resolution": {"type": "integer"},
                "n_injections": {"type": "integer"}
            },
            "required": ["p_value", "method", "detection_probability", "resolution", "n_injections"]
        }
        
        valid_data = {
            "p_value": 0.001,
            "method": "welch_ttest",
            "detection_probability": 0.85,
            "resolution": 2048,
            "n_injections": 1000
        }
        
        assert validate_json(valid_data, schema) is True
