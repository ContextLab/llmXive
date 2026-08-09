"""
Unit tests for the output validation logic (T022).
Tests verify that the validation script correctly identifies valid and invalid data structures.
"""
import json
import os
import tempfile
from pathlib import Path
from datetime import datetime

import pytest
import yaml
from jsonschema import ValidationError

# Import the validation logic
# We need to mock the config paths or set up a temporary structure
from unittest.mock import patch, MagicMock

# Import the main validation function logic
# Since the script is a CLI, we test the helper functions if we refactor,
# or we test the behavior via the main entry point with mocks.
# Here we test the core validation logic by importing the helpers if possible,
# or by simulating the environment.

# To avoid circular imports or config dependency issues in unit tests,
# we will test the schema structure and the jsonschema validation behavior directly.

SCHEMA_CONTENT = """
type: object
required:
  - metadata
  - data
properties:
  metadata:
    type: object
    required:
      - schema_version
      - generated_at
      - source_ecosystems
      - total_pairs
      - positive_pairs
      - negative_pairs
      - feature_columns
    properties:
      schema_version:
        type: string
        pattern: "^\\\\d+\\\\.\\\\d+\\\\.\\\\d+$"
      generated_at:
        type: string
        format: date-time
      source_ecosystems:
        type: array
        items:
          type: string
        minItems: 1
      total_pairs:
        type: integer
        minimum: 1
      positive_pairs:
        type: integer
        minimum: 0
      negative_pairs:
        type: integer
        minimum: 0
      feature_columns:
        type: array
        items:
          type: string
        minItems: 1
      label_column:
        type: string
        const: "link_label"
  data:
    type: array
    items:
      type: object
      required:
        - plant_species
        - pollinator_species
        - ecosystem_id
        - link_label
        - traits
      properties:
        plant_species:
          type: string
        pollinator_species:
          type: string
        ecosystem_id:
          type: string
        link_label:
          type: integer
          enum: [0, 1]
        traits:
          type: object
          minProperties: 1
additionalProperties: false
"""

@pytest.fixture
def valid_schema():
    return yaml.safe_load(SCHEMA_CONTENT)

@pytest.fixture
def valid_data():
    return {
        "metadata": {
            "schema_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_ecosystems": ["ecosystem_1"],
            "total_pairs": 2,
            "positive_pairs": 1,
            "negative_pairs": 1,
            "feature_columns": ["trait_a", "trait_b"],
            "label_column": "link_label"
        },
        "data": [
            {
                "plant_species": "PlantA",
                "pollinator_species": "PollinatorA",
                "ecosystem_id": "ecosystem_1",
                "link_label": 1,
                "traits": {"trait_a": 1.0, "trait_b": 2.0}
            },
            {
                "plant_species": "PlantB",
                "pollinator_species": "PollinatorB",
                "ecosystem_id": "ecosystem_1",
                "link_label": 0,
                "traits": {"trait_a": 0.5, "trait_b": 1.5}
            }
        ]
    }

@pytest.fixture
def invalid_data_missing_metadata():
    return {
        "data": []
    }

@pytest.fixture
def invalid_data_bad_label():
    return {
        "metadata": {
            "schema_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_ecosystems": ["ecosystem_1"],
            "total_pairs": 1,
            "positive_pairs": 1,
            "negative_pairs": 0,
            "feature_columns": ["trait_a"],
            "label_column": "link_label"
        },
        "data": [
            {
                "plant_species": "PlantA",
                "pollinator_species": "PollinatorA",
                "ecosystem_id": "ecosystem_1",
                "link_label": 2, # Invalid: must be 0 or 1
                "traits": {"trait_a": 1.0}
            }
        ]
    }

@pytest.fixture
def invalid_data_missing_required_field():
    return {
        "metadata": {
            "schema_version": "1.0.0",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_ecosystems": ["ecosystem_1"],
            "total_pairs": 1,
            "positive_pairs": 1,
            "negative_pairs": 0,
            "feature_columns": ["trait_a"],
            "label_column": "link_label"
        },
        "data": [
            {
                "plant_species": "PlantA",
                "pollinator_species": "PollinatorA",
                "ecosystem_id": "ecosystem_1",
                "traits": {"trait_a": 1.0}
                # Missing link_label
            }
        ]
    }

def test_valid_data_passes_validation(valid_schema, valid_data):
    from jsonschema import validate
    try:
        validate(instance=valid_data, schema=valid_schema)
        assert True
    except ValidationError as e:
        pytest.fail(f"Valid data failed validation: {e.message}")

def test_missing_metadata_fails(valid_schema, invalid_data_missing_metadata):
    from jsonschema import validate
    with pytest.raises(ValidationError):
        validate(instance=invalid_data_missing_metadata, schema=valid_schema)

def test_invalid_label_fails(valid_schema, invalid_data_bad_label):
    from jsonschema import validate
    with pytest.raises(ValidationError):
        validate(instance=invalid_data_bad_label, schema=valid_schema)

def test_missing_required_field_fails(valid_schema, invalid_data_missing_required_field):
    from jsonschema import validate
    with pytest.raises(ValidationError):
        validate(instance=invalid_data_missing_required_field, schema=valid_schema)

def test_schema_version_pattern_valid(valid_schema):
    data = {
        "metadata": {
            "schema_version": "2.1.3",
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_ecosystems": ["e1"],
            "total_pairs": 1,
            "positive_pairs": 1,
            "negative_pairs": 0,
            "feature_columns": ["f1"],
            "label_column": "link_label"
        },
        "data": [{"plant_species": "p1", "pollinator_species": "p2", "ecosystem_id": "e1", "link_label": 1, "traits": {"f1": 1}}]
    }
    from jsonschema import validate
    try:
        validate(instance=data, schema=valid_schema)
        assert True
    except ValidationError as e:
        pytest.fail(f"Valid version format failed: {e.message}")

def test_schema_version_pattern_invalid(valid_schema):
    data = {
        "metadata": {
            "schema_version": "v1.0", # Invalid format
            "generated_at": datetime.utcnow().isoformat() + "Z",
            "source_ecosystems": ["e1"],
            "total_pairs": 1,
            "positive_pairs": 1,
            "negative_pairs": 0,
            "feature_columns": ["f1"],
            "label_column": "link_label"
        },
        "data": [{"plant_species": "p1", "pollinator_species": "p2", "ecosystem_id": "e1", "link_label": 1, "traits": {"f1": 1}}]
    }
    from jsonschema import validate
    with pytest.raises(ValidationError):
        validate(instance=data, schema=valid_schema)