"""
Contract tests for model output schema.
"""
import pytest
import yaml
import json
from pathlib import Path
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from code.config import RESULTS_ROOT

def test_load_schema():
    """Test that the output schema YAML is valid and contains expected keys."""
    schema_path = Path("contracts/output.schema.yaml")
    assert schema_path.exists(), "Schema file missing"
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    assert 'expected_structure' in schema
    assert 'coefficients' in schema['expected_structure']
    assert 'p_values' in schema['expected_structure']
    assert 'vif_scores' in schema['expected_structure']
    assert 'diagnostics' in schema['expected_structure']
    assert 'interpretation' in schema['expected_structure']

def test_validate_json_keys():
    """Test that the regression summary JSON matches the schema."""
    schema_path = Path("contracts/output.schema.yaml")
    json_path = Path(f"{RESULTS_ROOT}/models/regression_summary.json")
    
    if not json_path.exists():
        pytest.skip("Regression summary JSON not found (expected if model hasn't run).")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    required_keys = schema['expected_structure'].keys()
    for key in required_keys:
        assert key in data, f"Missing key in JSON: {key}"
    
    # Check types
    assert isinstance(data.get('vif_scores'), dict), "vif_scores must be a dict"
    assert isinstance(data.get('interpretation'), str), "interpretation must be a string"
