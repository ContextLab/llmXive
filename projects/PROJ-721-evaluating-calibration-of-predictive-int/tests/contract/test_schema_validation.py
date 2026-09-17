"""
Contract tests for validating JSON data against the defined schemas.
Verifies that dataset records and output results conform to the expected structure.
"""
import json
import os
import pytest
import yaml
from jsonschema import validate, ValidationError, Draft7Validator

# Paths relative to project root
CONTRACTS_DIR = "contracts"
DATA_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "dataset.schema.yaml")
OUTPUT_SCHEMA_PATH = os.path.join(CONTRACTS_DIR, "output.schema.yaml")


def load_schema(schema_path: str) -> dict:
    """Load a YAML schema file and return it as a dictionary."""
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)


class TestDatasetSchema:
    """Tests for the M4 dataset schema (dataset.schema.yaml)."""

    @pytest.fixture
    def schema(self):
        return load_schema(DATA_SCHEMA_PATH)

    def test_schema_exists_and_valid(self, schema):
        """Ensure the schema file loads and is a valid JSON Schema dict."""
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_valid_dataset_record(self, schema):
        """Validate a correct M4 series record against the schema."""
        valid_record = {
            "id": "M1",
            "frequency": "monthly",
            "seasonality": 12,
            "values": [10.5, 11.2, 10.8, 12.1]
        }
        # Should not raise
        validate(instance=valid_record, schema=schema)

    def test_missing_required_field(self, schema):
        """Validate that missing required fields raise an error."""
        invalid_record = {
            "id": "M1",
            "frequency": "monthly"
            # Missing seasonality and values
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_record, schema=schema)

    def test_invalid_frequency_enum(self, schema):
        """Validate that invalid frequency values raise an error."""
        invalid_record = {
            "id": "M1",
            "frequency": "invalid_freq",
            "seasonality": 12,
            "values": [1.0]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_record, schema=schema)

    def test_negative_seasonality(self, schema):
        """Validate that negative seasonality raises an error."""
        invalid_record = {
            "id": "M1",
            "frequency": "monthly",
            "seasonality": -1,
            "values": [1.0]
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_record, schema=schema)


class TestOutputSchema:
    """Tests for the output results schema (output.schema.yaml)."""

    @pytest.fixture
    def schema(self):
        return load_schema(OUTPUT_SCHEMA_PATH)

    def test_schema_exists_and_valid(self, schema):
        """Ensure the schema file loads and is a valid JSON Schema dict."""
        assert isinstance(schema, dict)
        assert "$schema" in schema
        assert schema["$schema"] == "http://json-schema.org/draft-07/schema#"

    def test_valid_output_record(self, schema):
        """Validate a correct coverage result record against the schema."""
        valid_record = {
            "series_id": "M1",
            "model": "ARIMA",
            "horizon": 1,
            "nominal_coverage": 0.95,
            "empirical_coverage": 0.93,
            "deviation": 0.02
        }
        validate(instance=valid_record, schema=schema)

    def test_invalid_model_enum(self, schema):
        """Validate that invalid model names raise an error."""
        invalid_record = {
            "series_id": "M1",
            "model": "RandomForest",
            "horizon": 1,
            "nominal_coverage": 0.95,
            "empirical_coverage": 0.93,
            "deviation": 0.02
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_record, schema=schema)

    def test_coverage_out_of_range(self, schema):
        """Validate that coverage > 1.0 raises an error."""
        invalid_record = {
            "series_id": "M1",
            "model": "Prophet",
            "horizon": 1,
            "nominal_coverage": 1.5,
            "empirical_coverage": 0.93,
            "deviation": 0.57
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_record, schema=schema)

    def test_missing_deviation(self, schema):
        """Validate that missing deviation field raises an error."""
        invalid_record = {
            "series_id": "M1",
            "model": "ETS",
            "horizon": 1,
            "nominal_coverage": 0.80,
            "empirical_coverage": 0.78
            # Missing deviation
        }
        with pytest.raises(ValidationError):
            validate(instance=invalid_record, schema=schema)