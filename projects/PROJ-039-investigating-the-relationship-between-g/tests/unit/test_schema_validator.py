import pytest
import json
import yaml
import os
import tempfile
from pathlib import Path
import sys

# Add code directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "code"))

from schema_validator import SchemaValidator, validate_artifacts

class TestSchemaValidator:
    @pytest.fixture
    def temp_schema_file(self):
        schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "Test Schema",
            "type": "object",
            "required": ["name", "age"],
            "properties": {
                "name": {"type": "string"},
                "age": {"type": "integer", "minimum": 0}
            }
        }
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(schema, f)
            return f.name

    @pytest.fixture
    def temp_input_file(self, temp_schema_file):
        data = {"name": "Alice", "age": 30}
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(data, f)
            return f.name

    def test_validator_initialization(self, temp_schema_file):
        validator = SchemaValidator(temp_schema_file)
        assert validator.schema is not None
        assert "required" in validator.schema

    def test_validate_valid_data(self, temp_schema_file, temp_input_file):
        validator = SchemaValidator(temp_schema_file)
        with open(temp_input_file) as f:
            data = json.load(f)
        assert validator.validate(data) is True

    def test_validate_missing_required_field(self, temp_schema_file):
        validator = SchemaValidator(temp_schema_file)
        data = {"name": "Alice"}  # Missing age
        assert validator.validate(data) is False

    def test_validate_wrong_type(self, temp_schema_file):
        validator = SchemaValidator(temp_schema_file)
        data = {"name": "Alice", "age": "thirty"}  # Age should be integer
        assert validator.validate(data) is False

    def test_validate_artifacts_function(self, temp_schema_file, temp_input_file):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as out:
            output_path = out.name

        try:
            result = validate_artifacts(temp_input_file, temp_schema_file, output_path)
            assert result is True
            
            with open(output_path) as f:
                out_data = json.load(f)
            assert out_data["valid"] is True
        finally:
            os.unlink(output_path)

    def test_validate_artifacts_invalid(self, temp_schema_file):
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"name": "Alice"}, f)
            input_path = f.name

        try:
            result = validate_artifacts(input_path, temp_schema_file)
            assert result is False
        finally:
            os.unlink(input_path)

    def test_schema_not_found(self):
        with pytest.raises(FileNotFoundError):
            SchemaValidator("non_existent_schema.yaml")

def test_dataset_schema_structure():
    """Test that the actual dataset schema file has the required structure"""
    schema_path = Path("contracts/dataset.schema.yaml")
    if not schema_path.exists():
        pytest.skip("Schema file not found (expected in full project)")
        return
    
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    
    assert "required" in schema
    required_fields = schema["required"]
    assert "age" in required_fields
    assert "sex" in required_fields
    assert "bmi" in required_fields
    assert "alpha_power" in required_fields
    assert "taxon_abundances" in required_fields

def test_output_schema_structure():
    """Test that the actual output schema file has the required structure"""
    schema_path = Path("contracts/output.schema.yaml")
    if not schema_path.exists():
        pytest.skip("Schema file not found (expected in full project)")
        return
    
    with open(schema_path) as f:
        schema = yaml.safe_load(f)
    
    assert "required" in schema
    required_fields = schema["required"]
    assert "stratum_id" in required_fields
    assert "stratum_mean_alpha_power" in required_fields
    assert "stratum_taxa_means" in required_fields
    assert "valid_strata_count" in required_fields