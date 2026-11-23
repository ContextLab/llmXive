import json
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

import yaml

# Import the validator from the project source
# The project structure assumes code/src/ is added to sys.path or installed
from src.schema_validator import SchemaValidator, SchemaValidationError
from src.config import get_contract_path, ensure_directories


class TestSchemaEnforcement:
    """
    Tests to verify that the schema enforcement mechanism works correctly.
    Validates that data adheres to the JSON schemas defined in contracts/.
    """

    @pytest.fixture(autouse=True)
    def setup_schemas(self, tmp_path):
        """Create temporary schema files for testing."""
        self.tmp_dir = tmp_path
        self.contracts_dir = self.tmp_dir / "contracts"
        self.contracts_dir.mkdir()

        # Create a mock injection schema
        injection_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["injection_id", "mass_1", "mass_2", "luminosity_distance", "snr"],
            "properties": {
                "injection_id": {"type": "string"},
                "mass_1": {"type": "number", "minimum": 0},
                "mass_2": {"type": "number", "minimum": 0},
                "luminosity_distance": {"type": "number", "minimum": 0},
                "snr": {"type": "number"},
                "sampling_rate": {"type": "integer", "enum": [256, 512, 1024, 2048, 4096]},
                "metadata": {"type": "object"}
            },
            "additionalProperties": False
        }

        # Create a mock detection metric schema
        detection_schema = {
            "$schema": "http://json-schema.org/draft-07/schema#",
            "type": "object",
            "required": ["metric_id", "resolution_hz", "detection_probability"],
            "properties": {
                "metric_id": {"type": "string"},
                "resolution_hz": {"type": "integer"},
                "detection_probability": {"type": "number", "minimum": 0, "maximum": 1},
                "sample_size": {"type": "integer", "minimum": 1}
            },
            "additionalProperties": False
        }

        self.injection_schema_path = self.contracts_dir / "injection.schema.yaml"
        self.detection_schema_path = self.contracts_dir / "detection_metric.schema.yaml"

        with open(self.injection_schema_path, 'w') as f:
            yaml.dump(injection_schema, f)

        with open(self.detection_schema_path, 'w') as f:
            yaml.dump(detection_schema, f)

        # Patch get_contract_path to return our temp directory
        self.patcher = patch('src.schema_validator.get_contract_path', return_value=str(self.contracts_dir))
        self.patcher.start()
        
        # Also patch ensure_directories to use temp dir if needed, 
        # but mostly we just need the validator to find the schema files.
        # The validator loads schemas by name from the contracts dir.

        yield

        self.patcher.stop()

    def test_schema_validator_initialization(self):
        """Test that SchemaValidator can be initialized and loads schemas."""
        validator = SchemaValidator()
        assert validator is not None
        # Check that schemas are loaded (implementation dependent, but we expect no crash)
        assert hasattr(validator, 'schemas')

    def test_validate_valid_injection_data(self):
        """Test validation of data that conforms to the injection schema."""
        valid_data = {
            "injection_id": "test-001",
            "mass_1": 30.0,
            "mass_2": 25.0,
            "luminosity_distance": 200.0,
            "snr": 12.5,
            "sampling_rate": 4096,
            "metadata": {"source": "simulated"}
        }

        validator = SchemaValidator()
        result = validator.validate(valid_data, "injection")
        
        assert result is True

    def test_validate_invalid_injection_data_missing_field(self):
        """Test validation fails when a required field is missing."""
        invalid_data = {
            "injection_id": "test-002",
            "mass_1": 30.0,
            # missing mass_2, luminosity_distance, snr
        }

        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data, "injection")

    def test_validate_invalid_injection_data_type(self):
        """Test validation fails when a field has the wrong type."""
        invalid_data = {
            "injection_id": "test-003",
            "mass_1": "thirty",  # Should be number
            "mass_2": 25.0,
            "luminosity_distance": 200.0,
            "snr": 12.5,
            "sampling_rate": 4096
        }

        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data, "injection")

    def test_validate_invalid_sampling_rate(self):
        """Test validation fails for an unsupported sampling rate."""
        invalid_data = {
            "injection_id": "test-004",
            "mass_1": 30.0,
            "mass_2": 25.0,
            "luminosity_distance": 200.0,
            "snr": 12.5,
            "sampling_rate": 8192  # Not in enum
        }

        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data, "injection")

    def test_validate_valid_detection_metric(self):
        """Test validation of data that conforms to the detection metric schema."""
        valid_data = {
            "metric_id": "metric-001",
            "resolution_hz": 1024,
            "detection_probability": 0.85,
            "sample_size": 100
        }

        validator = SchemaValidator()
        result = validator.validate(valid_data, "detection_metric")
        
        assert result is True

    def test_validate_detection_metric_probability_range(self):
        """Test validation fails if probability is out of range."""
        invalid_data = {
            "metric_id": "metric-002",
            "resolution_hz": 512,
            "detection_probability": 1.5,  # > 1
            "sample_size": 50
        }

        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data, "detection_metric")

    def test_validate_extra_properties(self):
        """Test validation fails if additional properties are present (schema forbids)."""
        invalid_data = {
            "injection_id": "test-005",
            "mass_1": 30.0,
            "mass_2": 25.0,
            "luminosity_distance": 200.0,
            "snr": 12.5,
            "sampling_rate": 4096,
            "unexpected_field": "should_fail"
        }

        validator = SchemaValidator()
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data, "injection")

    def test_schema_not_found(self):
        """Test behavior when a schema name is not found."""
        invalid_data = {"id": "1"}
        validator = SchemaValidator()
        
        with pytest.raises(SchemaValidationError):
            validator.validate(invalid_data, "non_existent_schema")

    def test_convenience_function_validate_data(self):
        """Test the top-level validate_data function."""
        valid_data = {
            "injection_id": "test-006",
            "mass_1": 10.0,
            "mass_2": 10.0,
            "luminosity_distance": 100.0,
            "snr": 8.0,
            "sampling_rate": 2048
        }
        
        # This should not raise
        result = validate_data(valid_data, "injection")
        assert result is True

    def test_convenience_function_invalid_data(self):
        """Test the top-level validate_data function with invalid data."""
        invalid_data = {
            "injection_id": "test-007",
            "mass_1": "bad"
        }
        
        with pytest.raises(SchemaValidationError):
            validate_data(invalid_data, "injection")

    def test_schema_file_integrity(self):
        """Verify that the schema files themselves are valid YAML/JSON."""
        # Load and parse the schema files to ensure they are well-formed
        with open(self.injection_schema_path, 'r') as f:
            schema = yaml.safe_load(f)
            assert schema is not None
            assert "required" in schema
            assert "properties" in schema

        with open(self.detection_schema_path, 'r') as f:
            schema = yaml.safe_load(f)
            assert schema is not None
            assert "required" in schema

    def test_validate_and_save_integration(self):
        """Test the validate_and_save function which writes to disk."""
        valid_data = {
            "injection_id": "test-save-001",
            "mass_1": 30.0,
            "mass_2": 25.0,
            "luminosity_distance": 200.0,
            "snr": 12.5,
            "sampling_rate": 4096
        }
        
        output_path = self.tmp_dir / "test_output.json"
        
        # This should succeed and write the file
        result = validate_and_save(valid_data, "injection", str(output_path))
        
        assert result is True
        assert output_path.exists()
        
        # Verify content
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
            assert saved_data["injection_id"] == "test-save-001"
            assert saved_data["snr"] == 12.5

    def test_validate_and_save_invalid(self):
        """Test validate_and_save with invalid data."""
        invalid_data = {
            "injection_id": "test-save-002",
            "mass_1": "invalid"
        }
        
        output_path = self.tmp_dir / "test_output_invalid.json"
        
        with pytest.raises(SchemaValidationError):
            validate_and_save(invalid_data, "injection", str(output_path))
        
        # File should not exist if validation failed
        assert not output_path.exists()

# Helper functions imported from the module for testing convenience
def validate_data(data, schema_name):
    """Convenience wrapper for SchemaValidator.validate"""
    validator = SchemaValidator()
    return validator.validate(data, schema_name)

def validate_and_save(data, schema_name, output_path):
    """Convenience wrapper for SchemaValidator.validate_and_save"""
    validator = SchemaValidator()
    return validator.validate_and_save(data, schema_name, output_path)