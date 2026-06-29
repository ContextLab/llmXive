"""
Unit tests for schema validators.

Tests SC-001 compliance for schema validation functionality.
"""
import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

from utils.validators import (
    SchemaValidator,
    ValidationError,
    get_validator,
    validate_dataset_schema
)


class TestSchemaValidator:
    """Test SchemaValidator class functionality."""

    @pytest.fixture
    def validator(self):
        """Create a SchemaValidator instance."""
        with patch('utils.validators.get_path') as mock_get_path:
            mock_get_path.return_value = Path('/fake/contracts')
            return SchemaValidator(contracts_dir=Path('/fake/contracts'))

    def test_init_sets_contracts_dir(self, validator):
        """Test that contracts directory is set correctly."""
        assert validator.contracts_dir == Path('/fake/contracts')

    def test_load_schema_file_not_found(self, validator):
        """Test FileNotFoundError when schema doesn't exist."""
        with pytest.raises(FileNotFoundError):
            validator.load_schema('nonexistent_schema')

    @patch('builtins.open')
    @patch('yaml.safe_load')
    def test_load_schema_success(self, mock_load, mock_open, validator):
        """Test successful schema loading."""
        mock_load.return_value = {'properties': {}, 'required': []}
        mock_open.return_value.__enter__.return_value = MagicMock()
        
        schema = validator.load_schema('test_schema')
        
        assert schema == {'properties': {}, 'required': []}
        mock_open.assert_called_once()

    def test_validate_type_string_success(self, validator):
        """Test string type validation passes."""
        assert validator.validate_type("hello", "string", "name") is True

    def test_validate_type_string_fail(self, validator):
        """Test string type validation fails for non-string."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_type(123, "string", "name")
        assert "string" in str(exc_info.value)

    def test_validate_type_integer_success(self, validator):
        """Test integer type validation passes."""
        assert validator.validate_type(42, "integer", "count") is True

    def test_validate_type_integer_fail(self, validator):
        """Test integer type validation fails for non-integer."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_type("42", "integer", "count")
        assert "integer" in str(exc_info.value)

    def test_validate_type_number_success_int(self, validator):
        """Test number type validation passes for int."""
        assert validator.validate_type(42, "number", "value") is True

    def test_validate_type_number_success_float(self, validator):
        """Test number type validation passes for float."""
        assert validator.validate_type(3.14, "number", "value") is True

    def test_validate_required_all_present(self, validator):
        """Test required validation passes when all fields present."""
        data = {"name": "test", "value": 123}
        validator.validate_required(data, ["name", "value"])  # Should not raise

    def test_validate_required_missing(self, validator):
        """Test required validation fails when fields missing."""
        data = {"name": "test"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_required(data, ["name", "value"])
        assert "value" in str(exc_info.value)

    def test_validate_field_constraints_min_pass(self, validator):
        """Test min constraint passes."""
        validator.validate_field_constraints(10, {"min": 5}, "count")

    def test_validate_field_constraints_min_fail(self, validator):
        """Test min constraint fails."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_constraints(3, {"min": 5}, "count")
        assert "below minimum" in str(exc_info.value)

    def test_validate_field_constraints_max_pass(self, validator):
        """Test max constraint passes."""
        validator.validate_field_constraints(5, {"max": 10}, "count")

    def test_validate_field_constraints_max_fail(self, validator):
        """Test max constraint fails."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_constraints(15, {"max": 10}, "count")
        assert "exceeds maximum" in str(exc_info.value)

    def test_validate_field_constraints_enum_pass(self, validator):
        """Test enum constraint passes."""
        validator.validate_field_constraints("closed", {"enum": ["open", "closed"]}, "state")

    def test_validate_field_constraints_enum_fail(self, validator):
        """Test enum constraint fails."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_constraints("unknown", {"enum": ["open", "closed"]}, "state")
        assert "not in allowed values" in str(exc_info.value)

    def test_validate_field_constraints_min_length_pass(self, validator):
        """Test min_length constraint passes."""
        validator.validate_field_constraints("hello", {"min_length": 3}, "name")

    def test_validate_field_constraints_min_length_fail(self, validator):
        """Test min_length constraint fails."""
        with pytest.raises(ValidationError) as exc_info:
            validator.validate_field_constraints("hi", {"min_length": 3}, "name")
        assert "below minimum" in str(exc_info.value)

    def test_validate_record_valid(self, validator):
        """Test valid record passes validation."""
        schema = {
            "required": ["id", "title"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"}
            }
        }
        record = {"id": 123, "title": "Test Issue"}
        errors = validator.validate_record(record, schema)
        assert errors == []

    def test_validate_record_missing_required(self, validator):
        """Test record with missing required field fails."""
        schema = {
            "required": ["id", "title"],
            "properties": {
                "id": {"type": "integer"},
                "title": {"type": "string"}
            }
        }
        record = {"id": 123}
        errors = validator.validate_record(record, schema)
        assert len(errors) == 1
        assert "Missing required fields" in errors[0]

    def test_validate_record_wrong_type(self, validator):
        """Test record with wrong type fails."""
        schema = {
            "required": ["id"],
            "properties": {
                "id": {"type": "integer"}
            }
        }
        record = {"id": "not_an_integer"}
        errors = validator.validate_record(record, schema)
        assert len(errors) == 1
        assert "expected 'integer'" in errors[0]

    def test_validate_record_constraint_violation(self, validator):
        """Test record with constraint violation fails."""
        schema = {
            "required": ["count"],
            "properties": {
                "count": {"type": "integer", "min": 0}
            }
        }
        record = {"count": -1}
        errors = validator.validate_record(record, schema)
        assert len(errors) == 1
        assert "below minimum" in errors[0]

    def test_get_validator_returns_instance(self):
        """Test get_validator factory function."""
        with patch('utils.validators.get_path') as mock_get_path:
            mock_get_path.return_value = Path('/fake/contracts')
            validator = get_validator()
            assert isinstance(validator, SchemaValidator)

    def test_ensure_contracts_dir_creates_directory(self):
        """Test ensure_contracts_dir creates directory if needed."""
        from utils.validators import ensure_contracts_dir
        
        with patch('utils.validators.get_path') as mock_get_path:
            mock_path = MagicMock()
            mock_get_path.return_value = mock_path
            
            ensure_contracts_dir()
            
            mock_path.mkdir.assert_called_once_with(parents=True, exist_ok=True)


class TestValidationErrors:
    """Test ValidationError exception class."""

    def test_validation_error_message(self):
        """Test ValidationError has correct message."""
        error = ValidationError("Test error message")
        assert str(error) == "Test error message"

    def test_validation_error_with_field(self):
        """Test ValidationError stores field name."""
        error = ValidationError("Test error", field="name")
        assert error.field == "name"

    def test_validation_error_with_value(self):
        """Test ValidationError stores value."""
        error = ValidationError("Test error", value="test_value")
        assert error.value == "test_value"
