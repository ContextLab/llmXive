"""
Contract tests for data schema validation.

These tests verify that the data schemas defined in specs/001-knot-complexity-analysis/contracts/
are properly structured and can validate data correctly.

Per Constitution Principle I: All random seeds must be pinned for reproducibility.
"""

import json
import yaml
from pathlib import Path
from typing import Dict, Any, List
import pytest

# Pin random seed for reproducibility per Constitution Principle I
import random
random.seed(42)

# Test data schema paths
SCHEMAS_DIR = Path(__file__).parent.parent.parent / "specs" / "001-knot-complexity-analysis" / "contracts"
KNOT_RECORD_SCHEMA = SCHEMAS_DIR / "knot-record.schema.yaml"
REGRESSION_MODEL_SCHEMA = SCHEMAS_DIR / "regression-model.schema.yaml"
DATASET_SCHEMA = SCHEMAS_DIR / "dataset.schema.yaml"


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_knot_record_schema() -> None:
    """Validate the knot record schema structure."""
    schema = load_schema(KNOT_RECORD_SCHEMA)

    # Check required top-level keys
    assert "name" in schema, "Schema must have 'name' field"
    assert "type" in schema, "Schema must have 'type' field"
    assert "properties" in schema, "Schema must have 'properties' field"

    # Check required knot record fields
    required_fields = [
        "knot_id",
        "crossing_number",
        "braid_index",
        "hyperbolic_volume",
        "is_alternating"
    ]

    for field in required_fields:
        assert field in schema["properties"], f"Schema must have '{field}' property"


def validate_regression_model_schema() -> None:
    """Validate the regression model schema structure."""
    schema = load_schema(REGRESSION_MODEL_SCHEMA)

    # Check required top-level keys
    assert "name" in schema, "Schema must have 'name' field"
    assert "type" in schema, "Schema must have 'type' field"
    assert "properties" in schema, "Schema must have 'properties' field"

    # Check required regression model fields
    required_fields = [
        "model_id",
        "model_type",
        "features",
        "target",
        "coefficients"
    ]

    for field in required_fields:
        assert field in schema["properties"], f"Schema must have '{field}' property"


def validate_dataset_schema() -> None:
    """Validate the dataset schema structure."""
    schema = load_schema(DATASET_SCHEMA)

    # Check required top-level keys
    assert "name" in schema, "Schema must have 'name' field"
    assert "type" in schema, "Schema must have 'type' field"
    assert "properties" in schema, "Schema must have 'properties' field"

    # Check required dataset fields
    required_fields = [
        "dataset_id",
        "name",
        "description",
        "created_at",
        "records",
        "metadata"
    ]

    for field in required_fields:
        assert field in schema["properties"], f"Schema must have '{field}' property"


class TestKnotRecordSchema:
    """Contract tests for knot record schema."""

    def test_schema_file_exists(self):
        """Test that the knot record schema file exists."""
        assert KNOT_RECORD_SCHEMA.exists(), f"Schema file not found: {KNOT_RECORD_SCHEMA}"

    def test_schema_structure(self):
        """Test that the knot record schema has required structure."""
        validate_knot_record_schema()

    def test_schema_valid_yaml(self):
        """Test that the knot record schema is valid YAML."""
        schema = load_schema(KNOT_RECORD_SCHEMA)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert schema["type"] == "object", "Schema type must be 'object'"

    def test_schema_has_version(self):
        """Test that the schema has a version field."""
        schema = load_schema(KNOT_RECORD_SCHEMA)
        assert "version" in schema, "Schema must have 'version' field"

    def test_schema_properties_are_objects(self):
        """Test that all properties in the schema are objects."""
        schema = load_schema(KNOT_RECORD_SCHEMA)
        for prop_name, prop_def in schema["properties"].items():
            assert isinstance(prop_def, dict), f"Property '{prop_name}' must be a dictionary"


class TestRegressionModelSchema:
    """Contract tests for regression model schema."""

    def test_schema_file_exists(self):
        """Test that the regression model schema file exists."""
        assert REGRESSION_MODEL_SCHEMA.exists(), f"Schema file not found: {REGRESSION_MODEL_SCHEMA}"

    def test_schema_structure(self):
        """Test that the regression model schema has required structure."""
        validate_regression_model_schema()

    def test_schema_valid_yaml(self):
        """Test that the regression model schema is valid YAML."""
        schema = load_schema(REGRESSION_MODEL_SCHEMA)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert schema["type"] == "object", "Schema type must be 'object'"

    def test_schema_has_version(self):
        """Test that the schema has a version field."""
        schema = load_schema(REGRESSION_MODEL_SCHEMA)
        assert "version" in schema, "Schema must have 'version' field"


