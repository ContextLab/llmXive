"""
Contract test for feature_set schema.
Implements test_feature_set_schema_validates_nan_values to assert that
feature vectors contain no NaN values.
"""

import pytest
import json
from pathlib import Path
import sys

# Add project root to path for imports if running standalone
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root / "code"))

from pathlib import Path
import yaml
import numpy as np


def load_schema(schema_path: Path) -> dict:
    """Load a YAML schema file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_feature_set(data: dict, schema: dict) -> list:
    """
    Validate a feature_set record against the schema.
    Returns a list of error messages.
    """
    errors = []

    # Check required fields
    required_fields = schema.get('required', [])
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {field}")

    # Check specific field types and constraints based on schema definition
    properties = schema.get('properties', {})

    if 'molecule_id' in properties and 'molecule_id' in data:
        if not isinstance(data['molecule_id'], str):
            errors.append("molecule_id must be a string")

    if 'features_2d' in properties and 'features_2d' in data:
        features_2d = data['features_2d']
        if not isinstance(features_2d, list):
            errors.append("features_2d must be a list")
        else:
            # Check for NaN values
            if any(np.isnan(float(f)) for f in features_2d if isinstance(f, (int, float))):
                errors.append("features_2d contains NaN values")

    if 'features_3d' in properties and 'features_3d' in data:
        features_3d = data['features_3d']
        if not isinstance(features_3d, list):
            errors.append("features_3d must be a list")
        else:
            # Check for NaN values
            if any(np.isnan(float(f)) for f in features_3d if isinstance(f, (int, float))):
                errors.append("features_3d contains NaN values")

    return errors


def test_feature_set_schema_validates_nan_values():
    """
    Assert that feature vectors contain no NaN values.
    This test loads the feature_set schema, creates test data with NaN values,
    and asserts that the validation catches them.
    """
    # Load the schema
    schema_path = Path(__file__).parent / "feature_set.schema.yaml"
    if not schema_path.exists():
        pytest.fail(f"Schema file not found: {schema_path}")

    schema = load_schema(schema_path)

    # Test case 1: Valid data without NaN
    valid_data = {
        "molecule_id": "test_mol_1",
        "features_2d": [1.0, 2.0, 3.0],
        "features_3d": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6]
    }
    errors = validate_feature_set(valid_data, schema)
    nan_errors = [e for e in errors if "NaN" in e]
    assert len(nan_errors) == 0, f"Valid data should not produce NaN errors: {nan_errors}"

    # Test case 2: Data with NaN in features_2d
    data_with_nan_2d = {
        "molecule_id": "test_mol_2",
        "features_2d": [1.0, float('nan'), 3.0],
        "features_3d": [0.1, 0.2, 0.3]
    }
    errors = validate_feature_set(data_with_nan_2d, schema)
    nan_errors = [e for e in errors if "NaN" in e]
    assert len(nan_errors) > 0, "Should detect NaN in features_2d"
    assert any("features_2d" in e for e in nan_errors), "Error message should specify features_2d"

    # Test case 3: Data with NaN in features_3d
    data_with_nan_3d = {
        "molecule_id": "test_mol_3",
        "features_2d": [1.0, 2.0],
        "features_3d": [0.1, float('nan'), 0.3]
    }
    errors = validate_feature_set(data_with_nan_3d, schema)
    nan_errors = [e for e in errors if "NaN" in e]
    assert len(nan_errors) > 0, "Should detect NaN in features_3d"
    assert any("features_3d" in e for e in nan_errors), "Error message should specify features_3d"

    # Test case 4: Data with NaN in both
    data_with_both_nan = {
        "molecule_id": "test_mol_4",
        "features_2d": [float('nan'), 2.0],
        "features_3d": [0.1, float('nan')]
    }
    errors = validate_feature_set(data_with_both_nan, schema)
    nan_errors = [e for e in errors if "NaN" in e]
    assert len(nan_errors) >= 2, "Should detect NaN in both features_2d and features_3d"