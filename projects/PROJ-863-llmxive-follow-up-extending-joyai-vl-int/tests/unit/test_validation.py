"""
Unit tests for validation utilities.

Tests schema validation functionality including:
- Type checking
- Required field validation
- Value constraints (min/max, length, pattern, enum)
- Nested object validation
- JSONL validation
"""

import pytest
import json
import tempfile
from pathlib import Path

from src.utils.validation import (
    validate_schema,
    validate_jsonl_schema,
    ValidationError,
    SYNTHETIC_FRAME_SCHEMA,
    INTERNAL_STATE_SCHEMA
)


class TestValidateSchema:
    """Tests for the validate_schema function."""
    
    def test_valid_data(self):
        """Test that valid data passes validation."""
        schema = {
            "name": {"type": "string"},
            "age": {"type": "integer", "minimum": 0}
        }
        data = {"name": "Alice", "age": 30}
        
        # Should not raise
        validate_schema(data, schema)
    
    def test_missing_required_field(self):
        """Test that missing required fields raise ValidationError."""
        schema = {"name": {"type": "string"}}
        data = {}
        required = ["name"]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema, required_fields=required)
        
        assert "Missing required fields: name" in str(exc_info.value)
    
    def test_wrong_type(self):
        """Test that type mismatches raise ValidationError."""
        schema = {"count": {"type": "integer"}}
        data = {"count": "not a number"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "expected type 'integer', got 'str'" in str(exc_info.value).lower()
    
    def test_minimum_violation(self):
        """Test that values below minimum raise ValidationError."""
        schema = {"value": {"type": "integer", "minimum": 0}}
        data = {"value": -5}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "below minimum" in str(exc_info.value).lower()
    
    def test_maximum_violation(self):
        """Test that values above maximum raise ValidationError."""
        schema = {"value": {"type": "number", "maximum": 100}}
        data = {"value": 150.5}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "above maximum" in str(exc_info.value).lower()
    
    def test_string_min_length(self):
        """Test that strings below min_length raise ValidationError."""
        schema = {"code": {"type": "string", "min_length": 3}}
        data = {"code": "ab"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "below minimum" in str(exc_info.value).lower()
    
    def test_string_max_length(self):
        """Test that strings exceeding max_length raise ValidationError."""
        schema = {"code": {"type": "string", "max_length": 5}}
        data = {"code": "toolong"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "exceeds maximum" in str(exc_info.value).lower()
    
    def test_pattern_mismatch(self):
        """Test that values not matching pattern raise ValidationError."""
        schema = {"email": {"type": "string", "pattern": r"^[\w\.-]+@[\w\.-]+\.\w+$"}}
        data = {"email": "not-an-email"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "does not match pattern" in str(exc_info.value).lower()
    
    def test_enum_violation(self):
        """Test that values not in enum raise ValidationError."""
        schema = {"status": {"type": "string", "enum": ["active", "inactive", "pending"]}}
        data = {"status": "unknown"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "not in allowed values" in str(exc_info.value).lower()
    
    def test_strict_mode_extra_field(self):
        """Test that strict mode rejects extra fields."""
        schema = {"name": {"type": "string"}}
        data = {"name": "Alice", "extra": "field"}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema, strict=True)
        
        assert "Unexpected field" in str(exc_info.value)
    
    def test_strict_mode_passes_known_fields(self):
        """Test that strict mode allows only defined fields."""
        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        data = {"name": "Alice", "age": 30}
        
        # Should not raise
        validate_schema(data, schema, strict=True)
    
    def test_nested_object_validation(self):
        """Test validation of nested objects."""
        schema = {
            "user": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "age": {"type": "integer", "minimum": 0}
                }
            }
        }
        data = {"user": {"name": "Bob", "age": -5}}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "below minimum" in str(exc_info.value).lower()
    
    def test_array_validation(self):
        """Test validation of array items."""
        schema = {
            "scores": {
                "type": "array",
                "items": {"type": "integer", "minimum": 0, "maximum": 100}
            }
        }
        data = {"scores": [10, 50, -5]}
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "below minimum" in str(exc_info.value).lower()
    
    def test_not_object_type(self):
        """Test that non-dict data raises ValidationError."""
        schema = {"name": {"type": "string"}}
        data = ["not", "a", "dict"]
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, schema)
        
        assert "Expected object" in str(exc_info.value)
    
    def test_synthetic_frame_schema_valid(self):
        """Test valid synthetic frame data."""
        data = {
            "frame_id": "frame_001",
            "timestamp": 123.456,
            "video_id": "video_001",
            "width": 1920,
            "height": 1080,
            "label": "critical",
            "confidence": 0.95
        }
        
        # Should not raise
        validate_schema(data, SYNTHETIC_FRAME_SCHEMA)
    
    def test_synthetic_frame_schema_invalid_label(self):
        """Test synthetic frame with invalid label."""
        data = {
            "frame_id": "frame_001",
            "timestamp": 123.456,
            "video_id": "video_001",
            "width": 1920,
            "height": 1080,
            "label": "invalid_label",
            "confidence": 0.95
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, SYNTHETIC_FRAME_SCHEMA)
        
        assert "not in allowed values" in str(exc_info.value).lower()
    
    def test_synthetic_frame_schema_confidence_out_of_range(self):
        """Test synthetic frame with confidence out of range."""
        data = {
            "frame_id": "frame_001",
            "timestamp": 123.456,
            "video_id": "video_001",
            "width": 1920,
            "height": 1080,
            "label": "critical",
            "confidence": 1.5
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_schema(data, SYNTHETIC_FRAME_SCHEMA)
        
        assert "above maximum" in str(exc_info.value).lower()

class TestValidateJsonlSchema:
    """Tests for the validate_jsonl_schema function."""
    
    def test_valid_jsonl_file(self):
        """Test validation of a valid JSONL file."""
        schema = {"name": {"type": "string"}, "age": {"type": "integer"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"name": "Alice", "age": 30}\n')
            f.write('{"name": "Bob", "age": 25}\n')
            temp_path = f.name
        
        try:
            stats = validate_jsonl_schema(temp_path, schema)
            assert stats["total_lines"] == 2
            assert stats["valid_lines"] == 2
            assert stats["invalid_lines"] == 0
            assert len(stats["errors"]) == 0
        finally:
            Path(temp_path).unlink()
    
    def test_invalid_jsonl_file(self):
        """Test validation of a JSONL file with errors."""
        schema = {"name": {"type": "string"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"name": "Alice"}\n')  # Valid
            f.write('{"name": 123}\n')       # Invalid type
            f.write('not json\n')            # Invalid JSON
            f.write('{"name": "Charlie"}\n') # Valid
            temp_path = f.name
        
        try:
            stats = validate_jsonl_schema(temp_path, schema)
            assert stats["total_lines"] == 4
            assert stats["valid_lines"] == 2
            assert stats["invalid_lines"] == 2
            assert len(stats["errors"]) == 2
            
            # Check error messages
            errors = [e["error"] for e in stats["errors"]]
            assert any("expected type 'string'" in err for err in errors)
            assert any("JSON decode error" in err for err in errors)
        finally:
            Path(temp_path).unlink()
    
    def test_nonexistent_file(self):
        """Test that non-existent file raises FileNotFoundError."""
        schema = {"name": {"type": "string"}}
        
        with pytest.raises(FileNotFoundError):
            validate_jsonl_schema("/nonexistent/path/file.jsonl", schema)
    
    def test_max_lines_limit(self):
        """Test that max_lines parameter limits validation."""
        schema = {"value": {"type": "integer"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            for i in range(10):
                f.write(f'{{"value": {i}}}\n')
            temp_path = f.name
        
        try:
            stats = validate_jsonl_schema(temp_path, schema, max_lines=3)
            assert stats["total_lines"] == 3
            assert stats["valid_lines"] == 3
        finally:
            Path(temp_path).unlink()
    
    def test_empty_lines_ignored(self):
        """Test that empty lines in JSONL are ignored."""
        schema = {"value": {"type": "integer"}}
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"value": 1}\n')
            f.write('\n')  # Empty line
            f.write('{"value": 2}\n')
            f.write('\n')  # Another empty line
            temp_path = f.name
        
        try:
            stats = validate_jsonl_schema(temp_path, schema)
            assert stats["total_lines"] == 4  # Counts empty lines
            assert stats["valid_lines"] == 2
            assert stats["invalid_lines"] == 0
        finally:
            Path(temp_path).unlink()
    
    def test_required_fields_in_jsonl(self):
        """Test required fields validation in JSONL."""
        schema = {"name": {"type": "string"}}
        required = ["name", "age"]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False) as f:
            f.write('{"name": "Alice"}\n')  # Missing age
            f.write('{"name": "Bob", "age": 25}\n')
            temp_path = f.name
        
        try:
            stats = validate_jsonl_schema(temp_path, schema, required_fields=required)
            assert stats["invalid_lines"] == 1
            assert stats["valid_lines"] == 1
        finally:
            Path(temp_path).unlink()

class TestValidationError:
    """Tests for the ValidationError exception."""
    
    def test_error_message_with_path(self):
        """Test error message includes path when provided."""
        error = ValidationError("Test error", path="data/test.jsonl")
        assert "in data/test.jsonl" in str(error)
    
    def test_error_message_with_line(self):
        """Test error message includes line number when provided."""
        error = ValidationError("Test error", line=42)
        assert "at line 42" in str(error)
    
    def test_error_message_with_path_and_line(self):
        """Test error message includes both path and line number."""
        error = ValidationError("Test error", path="data/test.jsonl", line=42)
        assert "in data/test.jsonl" in str(error)
        assert "at line 42" in str(error)
    
    def test_error_message_without_location(self):
        """Test error message without path or line."""
        error = ValidationError("Test error")
        assert str(error) == "Validation Error: Test error"