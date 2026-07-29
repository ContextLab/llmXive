import pytest
import json
import yaml
from pathlib import Path
from code.utils.data_loader import load_schema, validate_fields

class TestDatasetSchema:
    def test_schema_loads(self):
        """Test that the dataset schema file loads correctly."""
        schema_path = Path("contracts/dataset.schema.yaml")
        assert schema_path.exists(), "Schema file not found"
        schema = load_schema(str(schema_path))
        assert "required" in schema

    def test_validate_fields_passes(self):
        """Test that valid data passes validation."""
        schema = {
            "required": ["id", "query", "role", "domain"]
        }
        valid_data = [
            {"id": "1", "query": "test", "role": "user", "domain": "test"},
            {"id": "2", "query": "test2", "role": "admin", "domain": "test"}
        ]
        # Should not raise
        validate_fields(valid_data, schema)

    def test_validate_fields_fails_missing(self):
        """Test that missing required fields raise ValueError."""
        schema = {
            "required": ["id", "missing_field"]
        }
        invalid_data = [
            {"id": "1", "query": "test"} # missing_field is missing
        ]
        
        with pytest.raises(ValueError) as excinfo:
            validate_fields(invalid_data, schema)
        
        assert "missing_field" in str(excinfo.value)

    def test_validate_fields_fails_all_missing(self):
        """Test error when all required fields are missing."""
        schema = {
            "required": ["outcome", "predictors", "covariates", "leak-target"]
        }
        invalid_data = [
            {"id": "1", "query": "test"}
        ]
        
        with pytest.raises(ValueError) as excinfo:
            validate_fields(invalid_data, schema)
        
        error_msg = str(excinfo.value)
        assert "outcome" in error_msg
        assert "predictors" in error_msg
        assert "covariates" in error_msg
        assert "leak-target" in error_msg