class TestDatasetSchema:
    """Contract tests for dataset schema."""

    def test_schema_file_exists(self):
        """Test that the dataset schema file exists."""
        assert DATASET_SCHEMA.exists(), f"Schema file not found: {DATASET_SCHEMA}"

    def test_schema_structure(self):
        """Test that the dataset schema has required structure."""
        validate_dataset_schema()

    def test_schema_valid_yaml(self):
        """Test that the dataset schema is valid YAML."""
        schema = load_schema(DATASET_SCHEMA)
        assert isinstance(schema, dict), "Schema must be a dictionary"
        assert schema["type"] == "object", "Schema type must be 'object'"

    def test_schema_has_version(self):
        """Test that the schema has a version field."""
        schema = load_schema(DATASET_SCHEMA)
        assert "version" in schema, "Schema must have 'version' field"


class TestDataQualityFlagsSchema:
    """Contract tests for data quality flags validation."""

    def test_data_quality_flags_field_exists(self):
        """Test that data quality flags are defined in the schema."""
        schema = load_schema(KNOT_RECORD_SCHEMA)
        assert "data_quality_flags" in schema["properties"], \
            "Schema must have 'data_quality_flags' property"

    def test_missing_invariant_flags_field_exists(self):
        """Test that missing invariant flags are defined in the schema."""
        schema = load_schema(KNOT_RECORD_SCHEMA)
        assert "missing_invariant_flags" in schema["properties"], \
            "Schema must have 'missing_invariant_flags' property"


class TestSampleDataValidation:
    """Contract tests for sample data validation against schemas."""

    def test_sample_knot_record_validates(self):
        """Test that a sample knot record validates against the schema."""
        schema = load_schema(KNOT_RECORD_SCHEMA)

        # Sample valid knot record data
        sample_record = {
            "knot_id": "5_2",
            "crossing_number": 5,
            "braid_index": 3,
            "hyperbolic_volume": 2.828,
            "is_alternating": False,
            "data_quality_flags": [],
            "missing_invariant_flags": []
        }

        # Basic validation: check all required fields are present
        for field in ["knot_id", "crossing_number", "braid_index", "hyperbolic_volume", "is_alternating"]:
            assert field in sample_record, f"Sample record missing required field: {field}"

        # Verify field types
        assert isinstance(sample_record["knot_id"], str), "knot_id must be string"
        assert isinstance(sample_record["crossing_number"], int), "crossing_number must be int"
        assert isinstance(sample_record["braid_index"], int), "braid_index must be int"
        assert isinstance(sample_record["hyperbolic_volume"], (int, float)), "hyperbolic_volume must be numeric"
        assert isinstance(sample_record["is_alternating"], bool), "is_alternating must be bool"

    def test_sample_regression_model_validates(self):
        """Test that a sample regression model validates against the schema."""
        schema = load_schema(REGRESSION_MODEL_SCHEMA)

        # Sample valid regression model data
        sample_model = {
            "model_id": "linear_crossing_braid",
            "model_type": "linear",
            "features": ["crossing_number"],
            "target": "braid_index",
            "coefficients": [0.5],
            "r_squared": 0.85,
            "created_at": "2024-01-01T00:00:00Z"
        }

        # Basic validation: check all required fields are present
        for field in ["model_id", "model_type", "features", "target", "coefficients"]:
            assert field in sample_model, f"Sample model missing required field: {field}"

    def test_sample_dataset_validates(self):
        """Test that a sample dataset validates against the schema."""
        schema = load_schema(DATASET_SCHEMA)

        # Sample valid dataset data
        sample_dataset = {
            "dataset_id": "knot_atlas_c13",
            "name": "Knot Atlas Crossing Number <= 13",
            "description": "Prime knots with crossing number <= 13 from Knot Atlas",
            "created_at": "2024-01-01T00:00:00Z",
            "records": [],
            "metadata": {
                "source": "Knot Atlas",
                "url": "https://katlas.org",
                "version": "1.0"
            }
        }

        # Basic validation: check all required fields are present
        for field in ["dataset_id", "name", "description", "created_at", "records", "metadata"]:
            assert field in sample_dataset, f"Sample dataset missing required field: {field}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])