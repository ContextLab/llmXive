"""
Contract tests for schema definitions (T006).
Validates that the YAML schema files are syntactically correct
and can be loaded by the validation pipeline.
"""
import os
import yaml
import json
import pytest
from pathlib import Path
import jsonschema

# Get the project root (assumes running from project root)
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "specs" / "001-text-tone-emotional-support" / "contracts"


@pytest.fixture
def schema_files():
    """Return paths to all schema files."""
    return [
        CONTRACTS_DIR / "stimulus.schema.yaml",
        CONTRACTS_DIR / "rating.schema.yaml",
        CONTRACTS_DIR / "analysis_result.schema.yaml",
    ]


def test_schema_files_exist(schema_files):
    """Assert that all required schema files exist."""
    for schema_path in schema_files:
        assert schema_path.exists(), f"Schema file missing: {schema_path}"


def test_stimulus_schema_valid_syntax(schema_files):
    """Assert that the stimulus schema is valid YAML."""
    schema_path = CONTRACTS_DIR / "stimulus.schema.yaml"
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        assert schema is not None
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in stimulus schema: {e}")


def test_rating_schema_valid_syntax(schema_files):
    """Assert that the rating schema is valid YAML."""
    schema_path = CONTRACTS_DIR / "rating.schema.yaml"
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        assert schema is not None
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in rating schema: {e}")


def test_analysis_result_schema_valid_syntax(schema_files):
    """Assert that the analysis result schema is valid YAML."""
    schema_path = CONTRACTS_DIR / "analysis_result.schema.yaml"
    try:
        with open(schema_path, "r", encoding="utf-8") as f:
            schema = yaml.safe_load(f)
        assert schema is not None
        assert "$schema" in schema
        assert "type" in schema
        assert schema["type"] == "object"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in analysis result schema: {e}")


def test_stimulus_schema_compiles():
    """Assert that the stimulus schema can be compiled by jsonschema."""
    schema_path = CONTRACTS_DIR / "stimulus.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        pytest.fail(f"Invalid JSON schema: {e}")


def test_rating_schema_compiles():
    """Assert that the rating schema can be compiled by jsonschema."""
    schema_path = CONTRACTS_DIR / "rating.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        pytest.fail(f"Invalid JSON schema: {e}")


def test_analysis_result_schema_compiles():
    """Assert that the analysis result schema can be compiled by jsonschema."""
    schema_path = CONTRACTS_DIR / "analysis_result.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    try:
        jsonschema.Draft7Validator.check_schema(schema)
    except jsonschema.SchemaError as e:
        pytest.fail(f"Invalid JSON schema: {e}")


def test_stimulus_schema_has_required_fields():
    """Assert that the stimulus schema defines required fields."""
    schema_path = CONTRACTS_DIR / "stimulus.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert "required" in schema
    required = schema["required"]
    assert "stimulus_id" in required
    assert "text_content" in required
    assert "emoji_level" in required
    assert "punctuation_type" in required
    assert "length_category" in required
    assert "context_type" in required


def test_rating_schema_has_required_fields():
    """Assert that the rating schema defines required fields."""
    schema_path = CONTRACTS_DIR / "rating.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert "required" in schema
    required = schema["required"]
    assert "rating_id" in required
    assert "participant_id" in required
    assert "stimulus_id" in required
    assert "context_type" in required
    assert "support_rating" in required


def test_analysis_result_schema_has_required_fields():
    """Assert that the analysis result schema defines required fields."""
    schema_path = CONTRACTS_DIR / "analysis_result.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)
    assert "required" in schema
    required = schema["required"]
    assert "analysis_id" in required
    assert "model_formula" in required
    assert "fixed_effects" in required
    assert "random_effects" in required
    assert "p_values" in required
    assert "n_observations" in required
    assert "run_timestamp" in required


def test_stimulus_schema_validates_sample():
    """Assert that a valid stimulus instance passes validation."""
    schema_path = CONTRACTS_DIR / "stimulus.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    sample = {
        "stimulus_id": "S001",
        "text_content": "Hey, how are you doing?",
        "emoji_level": "none",
        "punctuation_type": "standard",
        "length_category": "short",
        "context_type": "friend",
        "created_at": "2024-01-01T12:00:00Z"
    }

    try:
        jsonschema.validate(instance=sample, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Valid sample failed validation: {e.message}")


def test_rating_schema_validates_sample():
    """Assert that a valid rating instance passes validation."""
    schema_path = CONTRACTS_DIR / "rating.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    sample = {
        "rating_id": "R000001",
        "participant_id": "P-ABCD1234",
        "stimulus_id": "S001",
        "context_type": "friend",
        "support_rating": 5,
        "timestamp": "2024-01-01T12:05:00Z"
    }

    try:
        jsonschema.validate(instance=sample, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Valid sample failed validation: {e.message}")


def test_analysis_result_schema_validates_sample():
    """Assert that a valid analysis result instance passes validation."""
    schema_path = CONTRACTS_DIR / "analysis_result.schema.yaml"
    with open(schema_path, "r", encoding="utf-8") as f:
        schema = yaml.safe_load(f)

    sample = {
        "analysis_id": "A0001",
        "model_formula": "support_rating ~ context_type * emoji_level + (1|participant_id) + (1|stimulus_id)",
        "fixed_effects": [
            {"term": "Intercept", "estimate": 4.2, "std_error": 0.15, "t_value": 28.0},
            {"term": "context_type[T.acquaintance]", "estimate": -0.5, "std_error": 0.12, "t_value": -4.16}
        ],
        "random_effects": {
            "participant": 0.25,
            "stimulus": 0.15,
            "residual": 1.5
        },
        "p_values": {
            "context_type": 0.001,
            "emoji_level": 0.03
        },
        "n_observations": 500,
        "n_participants": 50,
        "n_stimuli": 24,
        "run_timestamp": "2024-01-01T14:00:00Z"
    }

    try:
        jsonschema.validate(instance=sample, schema=schema)
    except jsonschema.ValidationError as e:
        pytest.fail(f"Valid sample failed validation: {e.message}")
