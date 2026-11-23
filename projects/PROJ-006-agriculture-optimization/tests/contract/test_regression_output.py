"""
Contract test skeleton for regression output (TDD).

This test validates that the regression results JSON conforms to the
expected output schema defined in contracts/output.schema.yaml.

Note: This test will fail until T025 is implemented.
"""
import json
import os
import tempfile
from pathlib import Path
import yaml
import pytest
import sys

# Add src to path for imports if not already present
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCHEMA_PATH = PROJECT_ROOT / "contracts" / "output.schema.yaml"
RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "regression_results.json"

def load_schema():
    if not SCHEMA_PATH.exists():
        pytest.skip(f"Schema file not found: {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def load_results():
    if not RESULTS_PATH.exists():
        pytest.skip(f"Results file not found: {RESULTS_PATH}")
    with open(RESULTS_PATH, 'r') as f:
        return json.load(f)

@pytest.mark.contract
def test_schema_file_exists():
    """Assert that the regression output schema exists."""
    assert SCHEMA_PATH.exists(), f"Schema file missing: {SCHEMA_PATH}"

@pytest.mark.contract
def test_schema_is_valid_yaml():
    """Assert that the schema file is valid YAML."""
    try:
        schema = load_schema()
        assert isinstance(schema, dict), "Schema must be a dictionary"
    except yaml.YAMLError as e:
        pytest.fail(f"Invalid YAML in schema: {e}")

@pytest.mark.contract
def test_results_file_exists():
    """Assert that the regression results file exists."""
    assert RESULTS_PATH.exists(), f"Results file missing: {RESULTS_PATH}"

@pytest.mark.contract
def test_results_has_required_fields():
    """Assert that results contain required top-level fields."""
    results = load_results()
    required = ['coefficients', 'p_values', 'vif_scores', 'model_type']
    missing = [k for k in required if k not in results]
    assert not missing, f"Results missing required fields: {missing}"

@pytest.mark.contract
def test_results_validates_against_schema():
    """Assert that results match the schema structure."""
    schema = load_schema()
    results = load_results()
    
    # Basic structural check
    if 'properties' in schema:
        for key in schema['properties']:
            assert key in results, f"Missing key in results: {key}"
