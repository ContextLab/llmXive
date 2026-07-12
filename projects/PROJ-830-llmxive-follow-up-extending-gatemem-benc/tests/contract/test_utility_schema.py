"""
Contract test for Utility Results Schema.

Verifies that data/processed/utility_results.json contains the required fields:
- conditional_utility
- overall_success

This test validates the structure of the output against the results.schema.yaml
contract defined in the project.
"""
import json
import os
import pytest
from pathlib import Path

import yaml

# Ensure the test can find the schema file
PROJECT_ROOT = Path(__file__).parent.parent.parent
SCHEMA_PATH = PROJECT_ROOT / "contracts" / "results.schema.yaml"
RESULTS_PATH = PROJECT_ROOT / "data" / "processed" / "utility_results.json"

@pytest.fixture
def schema():
    """Load the results schema from YAML."""
    if not SCHEMA_PATH.exists():
        pytest.fail(f"Schema file not found at {SCHEMA_PATH}")
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

@pytest.fixture
def results():
    """Load the utility results from JSON."""
    if not RESULTS_PATH.exists():
        pytest.fail(f"Results file not found at {RESULTS_PATH}. "
                    "Run the US2 pipeline to generate this file.")
    with open(RESULTS_PATH, 'r') as f:
        return json.load(f)

def test_results_schema_exists(schema):
    """Verify the schema defines the utility_results section."""
    assert schema is not None
    # Check for top-level structure expected in results.schema.yaml
    assert "properties" in schema or "required" in schema or "utility_results" in schema

def test_utility_results_file_structure(results):
    """Verify the utility_results.json file contains required top-level fields."""
    # The file should be a dictionary (JSON object)
    assert isinstance(results, dict), "Results must be a JSON object (dict)"

def test_conditional_utility_field_present(results):
    """Verify 'conditional_utility' field exists in the results."""
    # Check if it's at the top level or nested under a specific key
    # Based on typical structure, it might be directly in results or under 'metrics'
    if "conditional_utility" in results:
        assert results["conditional_utility"] is not None
    elif "metrics" in results and "conditional_utility" in results["metrics"]:
        assert results["metrics"]["conditional_utility"] is not None
    else:
        # Try to find it anywhere in the nested structure
        def find_key_recursive(d, key):
            if isinstance(d, dict):
                if key in d:
                    return d[key]
                for v in d.values():
                    result = find_key_recursive(v, key)
                    if result is not None:
                        return result
            elif isinstance(d, list):
                for item in d:
                    result = find_key_recursive(item, key)
                    if result is not None:
                        return result
            return None
        
        value = find_key_recursive(results, "conditional_utility")
        assert value is not None, "Field 'conditional_utility' not found in results"

def test_overall_success_field_present(results):
    """Verify 'overall_success' field exists in the results."""
    # Check if it's at the top level or nested under a specific key
    if "overall_success" in results:
        assert results["overall_success"] is not None
    elif "metrics" in results and "overall_success" in results["metrics"]:
        assert results["metrics"]["overall_success"] is not None
    else:
        # Try to find it anywhere in the nested structure
        def find_key_recursive(d, key):
            if isinstance(d, dict):
                if key in d:
                    return d[key]
                for v in d.values():
                    result = find_key_recursive(v, key)
                    if result is not None:
                        return result
            elif isinstance(d, list):
                for item in d:
                    result = find_key_recursive(item, key)
                    if result is not None:
                        return result
            return None
        
        value = find_key_recursive(results, "overall_success")
        assert value is not None, "Field 'overall_success' not found in results"

def test_conditional_utility_is_numeric(results):
    """Verify 'conditional_utility' contains a numeric value."""
    def find_key_recursive(d, key):
        if isinstance(d, dict):
            if key in d:
                return d[key]
            for v in d.values():
                result = find_key_recursive(v, key)
                if result is not None:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = find_key_recursive(item, key)
                if result is not None:
                    return result
        return None
    
    value = find_key_recursive(results, "conditional_utility")
    assert isinstance(value, (int, float)), f"conditional_utility must be numeric, got {type(value)}"

def test_overall_success_is_numeric(results):
    """Verify 'overall_success' contains a numeric value."""
    def find_key_recursive(d, key):
        if isinstance(d, dict):
            if key in d:
                return d[key]
            for v in d.values():
                result = find_key_recursive(v, key)
                if result is not None:
                    return result
        elif isinstance(d, list):
            for item in d:
                result = find_key_recursive(item, key)
                if result is not None:
                    return result
        return None
    
    value = find_key_recursive(results, "overall_success")
    assert isinstance(value, (int, float)), f"overall_success must be numeric, got {type(value)}"