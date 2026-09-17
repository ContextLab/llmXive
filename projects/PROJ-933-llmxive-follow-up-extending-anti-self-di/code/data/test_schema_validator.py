"""
Unit tests for schema validation logic.
"""
import json
import tempfile
import pytest
from pathlib import Path
from data.schema_validator import (
    SchemaValidationError,
    load_schema,
    validate_type,
    validate_value,
    validate_object,
    validate_json_against_schema,
    validate_dataset_schema,
    validate_training_output_schema,
    validate_analysis_results_schema,
    load_json_file
)


class TestValidateType:
    def test_string_type(self):
        assert validate_type("hello", "string") is True
        assert validate_type(123, "string") is False
        
    def test_number_type(self):
        assert validate_type(123, "number") is True
        assert validate_type(12.5, "number") is True
        assert validate_type("123", "number") is False
        
    def test_integer_type(self):
        assert validate_type(123, "integer") is True
        assert validate_type(12.5, "integer") is False
        assert validate_type(True, "integer") is False  # bool is subclass of int in Python
        
    def test_boolean_type(self):
        assert validate_type(True, "boolean") is True
        assert validate_type(False, "boolean") is True
        assert validate_type(1, "boolean") is False  # int is not bool
        
    def test_array_type(self):
        assert validate_type([1, 2, 3], "array") is True
        assert validate_type((1, 2, 3), "array") is False
        
    def test_object_type(self):
        assert validate_type({"key": "value"}, "object") is True
        assert validate_type([], "object") is False
        
    def test_null_type(self):
        assert validate_type(None, "null") is True
        assert validate_type("", "null") is False


class TestValidateValue:
    def test_valid_string(self):
        schema = {"type": "string"}
        validate_value("hello", schema)  # Should not raise
        
    def test_invalid_string_type(self):
        schema = {"type": "string"}
        with pytest.raises(SchemaValidationError):
            validate_value(123, schema)
            
    def test_string_min_length(self):
        schema = {"type": "string", "minLength": 5}
        validate_value("hello", schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value("hi", schema)
            
    def test_string_max_length(self):
        schema = {"type": "string", "maxLength": 3}
        validate_value("hi", schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value("hello", schema)
            
    def test_string_pattern(self):
        schema = {"type": "string", "pattern": r"^[a-z]+$"}
        validate_value("hello", schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value("Hello", schema)
            
    def test_string_enum(self):
        schema = {"type": "string", "enum": ["red", "green", "blue"]}
        validate_value("red", schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value("yellow", schema)
            
    def test_number_minimum(self):
        schema = {"type": "number", "minimum": 0}
        validate_value(5, schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value(-1, schema)
            
    def test_number_maximum(self):
        schema = {"type": "number", "maximum": 100}
        validate_value(50, schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value(150, schema)
            
    def test_array_min_items(self):
        schema = {"type": "array", "minItems": 3}
        validate_value([1, 2, 3], schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value([1, 2], schema)
            
    def test_array_items_validation(self):
        schema = {"type": "array", "items": {"type": "integer"}}
        validate_value([1, 2, 3], schema)  # Should not raise
        with pytest.raises(SchemaValidationError):
            validate_value([1, "two", 3], schema)


class TestValidateObject:
    def test_valid_object(self):
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        validate_object({"name": "Alice", "age": 30}, schema)  # Should not raise
        
    def test_missing_required_field(self):
        schema = {
            "type": "object",
            "required": ["name"],
            "properties": {
                "name": {"type": "string"}
            }
        }
        with pytest.raises(SchemaValidationError):
            validate_object({}, schema)
            
    def test_invalid_property_type(self):
        schema = {
            "type": "object",
            "properties": {
                "age": {"type": "integer"}
            }
        }
        with pytest.raises(SchemaValidationError):
            validate_object({"age": "thirty"}, schema)
            
    def test_additional_properties_false(self):
        schema = {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "name": {"type": "string"}
            }
        }
        with pytest.raises(SchemaValidationError):
            validate_object({"name": "Alice", "extra": "field"}, schema)


class TestValidateJsonAgainstSchema:
    def test_valid_json(self):
        data = {"name": "Alice", "age": 30}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        validate_json_against_schema(data, schema)  # Should not raise
        
    def test_invalid_json(self):
        data = {"name": "Alice", "age": "thirty"}
        schema = {
            "type": "object",
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer"}
            }
        }
        with pytest.raises(SchemaValidationError):
            validate_json_against_schema(data, schema)


class TestValidateDatasetSchema:
    def test_valid_dataset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.json"
            schema_file = Path(tmpdir) / "schema.yaml"
            
            data = {"prompts": [{"id": "1", "text": "hello"}]}
            schema = {
                "type": "object",
                "properties": {
                    "prompts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "text": {"type": "string"}
                            },
                            "required": ["id", "text"]
                        }
                    }
                },
                "required": ["prompts"]
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f)
            with open(schema_file, 'w') as f:
                import yaml
                yaml.dump(schema, f)
                
            result = validate_dataset_schema(str(data_file), str(schema_file))
            assert result is True
            
    def test_invalid_dataset(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "data.json"
            schema_file = Path(tmpdir) / "schema.yaml"
            
            data = {"prompts": [{"id": "1"}]}  # Missing "text"
            schema = {
                "type": "object",
                "properties": {
                    "prompts": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "text": {"type": "string"}
                            },
                            "required": ["id", "text"]
                        }
                    }
                },
                "required": ["prompts"]
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f)
            with open(schema_file, 'w') as f:
                import yaml
                yaml.dump(schema, f)
                
            with pytest.raises(SchemaValidationError):
                validate_dataset_schema(str(data_file), str(schema_file))


