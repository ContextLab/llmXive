import pytest
import json
import os
from pathlib import Path
import yaml
from utils.data_utils import load_schema, validate_against_schema

# Path resolution relative to project root
# tests/contract/test_schemas.py -> project root is parent of tests
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
contracts_dir = project_root / "specs" / "001-gene-regulation" / "contracts"

def get_schema_path(schema_name: str) -> Path:
    """Construct the path to a schema file in the contracts directory."""
    return contracts_dir / f"{schema_name}.yaml"

def load_sample_dataset() -> dict:
    """
    Load a minimal valid sample dataset structure for schema validation.
    Matches the expected structure from generate_data.py output.
    """
    return {
        "columns": [
            "translation_x",
            "translation_y",
            "translation_z",
            "initial_object_bounds",
            "stability"
        ],
        "num_rows": 100,
        "format": "parquet"
    }

def load_sample_model_output() -> dict:
    """
    Load a minimal valid sample model output structure for schema validation.
    Matches the expected structure for model predictions.
    """
    return {
        "model_id": "test-model",
        "predictions": [
            {"row_id": 1, "predicted_stability": 1, "confidence": 0.9},
            {"row_id": 2, "predicted_stability": 0, "confidence": 0.8}
        ],
        "metrics": {"accuracy": 0.85}
    }

class TestDatasetSchema:
    def test_dataset_schema_exists(self):
        """Verify that the dataset schema file exists."""
        schema_path = get_schema_path("dataset.schema")
        assert schema_path.exists(), f"Dataset schema not found at {schema_path}"

    def test_dataset_schema_loads(self):
        """Verify that the dataset schema can be loaded as valid YAML/JSON."""
        schema_path = get_schema_path("dataset.schema")
        schema = load_schema(str(schema_path))
        assert schema is not None
        assert "type" in schema or "properties" in schema, "Schema must define type or properties"

    def test_sample_dataset_conforms(self):
        """Verify that a sample dataset conforms to the schema."""
        schema_path = get_schema_path("dataset.schema")
        schema = load_schema(str(schema_path))
        sample_data = load_sample_dataset()
        # validate_against_schema raises on failure, returns True on success
        result = validate_against_schema(sample_data, schema)
        assert result is True, "Sample dataset does not conform to dataset.schema.yaml"

class TestModelOutputSchema:
    def test_model_output_schema_exists(self):
        """Verify that the model output schema file exists."""
        schema_path = get_schema_path("model_output.schema")
        assert schema_path.exists(), f"Model output schema not found at {schema_path}"

    def test_model_output_schema_loads(self):
        """Verify that the model output schema can be loaded as valid YAML/JSON."""
        schema_path = get_schema_path("model_output.schema")
        schema = load_schema(str(schema_path))
        assert schema is not None
        assert "type" in schema or "properties" in schema, "Schema must define type or properties"

    def test_sample_model_output_conforms(self):
        """Verify that a sample model output conforms to the schema."""
        schema_path = get_schema_path("model_output.schema")
        schema = load_schema(str(schema_path))
        sample_data = load_sample_model_output()
        result = validate_against_schema(sample_data, schema)
        assert result is True, "Sample model output does not conform to model_output.schema.yaml"
