import json
import pytest
from pathlib import Path
import yaml
from jsonschema import validate, ValidationError
import os

@pytest.fixture
def schema_path():
    return Path("contracts/results_schema.yaml")

@pytest.fixture
def results_path():
    return Path("results/stats.json")

def test_results_schema_valid(schema_path, results_path):
    """Contract test: Verify results/stats.json matches results_schema.yaml."""
    if not results_path.exists():
        pytest.skip("results/stats.json not found. Run the analysis first.")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    with open(results_path, 'r') as f:
        data = json.load(f)
    
    # Validate
    try:
        validate(instance=data, schema=schema)
    except ValidationError as e:
        pytest.fail(f"Schema validation failed: {e.message}")
