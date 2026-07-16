"""
Contract test for dataset schema validation.

This task validates the existence and structure of the schema files
(T004a, T004b, T005a), NOT the validation logic implementation (T012).

It ensures that:
1. The schema file exists at the expected path.
2. The schema is valid YAML.
3. The schema contains required top-level keys: 'predictors' and 'outcomes'.
4. The schema structure matches the expected contract (lists of variables with names).
"""

import os
import yaml
import pytest
from pathlib import Path

# Project root relative to this test file
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "specs" / "001-gut-microbiome-sleep-architecture" / "contracts" / "dataset.schema.yaml"

def test_schema_file_exists():
    """Assert that the dataset schema file exists."""
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}"

def test_schema_is_valid_yaml():
    """Assert that the schema file is valid YAML and can be parsed."""
    try:
        with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        assert schema is not None, "Schema file is empty or invalid YAML"
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")

def test_schema_has_required_top_level_keys():
    """Assert that the schema contains 'predictors' and 'outcomes' keys."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    assert 'predictors' in schema, "Schema missing 'predictors' key"
    assert 'outcomes' in schema, "Schema missing 'outcomes' key"

def test_predictors_structure():
    """Assert that 'predictors' is a list of dicts with 'name' keys."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    predictors = schema['predictors']
    assert isinstance(predictors, list), "'predictors' must be a list"
    assert len(predictors) > 0, "'predictors' list must not be empty"

    for item in predictors:
        assert isinstance(item, dict), "Each predictor must be a dictionary"
        assert 'name' in item, "Each predictor must have a 'name' key"
        assert isinstance(item['name'], str), "'name' must be a string"

def test_outcomes_structure():
    """Assert that 'outcomes' is a list of dicts with 'name' keys."""
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    outcomes = schema['outcomes']
    assert isinstance(outcomes, list), "'outcomes' must be a list"
    assert len(outcomes) > 0, "'outcomes' list must not be empty"

    for item in outcomes:
        assert isinstance(item, dict), "Each outcome must be a dictionary"
        assert 'name' in item, "Each outcome must have a 'name' key"
        assert isinstance(item['name'], str), "'name' must be a string"

def test_schema_contains_expected_variables():
    """
    Assert that the schema contains specific expected variables
    mentioned in the project description (e.g., 'SWS duration').
    This ensures the schema is not just structurally valid but semantically relevant.
    """
    with open(SCHEMA_PATH, 'r', encoding='utf-8') as f:
        schema = yaml.safe_load(f)

    predictor_names = [p['name'] for p in schema['predictors']]
    outcome_names = [o['name'] for o in schema['outcomes']]

    # Check for a known sleep metric
    assert 'SWS duration' in outcome_names, "Expected outcome 'SWS duration' not found in schema"

    # Check for at least one gut microbiome taxon (commonly Bacteroides or similar)
    # We check if any name contains 'Bacteroides' or 'Firmicutes' as a heuristic for taxa presence
    taxa_found = any('Bacteroides' in name or 'Firmicutes' in name or 'Prevotella' in name for name in predictor_names)
    assert taxa_found, "Expected at least one gut microbiome taxon (e.g., Bacteroides, Firmicutes) in predictors"