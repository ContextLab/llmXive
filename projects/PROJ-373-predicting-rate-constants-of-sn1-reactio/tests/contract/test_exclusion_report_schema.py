"""
Contract tests for exclusion_report schema validation.
Verifies that exclusion reports conform to specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml
"""
import os
import yaml
import pytest
from pathlib import Path
from jsonschema import validate, ValidationError

PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-predict-sn1-rate-constants" / "contracts" / "exclusion_report.schema.yaml"

@pytest.fixture
def schema():
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def valid_exclusion():
    return {
        "row_index": 42,
        "reason": "parsing_error",
        "original_smiles": "CC(C)(C)Br"
    }

def test_schema_exists():
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_valid_exclusion_conforms(schema, valid_exclusion):
    try:
        validate(instance=valid_exclusion, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Valid exclusion failed schema validation: {e.message}")

def test_invalid_reason_raises(schema):
    invalid_exclusion = {
        "row_index": 42,
        "reason": "unknown_reason",  # Invalid enum
        "original_smiles": "CC(C)(C)Br"
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_exclusion, schema=schema)

def test_missing_original_smiles_raises(schema):
    invalid_exclusion = {
        "row_index": 42,
        "reason": "missing_rate"
        # Missing original_smiles
    }
    with pytest.raises(ValidationError):
        validate(instance=invalid_exclusion, schema=schema)
