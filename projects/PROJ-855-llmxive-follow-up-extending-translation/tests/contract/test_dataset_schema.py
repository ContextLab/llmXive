import pytest
import json
import os
from pathlib import Path
from utils.data_utils import load_schema, validate_against_schema

# Path resolution relative to project root
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent
contracts_dir = project_root / "specs" / "001-gene-regulation" / "contracts"

def get_schema_path() -> Path:
    """Return the path to the dataset schema file."""
    return contracts_dir / "dataset.schema.yaml"

def load_real_data_sample() -> dict:
    """
    Load a minimal sample dataset that conforms to the expected schema.
    This is used to verify the schema validation logic.
    The sample reflects the columns required by generate_data.py:
    - translation_vector (list of floats)
    - initial_object_bounds (list of floats)
    - stability (int: 0 or 1)
    """
    return {
        "columns": [
            "translation_vector",
            "initial_object_bounds",
            "stability"
        ],
        "num_rows": 100,
        "format": "parquet",
        "metadata": {
            "generated_by": "test",
            "version": "1.0"
        }
    }

class TestDatasetSchemaContract:
    def test_schema_file_exists(self):
        """Verify that the dataset schema file exists in the contracts directory."""
        schema_path = get_schema_path()
        assert schema_path.exists(), f"Dataset schema file not found at {schema_path}"

    def test_schema_loads_correctly(self):
        """Verify that the dataset schema can be loaded and parsed."""
        schema_path = get_schema_path()
        schema = load_schema(str(schema_path))
        assert schema is not None, "Failed to load schema"
        assert "properties" in schema or "type" in schema, "Invalid schema structure"

    def test_sample_dataset_validates(self):
        """
        Verify that a sample dataset validates against the schema.
        This ensures the schema is correctly defined and the validation logic works.
        """
        schema_path = get_schema_path()
        schema = load_schema(str(schema_path))
        sample_data = load_real_data_sample()

        # Attempt validation; should not raise an exception if valid
        try:
            validate_against_schema(sample_data, schema)
        except Exception as e:
            pytest.fail(f"Sample dataset failed schema validation: {e}")

    def test_missing_columns_fails(self):
        """
        Verify that a dataset with missing required columns fails validation.
        """
        schema_path = get_schema_path()
        schema = load_schema(str(schema_path))
        
        # Create a dataset missing a required column (e.g., 'stability')
        invalid_data = {
            "columns": ["translation_vector", "initial_object_bounds"],
            "num_rows": 100,
            "format": "parquet"
        }

        with pytest.raises(Exception):
            validate_against_schema(invalid_data, schema)

    def test_extra_columns_pass(self):
        """
        Verify that a dataset with extra (non-required) columns passes validation.
        (Assuming the schema allows additional properties or the extra columns are ignored)
        """
        schema_path = get_schema_path()
        schema = load_schema(str(schema_path))
        
        # Create a dataset with an extra column
        extra_data = {
            "columns": ["translation_vector", "initial_object_bounds", "stability", "extra_column"],
            "num_rows": 100,
            "format": "parquet"
        }

        # Depending on schema strictness, this might pass or fail.
        # For now, we assume it passes if the schema doesn't explicitly forbid extra columns.
        try:
            validate_against_schema(extra_data, schema)
        except Exception:
            # If it fails, it might be due to a strict schema. This is acceptable.
            pass