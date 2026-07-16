"""
Unit tests for contract validation.
Validates that drift scoring outputs strictly adhere to the defined schema.
"""

import json
import yaml
import os
import sys
import pytest

# Add parent directory to path to import utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'code'))

from utils import load_schema, validate_against_schema

def test_drift_score_schema_matches_drift_result_yaml():
    """
    Contract test for drift_scoring.py output schema.
    Validates that a sample output record matches the schema defined in
    contracts/drift_result.schema.yaml.
    """
    # Determine the project root relative to this test file
    # Project root is 3 levels up from tests/unit/test_contracts.py
    project_root = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    )
    
    schema_path = os.path.join(project_root, "contracts", "drift_result.schema.yaml")
    
    # 1. Verify schema file exists
    assert os.path.exists(schema_path), f"Schema file missing at {schema_path}"

    # 2. Load the schema
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)

    # 3. Verify schema structure (basic sanity check)
    assert 'required' in schema, "Schema must have a 'required' field"
    required_fields = schema['required']
    assert 'log_id' in required_fields, "Schema requires 'log_id'"
    assert 'drift_score' in required_fields, "Schema requires 'drift_score'"
    assert 'review_flag' in required_fields, "Schema requires 'review_flag'"

    # 4. Create a valid sample record that mimics drift_scoring.py output
    valid_record = {
        "log_id": "log_12345",
        "drift_score": 0.85,
        "review_flag": True
    }

    # 5. Validate the record against the schema
    # We use the validate_against_schema helper from utils.py
    try:
        validate_against_schema(valid_record, schema)
        is_valid = True
    except ValueError as e:
        is_valid = False
        error_msg = str(e)
    
    assert is_valid, f"Valid record failed schema validation: {error_msg if not is_valid else 'Unknown error'}"

    # 6. Test invalid record (missing required field) to ensure schema is strict
    invalid_record = {
        "log_id": "log_12345",
        # drift_score missing
        "review_flag": True
    }

    try:
        validate_against_schema(invalid_record, schema)
        should_fail = False
    except ValueError:
        should_fail = True

    assert should_fail, "Invalid record (missing required field) should have failed validation"

    # 7. Test invalid record (wrong type)
    invalid_type_record = {
        "log_id": "log_12345",
        "drift_score": "not_a_number",
        "review_flag": True
    }

    try:
        validate_against_schema(invalid_type_record, schema)
        should_fail_type = False
    except ValueError:
        should_fail_type = True

    assert should_fail_type, "Invalid record (wrong type) should have failed validation"