class TestValidateTrainingOutputSchema:
    def test_valid_training_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "output.json"
            schema_file = Path(tmpdir) / "schema.yaml"
            
            data = {
                "training_loss": 0.5,
                "steps": 100,
                "model_path": "/path/to/model"
            }
            schema = {
                "type": "object",
                "properties": {
                    "training_loss": {"type": "number"},
                    "steps": {"type": "integer"},
                    "model_path": {"type": "string"}
                },
                "required": ["training_loss", "steps", "model_path"]
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f)
            with open(schema_file, 'w') as f:
                import yaml
                yaml.dump(schema, f)
                
            result = validate_training_output_schema(str(data_file), str(schema_file))
            assert result is True


class TestValidateAnalysisResultsSchema:
    def test_valid_analysis_results(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            data_file = Path(tmpdir) / "analysis.json"
            schema_file = Path(tmpdir) / "schema.yaml"
            
            data = {
                "p_value": 0.03,
                "effect_size": 0.8,
                "power": 0.85
            }
            schema = {
                "type": "object",
                "properties": {
                    "p_value": {"type": "number"},
                    "effect_size": {"type": "number"},
                    "power": {"type": "number"}
                },
                "required": ["p_value", "effect_size", "power"]
            }
            
            with open(data_file, 'w') as f:
                json.dump(data, f)
            with open(schema_file, 'w') as f:
                import yaml
                yaml.dump(schema, f)
                
            result = validate_analysis_results_schema(str(data_file), str(schema_file))
            assert result is True


class TestLoadSchema:
    def test_load_yaml_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "schema.yaml"
            schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            
            with open(schema_file, 'w') as f:
                import yaml
                yaml.dump(schema, f)
                
            result = load_schema(str(schema_file))
            assert result == schema
            
    def test_load_json_schema(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "schema.json"
            schema = {"type": "object", "properties": {"name": {"type": "string"}}}
            
            with open(schema_file, 'w') as f:
                json.dump(schema, f)
                
            result = load_schema(str(schema_file))
            assert result == schema
            
    def test_schema_not_found(self):
        with pytest.raises(FileNotFoundError):
            load_schema("/nonexistent/path/schema.yaml")
            
    def test_unsupported_format(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            schema_file = Path(tmpdir) / "schema.txt"
            schema_file.write_text("type: object")
            
            with pytest.raises(ValueError):
                load_schema(str(schema_file))
