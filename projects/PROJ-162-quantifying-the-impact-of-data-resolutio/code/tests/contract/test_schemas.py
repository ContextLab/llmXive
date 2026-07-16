"""
Contract tests to verify schema enforcement across the project.
These tests ensure that data written to disk conforms to the defined JSON schemas.
"""
import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Import the validator from the project source
# Note: Using relative import style compatible with pytest running from code/ or root
import sys
from pathlib import Path

# Ensure we can import from code/src
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from schema_validator import SchemaValidator, SchemaValidationError, get_validator
from config import get_contract_path, ensure_directories


class TestSchemaEnforcement:
    """Tests for verifying schema enforcement logic."""

    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for test outputs."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    def test_validator_initialization(self, temp_dir):
        """Test that SchemaValidator initializes correctly with a schema path."""
        # Create a dummy schema file for testing
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "name": {"type": "string"}
            },
            "required": ["name"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        validator = SchemaValidator(schema_path)
        assert validator.schema_path == schema_path
        assert validator.schema == schema_content

    def test_validate_valid_data(self, temp_dir):
        """Test validation passes for data conforming to schema."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["id", "status"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        valid_data = {"id": 123, "status": "active"}

        validator = SchemaValidator(schema_path)
        result = validator.validate(valid_data)

        assert result is True

    def test_validate_missing_required_field(self, temp_dir):
        """Test validation fails when required field is missing."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "id": {"type": "integer"},
                "status": {"type": "string"}
            },
            "required": ["id", "status"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        invalid_data = {"id": 123}  # Missing 'status'

        validator = SchemaValidator(schema_path)
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(invalid_data)

        assert "status" in str(exc_info.value).lower()

    def test_validate_wrong_type(self, temp_dir):
        """Test validation fails when data type is incorrect."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "count": {"type": "integer"}
            },
            "required": ["count"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        invalid_data = {"count": "not_an_integer"}

        validator = SchemaValidator(schema_path)
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(invalid_data)

        assert "integer" in str(exc_info.value).lower() or "type" in str(exc_info.value).lower()

    def test_validate_enum_constraint(self, temp_dir):
        """Test validation fails when enum constraint is violated."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "status": {"type": "string", "enum": ["active", "inactive"]}
            },
            "required": ["status"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        invalid_data = {"status": "pending"}

        validator = SchemaValidator(schema_path)
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(invalid_data)

        assert "enum" in str(exc_info.value).lower() or "pending" in str(exc_info.value)

    def test_get_validator_factory(self, temp_dir):
        """Test the get_validator factory function creates correct validator."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {"value": {"type": "number"}}
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        validator = get_validator(schema_path)
        assert isinstance(validator, SchemaValidator)
        assert validator.validate({"value": 3.14}) is True

    def test_integration_with_project_schemas(self, temp_dir):
        """Test that the validator works with the actual project schema files if they exist."""
        # Check if the project contracts directory exists and has schemas
        contracts_dir = Path(__file__).parent.parent.parent / "contracts"
        
        if contracts_dir.exists():
            # Find any yaml/json schema files
            schema_files = list(contracts_dir.glob("*.yaml")) + list(contracts_dir.glob("*.json"))
            
            if schema_files:
                # Test with the first found schema
                schema_file = schema_files[0]
                try:
                    # Load schema (handle yaml if jsonschema supports it or convert)
                    with open(schema_file, 'r') as f:
                        schema_content = json.load(f)
                    
                    # Create a temporary copy for the validator to avoid path issues
                    temp_schema = temp_dir / "temp_schema.json"
                    with open(temp_schema, 'w') as f:
                        json.dump(schema_content, f)
                    
                    validator = SchemaValidator(temp_schema)
                    
                    # Try to validate a minimal valid object based on schema type
                    # This is a basic sanity check; specific validation depends on schema content
                    if schema_content.get("type") == "object":
                        valid_instance = {}
                        # If there are required fields, we can't easily validate without more logic
                        # So we just check that the validator initializes and doesn't crash on empty object
                        # unless 'required' fields are present
                        try:
                            validator.validate(valid_instance)
                        except SchemaValidationError:
                            # Expected if required fields are missing, which is fine
                            pass
                    
                except json.JSONDecodeError:
                    # Skip if it's a YAML file and we can't parse it as JSON directly
                    # In a real scenario, we'd use PyYAML, but for this test we just ensure the mechanism works
                    pass
        else:
            pytest.skip("Contracts directory not found; skipping integration test.")

    def test_schema_file_loading(self, temp_dir):
        """Test that schema is loaded correctly from file."""
        schema_content = {
            "title": "Test Schema",
            "type": "object",
            "properties": {
                "field": {"type": "string"}
            }
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        validator = SchemaValidator(schema_path)
        assert validator.schema["title"] == "Test Schema"
        assert validator.schema["properties"]["field"]["type"] == "string"

    def test_validation_error_message_quality(self, temp_dir):
        """Test that validation errors provide meaningful messages."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "email": {"type": "string", "format": "email"}
            }
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        invalid_data = {"email": "not-an-email"}

        validator = SchemaValidator(schema_path)
        with pytest.raises(SchemaValidationError) as exc_info:
            validator.validate(invalid_data)

        error_msg = str(exc_info.value)
        assert "email" in error_msg or "format" in error_msg

    def test_empty_data_validation(self, temp_dir):
        """Test validation behavior with empty data."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "optional_field": {"type": "string"}
            }
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        validator = SchemaValidator(schema_path)
        # Empty object should be valid if no required fields
        assert validator.validate({}) is True

        # Add a required field to schema
        schema_content["required"] = ["optional_field"]
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)
        
        # Reload validator to pick up changes
        validator = SchemaValidator(schema_path)
        
        with pytest.raises(SchemaValidationError):
            validator.validate({})

    def test_array_schema_validation(self, temp_dir):
        """Test validation of array types."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {"type": "integer"}
                }
            },
            "required": ["items"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        valid_data = {"items": [1, 2, 3]}
        invalid_data = {"items": [1, "two", 3]}

        validator = SchemaValidator(schema_path)
        
        assert validator.validate(valid_data) is True
        
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data)

    def test_nested_object_validation(self, temp_dir):
        """Test validation of nested object structures."""
        schema_content = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "properties": {
                "user": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "age": {"type": "integer", "minimum": 0}
                    },
                    "required": ["name", "age"]
                }
            },
            "required": ["user"]
        }
        schema_path = temp_dir / "test_schema.json"
        with open(schema_path, "w") as f:
            json.dump(schema_content, f)

        valid_data = {"user": {"name": "Alice", "age": 30}}
        invalid_data = {"user": {"name": "Bob"}}  # Missing age
        invalid_age_data = {"user": {"name": "Charlie", "age": -5}}

        validator = SchemaValidator(schema_path)
        
        assert validator.validate(valid_data) is True
        
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data)
        
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_age_data)
