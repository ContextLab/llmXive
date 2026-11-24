"""
Unit tests for the contract validator utility.
Ensures that `validate_schema` correctly validates data against the
JSON schemas defined in the contracts directory.
"""

import json
from pathlib import Path

import pytest

# Import the validator from the utils package
from utils.contract_validator import validate_schema

# Helper to load a schema file from the contracts directory
def load_schema(schema_name: str) -> Path:
    """
    Returns the Path to a schema file located under the contracts directory.

    Parameters
    ----------
    schema_name : str
        Filename of the schema (e.g., "dataset.schema.yaml").

    Returns
    -------
    Path
        Absolute path to the requested schema file.
    """
    # The contracts are stored under the specs folder as per the project layout
    return Path("specs/001-quantifying-the-impact-of-dataset-sparsity") / "contracts" / schema_name

# Sample data that conforms to the dataset schema
SAMPLE_DATASET_ENTRY = {
    "material_id": "mp-1234",
    "composition": "Fe2O3",
    "formation_energy_per_atom": -1.234,
    "elemental_descriptors": {
        "avg_atomic_number": 26.0,
        "avg_electronegativity": 1.83,
        "avg_atomic_radius": 1.40
    },
    "is_in_test_set": False
}

# Sample data that conforms to the metrics schema
SAMPLE_METRICS_ENTRY = {
    "subset_id": "sparsity_10pct_seed42",
    "model_type": "GPR",
    "metric_name": "RMSE",
    "value": 0.123,
    "sparsity_level": 10.0,
    "seed": 42
}

@pytest.mark.parametrize(
    "data, schema_file, expected",
    [
        (SAMPLE_DATASET_ENTRY, "dataset.schema.yaml", True),
        (SAMPLE_METRICS_ENTRY, "metrics.schema.yaml", True),
    ],
)
def test_validate_schema_success(data, schema_file, expected):
    """
    Verify that valid data passes schema validation.
    """
    schema_path = load_schema(schema_file)
    # The function should return True for valid data
    assert validate_schema(data, str(schema_path)) is expected

def test_validate_schema_missing_file():
    """
    Ensure that a FileNotFoundError is raised when the schema file does not exist.
    """
    missing_path = Path("nonexistent", "schema.yaml")
    with pytest.raises(FileNotFoundError):
        validate_schema({}, str(missing_path))

def test_validate_schema_invalid_data():
    """
    Provide data that violates the schema and confirm that validation returns False.
    """
    # Remove a required field from the dataset entry
    invalid_data = {
        "material_id": "mp-1234",
        "composition": "Fe2O3",
        # "formation_energy_per_atom" is omitted intentionally
        "elemental_descriptors": {
            "avg_atomic_number": 26.0,
            "avg_electronegativity": 1.83,
            "avg_atomic_radius": 1.40
        },
        "is_in_test_set": False
    }
    schema_path = load_schema("dataset.schema.yaml")
    assert validate_schema(invalid_data, str(schema_path)) is False