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
        # Verify specific GateMem required fields are present
        required_fields = schema.get("required", [])
        assert "outcome" in required_fields
        assert "predictors" in required_fields
        assert "covariates" in required_fields
        assert "leak-target" in required_fields

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

    def test_validate_against_real_schema(self):
        """Test validation against the actual GateMem schema file."""
        schema_path = Path("contracts/dataset.schema.yaml")
        schema = load_schema(str(schema_path))
        
        # Valid record matching schema
        valid_record = [
            {
                "id": "test-001",
                "outcome": "leak",
                "predictors": ["feature_a", "feature_b"],
                "covariates": {"domain": "medical"},
                "leak-target": "patient_name",
                "role": "admin",
                "domain": "medical",
                "query": "Get patient info",
                "memory": "Patient John Doe"
            }
        ]
        # Should not raise
        validate_fields(valid_record, schema)

        # Invalid record missing 'leak-target'
        invalid_record = [
            {
                "id": "test-002",
                "outcome": "no_leak",
                "predictors": [],
                "covariates": {},
                "role": "user"
            }
        ]
        with pytest.raises(ValueError) as excinfo:
            validate_fields(invalid_record, schema)
        assert "leak-target" in str(excinfo.value)
        assert "outcome" in str(excinfo.value)
        assert "predictors" in str(excinfo.value)
        assert "covariates" in str(excinfo.value)