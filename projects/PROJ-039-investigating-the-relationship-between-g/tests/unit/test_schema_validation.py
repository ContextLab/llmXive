"""
Unit tests for schema validation functionality.
"""
import pytest
import json
import yaml
import os
import sys
from pathlib import Path
from unittest.mock import patch, mock_open

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from schema_validator import SchemaValidator, validate_artifacts

# Test data
VALID_DATASET_RECORD = {
    "age": 30,
    "sex": "Male",
    "bmi": 25.5,
    "alpha_power": 10.2,
    "taxon_abundances": {
        "Bacteroides": 0.4,
        "Firmicutes": 0.3,
        "Actinobacteria": 0.2
    }
}

INVALID_DATASET_RECORD = {
    "age": "thirty",  # Should be integer
    "sex": "Male",
    "bmi": 25.5,
    "alpha_power": 10.2,
    "taxon_abundances": {
        "Bacteroides": 0.4
    }
}

VALID_OUTPUT_RECORD = {
    "stratum_id": "S001",
    "stratum_mean_alpha_power": 12.5,
    "stratum_taxa_means": {
        "Bacteroides": 0.35,
        "Firmicutes": 0.45
    },
    "valid_strata_count": 5
}

INVALID_OUTPUT_RECORD = {
    "stratum_id": "S001",
    "stratum_mean_alpha_power": "high",  # Should be number
    "stratum_taxa_means": {
        "Bacteroides": 0.35
    },
    "valid_strata_count": 5
}

# Sample schema content for testing
SAMPLE_DATASET_SCHEMA = """
$schema: "http://json-schema.org/draft-07/schema#"
title: "TestDataset"
type: "object"
required:
  - age
  - name
properties:
  age:
    type: integer
    minimum: 0
  name:
    type: string
"""

SAMPLE_OUTPUT_SCHEMA = """
$schema: "http://json-schema.org/draft-07/schema#"
title: "TestOutput"
type: "object"
required:
  - id
  - value
properties:
  id:
    type: string
  value:
    type: number
"""

class TestSchemaValidator:
    """Test cases for SchemaValidator class."""
    
    def test_load_schema_from_yaml(self, tmp_path):
        """Test loading schema from a YAML file."""
        schema_file = tmp_path / "test_schema.yaml"
        schema_file.write_text(SAMPLE_DATASET_SCHEMA)
        
        validator = SchemaValidator(str(schema_file))
        assert validator.schema is not None
        assert validator.schema["title"] == "TestDataset"
    
    def test_load_schema_from_json(self, tmp_path):
        """Test loading schema from a JSON file."""
        schema_data = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "title": "TestJSONSchema",
            "type": "object"
        }
        schema_file = tmp_path / "test_schema.json"
        schema_file.write_text(json.dumps(schema_data))
        
        validator = SchemaValidator(str(schema_file))
        assert validator.schema is not None
        assert validator.schema["title"] == "TestJSONSchema"
    
    def test_validate_valid_record(self):
        """Test validation of a valid record."""
        # Create a temporary schema file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(SAMPLE_DATASET_SCHEMA)
            temp_path = f.name
        
        try:
            validator = SchemaValidator(temp_path)
            # This should not raise an exception
            result = validator.validate(VALID_DATASET_RECORD)
            assert result is True
        finally:
            os.unlink(temp_path)
    
    def test_validate_invalid_record(self):
        """Test validation of an invalid record."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(SAMPLE_DATASET_SCHEMA)
            temp_path = f.name
        
        try:
            validator = SchemaValidator(temp_path)
            with pytest.raises(Exception):  # jsonschema.ValidationError
                validator.validate(INVALID_DATASET_RECORD)
        finally:
            os.unlink(temp_path)
    
    def test_validate_list_of_records(self):
        """Test validation of a list of records."""
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(SAMPLE_DATASET_SCHEMA)
            temp_path = f.name
        
        try:
            validator = SchemaValidator(temp_path)
            records = [VALID_DATASET_RECORD, VALID_DATASET_RECORD]
            result = validator.validate(records)
            assert result is True
        finally:
            os.unlink(temp_path)
    
    def test_validate_file_not_found(self):
        """Test validation when file does not exist."""
        validator = SchemaValidator("/nonexistent/path/schema.yaml")
        with pytest.raises(FileNotFoundError):
            validator.validate_file("/nonexistent/path/data.json")
    
    def test_missing_required_field(self):
        """Test validation fails when required field is missing."""
        missing_field_record = {
            "age": 30,
            # Missing 'name' which is required
        }
        
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(SAMPLE_DATASET_SCHEMA)
            temp_path = f.name
        
        try:
            validator = SchemaValidator(temp_path)
            with pytest.raises(Exception):
                validator.validate(missing_field_record)
        finally:
            os.unlink(temp_path)

class TestValidateArtifacts:
    """Test cases for validate_artifacts function."""
    
    def test_schemas_exist(self):
        """Test that validate_artifacts returns True when schemas exist."""
        # This test assumes the schemas are present in the contracts directory
        # as per the task requirements
        result = validate_artifacts()
        assert result is True

if __name__ == "__main__":
    pytest.main([__file__, "-v"])