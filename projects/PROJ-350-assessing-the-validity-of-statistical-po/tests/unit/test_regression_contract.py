"""
Contract test for regression results output.

Verifies that `data/derived/regression_results.json` adheres to the
expected schema defined in `specs/contracts/regression_results.schema.yaml`.
"""
import json
import os
import sys
from pathlib import Path

import pytest
import yaml
from jsonschema import validate, ValidationError

# Ensure code directory is in path for imports if running standalone
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from validate_contracts import load_schema, load_data, validate_file_against_schema

SCHEMA_PATH = project_root / "specs" / "contracts" / "regression_results.schema.yaml"
DATA_PATH = project_root / "data" / "derived" / "regression_results.json"

@pytest.fixture(scope="module")
def schema():
    """Load the regression results schema."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found: {SCHEMA_PATH}. "
                    "Ensure T030 implementation creates this schema or it exists from prior steps.")
    return load_schema(SCHEMA_PATH)

@pytest.fixture(scope="module")
def data():
    """Load the regression results data."""
    if not DATA_PATH.exists():
        pytest.fail(f"Data file not found: {DATA_PATH}. "
                    "Ensure the regression pipeline (T031-T036) has been executed to generate this file.")
    return load_data(DATA_PATH)

def test_regression_results_schema_compliance(schema, data):
    """
    Contract Test: Verify data structure matches the schema.
    
    This test ensures that the output of the regression pipeline (T036)
    strictly follows the defined contract in the schema file.
    """
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Data validation failed against schema: {e.message} "
                    f"at path: {'/'.join(str(p) for p in e.path)}")

def test_regression_results_has_required_fields(data):
    """
    Contract Test: Verify top-level required keys exist.
    
    Checks for the presence of 'model_summary', 'coefficients', 'vif_diagnostics',
    and 'metadata' keys as per the schema definition.
    """
    required_keys = ["model_summary", "coefficients", "vif_diagnostics", "metadata"]
    missing = [k for k in required_keys if k not in data]
    
    if missing:
        pytest.fail(f"Missing required top-level keys in regression_results.json: {missing}")

def test_regression_results_coefficients_structure(data):
    """
    Contract Test: Verify coefficients list structure.
    
    Ensures each coefficient entry has 'term', 'estimate', 'std_err', 'p_value',
    and 'conf_int' keys.
    """
    if "coefficients" not in data:
        pytest.skip("Coefficients key missing, covered by schema test.")

    if not isinstance(data["coefficients"], list):
        pytest.fail("coefficients must be a list.")

    if len(data["coefficients"]) == 0:
        pytest.fail("coefficients list is empty. At least an intercept should be present.")

    required_field_keys = {"term", "estimate", "std_err", "p_value", "conf_int"}
    
    for i, row in enumerate(data["coefficients"]):
        missing = required_field_keys - set(row.keys())
        if missing:
            pytest.fail(f"Coefficient entry {i} missing keys: {missing}. "
                        f"Found keys: {list(row.keys())}")

def test_regression_results_vif_structure(data):
    """
    Contract Test: Verify VIF diagnostics structure.
    
    Ensures VIF entries have 'term' and 'vif_factor' keys.
    """
    if "vif_diagnostics" not in data:
        pytest.skip("VIF diagnostics key missing, covered by schema test.")

    if not isinstance(data["vif_diagnostics"], list):
        pytest.fail("vif_diagnostics must be a list.")

    required_vif_keys = {"term", "vif_factor"}
    
    for i, row in enumerate(data["vif_diagnostics"]):
        missing = required_vif_keys - set(row.keys())
        if missing:
            pytest.fail(f"VIF entry {i} missing keys: {missing}. "
                        f"Found keys: {list(row.keys())}")
