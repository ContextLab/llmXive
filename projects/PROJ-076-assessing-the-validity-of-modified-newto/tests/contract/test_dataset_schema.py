"""
Contract test for the parsed galaxy dataset schema.

This module validates that the parsed galaxy data conforms to the schema
defined in `contracts/dataset.schema.yaml`. It ensures that all required
fields are present, types are correct, and constraints (like non-negative
values for physical quantities) are met.

Dependencies:
  - contracts/dataset.schema.yaml (generated in T004c)
  - code/preprocess.py (for potential data loading, though this test uses fixtures)
"""

import os
import sys
import yaml
import pytest
from pathlib import Path
from typing import Any, Dict, List

import pandas as pd
import numpy as np

# Add project root to path to allow imports if running from tests/
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

SCHEMA_PATH = project_root / "contracts" / "dataset.schema.yaml"
FIXTURES_DIR = project_root / "tests" / "fixtures"


def load_schema() -> Dict[str, Any]:
    """Load the dataset schema from the YAML file."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}. "
                    "Ensure T004c (Generate schema) has been completed.")
    with open(SCHEMA_PATH, "r") as f:
        return yaml.safe_load(f)


def get_field_schema(schema: Dict[str, Any], field_name: str) -> Dict[str, Any]:
    """Retrieve the schema definition for a specific field."""
    properties = schema.get("properties", {})
    if field_name not in properties:
        pytest.fail(f"Field '{field_name}' not found in schema properties.")
    return properties[field_name]


def validate_type(value: Any, expected_type: str) -> bool:
    """Validate that a value matches the expected JSON Schema type."""
    if expected_type == "number":
        return isinstance(value, (int, float, np.number)) and not isinstance(value, bool)
    elif expected_type == "integer":
        return isinstance(value, (int, np.integer)) and not isinstance(value, bool)
    elif expected_type == "string":
        return isinstance(value, str)
    elif expected_type == "boolean":
        return isinstance(value, bool)
    elif expected_type == "array":
        return isinstance(value, (list, np.ndarray))
    elif expected_type == "object":
        return isinstance(value, dict)
    return False


def validate_constraints(value: Any, field_schema: Dict[str, Any]) -> List[str]:
    """Validate value against constraints defined in the schema."""
    errors = []
    field_name = field_schema.get("name", "unknown")

    # Check minimum
    if "minimum" in field_schema:
        if isinstance(value, (int, float, np.number)) and value < field_schema["minimum"]:
            errors.append(f"{field_name} value {value} is less than minimum {field_schema['minimum']}")

    # Check maximum
    if "maximum" in field_schema:
        if isinstance(value, (int, float, np.number)) and value > field_schema["maximum"]:
            errors.append(f"{field_name} value {value} is greater than maximum {field_schema['maximum']}")

    # Check pattern (for strings)
    if "pattern" in field_schema and isinstance(value, str):
        import re
        if not re.match(field_schema["pattern"], value):
            errors.append(f"{field_name} value '{value}' does not match pattern '{field_schema['pattern']}'")

    # Check unique_items (for arrays/lists)
    if field_schema.get("uniqueItems") and isinstance(value, (list, np.ndarray)):
        if len(value) != len(set(value)):
            errors.append(f"{field_name} array contains duplicate items")

    return errors


@pytest.fixture
def sample_galaxy_data() -> pd.DataFrame:
    """
    Fixture providing a valid sample DataFrame conforming to the schema.
    This data is manually constructed to ensure all required fields and types are present.
    """
    # Based on typical SPARC data structure inferred from the schema
    data = {
        "galaxy_name": ["NGC3198", "NGC2403", "NGC6509"],
        "ra": [158.94, 111.06, 189.45],
        "dec": [45.83, 65.70, 45.12],
        "distance_mpc": [9.4, 3.2, 14.0],
        "inclination_deg": [70.0, 55.0, 60.0],
        "inclination_uncertainty": [2.0, 1.5, 3.0],
        "hubble_type": ["Sc", "Scd", "SBb"],
        "radial_distance_kpc": [
            [0.1, 0.2, 0.3, 0.4, 0.5],
            [0.15, 0.25, 0.35, 0.45],
            [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
        ],
        "velocity_kms": [
            [100.0, 150.0, 180.0, 190.0, 195.0],
            [80.0, 120.0, 140.0, 145.0],
            [110.0, 160.0, 190.0, 200.0, 205.0, 208.0]
        ],
        "velocity_uncertainty": [
            [5.0, 5.0, 5.0, 5.0, 5.0],
            [3.0, 3.0, 3.0, 3.0],
            [4.0, 4.0, 4.0, 4.0, 4.0, 4.0]
        ],
        "surface_brightness": [21.5, 22.1, 20.8],
        "stellar_mass_sun": [4.5e9, 1.2e9, 6.0e9],
        "gas_mass_sun": [0.8e9, 0.3e9, 1.1e9],
        "total_mass_sun": [5.3e9, 1.5e9, 7.1e9],
        "data_source": ["SPARC", "SPARC", "SPARC"],
        "processed_timestamp": ["2026-01-01T00:00:00Z"] * 3
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_data_missing_field() -> pd.DataFrame:
    """Fixture with a missing required field."""
    data = {
        "galaxy_name": ["NGC3198"],
        "ra": [158.94],
        # Missing 'dec' which is required
        "distance_mpc": [9.4],
        "inclination_deg": [70.0],
        "inclination_uncertainty": [2.0],
        "hubble_type": ["Sc"],
        "radial_distance_kpc": [[0.1, 0.2]],
        "velocity_kms": [[100.0, 150.0]],
        "velocity_uncertainty": [[5.0, 5.0]],
        "surface_brightness": [21.5],
        "stellar_mass_sun": [4.5e9],
        "gas_mass_sun": [0.8e9],
        "total_mass_sun": [5.3e9],
        "data_source": ["SPARC"],
        "processed_timestamp": ["2026-01-01T00:00:00Z"]
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_data_wrong_type() -> pd.DataFrame:
    """Fixture with a field having the wrong type."""
    data = {
        "galaxy_name": ["NGC3198"],
        "ra": [158.94],
        "dec": [45.83],
        "distance_mpc": [9.4],
        "inclination_deg": [70.0],
        "inclination_uncertainty": [2.0],
        "hubble_type": ["Sc"],
        "radial_distance_kpc": [[0.1, 0.2]],
        "velocity_kms": [[100.0, 150.0]],
        "velocity_uncertainty": [[5.0, 5.0]],
        "surface_brightness": [21.5],
        "stellar_mass_sun": [4.5e9],
        "gas_mass_sun": [0.8e9],
        "total_mass_sun": [5.3e9],
        "data_source": ["SPARC"],
        "processed_timestamp": [12345] # Wrong type: integer instead of string
    }
    return pd.DataFrame(data)


@pytest.fixture
def invalid_data_constraint_violation() -> pd.DataFrame:
    """Fixture with a constraint violation (negative velocity)."""
    data = {
        "galaxy_name": ["NGC3198"],
        "ra": [158.94],
        "dec": [45.83],
        "distance_mpc": [9.4],
        "inclination_deg": [70.0],
        "inclination_uncertainty": [2.0],
        "hubble_type": ["Sc"],
        "radial_distance_kpc": [[0.1, 0.2]],
        "velocity_kms": [[-100.0, 150.0]], # Negative velocity
        "velocity_uncertainty": [[5.0, 5.0]],
        "surface_brightness": [21.5],
        "stellar_mass_sun": [4.5e9],
        "gas_mass_sun": [0.8e9],
        "total_mass_sun": [5.3e9],
        "data_source": ["SPARC"],
        "processed_timestamp": ["2026-01-01T00:00:00Z"]
    }
    return pd.DataFrame(data)


class TestDatasetSchema:
    """
    Contract tests for the parsed galaxy dataset schema.
    These tests ensure that the data produced by the pipeline adheres to the
    schema defined in contracts/dataset.schema.yaml.
    """

    def test_schema_file_exists(self):
        """Verify that the schema file exists."""
        assert SCHEMA_PATH.exists(), f"Schema file {SCHEMA_PATH} does not exist."

    def test_schema_is_valid_yaml(self):
        """Verify that the schema file is valid YAML."""
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary."
        assert "properties" in schema, "Schema must contain 'properties'."

    @pytest.mark.parametrize("field_name", [
        "galaxy_name", "ra", "dec", "distance_mpc", "inclination_deg",
        "inclination_uncertainty", "hubble_type", "radial_distance_kpc",
        "velocity_kms", "velocity_uncertainty", "surface_brightness",
        "stellar_mass_sun", "gas_mass_sun", "total_mass_sun", "data_source",
        "processed_timestamp"
    ])
    def test_required_fields_present(self, sample_galaxy_data, field_name):
        """Verify that all required fields defined in the schema are present in the data."""
        schema = load_schema()
        # Check if field is required in schema
        required_fields = schema.get("required", [])
        if field_name in required_fields:
            assert field_name in sample_galaxy_data.columns, \
                f"Required field '{field_name}' is missing from DataFrame."

    def test_field_types_correct(self, sample_galaxy_data):
        """Verify that each field has the correct type as per schema."""
        schema = load_schema()
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            if field_name not in sample_galaxy_data.columns:
                continue # Skip if not present (though required check should catch this)

            expected_type = field_schema.get("type")
            if not expected_type:
                continue

            # Check a sample value (first row)
            # Handle list columns (like radial_distance_kpc) differently if needed
            sample_val = sample_galaxy_data[field_name].iloc[0]

            # Special handling for array types which are lists of numbers
            if expected_type == "array":
                assert isinstance(sample_val, (list, np.ndarray)), \
                    f"Field '{field_name}' should be an array, got {type(sample_val)}"
            else:
                assert validate_type(sample_val, expected_type), \
                    f"Field '{field_name}' expected type {expected_type}, got {type(sample_val)}"

    def test_constraints_valid(self, sample_galaxy_data):
        """Verify that values satisfy schema constraints."""
        schema = load_schema()
        properties = schema.get("properties", {})

        for field_name, field_schema in properties.items():
            if field_name not in sample_galaxy_data.columns:
                continue

            values = sample_galaxy_data[field_name].tolist()
            for val in values:
                # If it's a list (array field), check elements
                if isinstance(val, (list, np.ndarray)):
                    for elem in val:
                        errors = validate_constraints(elem, field_schema)
                        assert not errors, f"Constraint error in {field_name}: {errors}"
                else:
                    errors = validate_constraints(val, field_schema)
                    assert not errors, f"Constraint error in {field_name}: {errors}"

    def test_missing_field_fails_validation(self, invalid_data_missing_field):
        """Verify that data missing a required field fails schema validation."""
        schema = load_schema()
        required = schema.get("required", [])
        # We expect 'dec' to be required and missing in the fixture
        missing_required = [f for f in required if f not in invalid_data_missing_field.columns]
        assert len(missing_required) > 0, "Test fixture did not miss any required fields."

    def test_wrong_type_fails_validation(self, invalid_data_wrong_type):
        """Verify that data with wrong types fails validation logic."""
        # This test ensures the validation logic catches type errors
        # We simulate the check here
        schema = load_schema()
        props = schema.get("properties", {})
        ts_schema = props.get("processed_timestamp", {})
        expected_type = ts_schema.get("type")

        val = invalid_data_wrong_type["processed_timestamp"].iloc[0]
        assert not validate_type(val, expected_type), \
            "Validation logic failed to detect wrong type in fixture."

    def test_constraint_violation_fails_validation(self, invalid_data_constraint_violation):
        """Verify that data violating constraints fails validation logic."""
        schema = load_schema()
        props = schema.get("properties", {})
        vel_schema = props.get("velocity_kms", {})
        # velocity_kms is an array of numbers, check constraints on elements
        # The fixture has a negative value, which should violate 'minimum': 0

        # We need to check the inner elements
        val_list = invalid_data_constraint_violation["velocity_kms"].iloc[0]
        for val in val_list:
            errors = validate_constraints(val, vel_schema)
            # We expect at least one error for the negative value
            if val < 0:
                assert len(errors) > 0, "Validation logic failed to catch negative velocity."