"""
Contract tests for analysis output schema validation.
Validates that results/statistics/statistics.json and other analysis outputs
conform to the schema defined in specs/001-visual-distraction-cognitive-control/contracts/analysis_output.schema.yaml
"""
import os
import json
import csv
import pytest
import yaml
from typing import Dict, Any, List

# Paths relative to project root
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
SCHEMA_PATH = os.path.join(
    PROJECT_ROOT,
    "specs", "001-visual-distraction-cognitive-control", "contracts", "analysis_output.schema.yaml"
)
STATISTICS_JSON_PATH = os.path.join(PROJECT_ROOT, "results", "statistics", "statistics.json")
VIF_REPORT_PATH = os.path.join(PROJECT_ROOT, "results", "statistics", "vif_report.json")
MULTIPLICITY_TABLE_PATH = os.path.join(PROJECT_ROOT, "results", "statistics", "multiplicity_table.csv")
BOOTSTRAP_RESULTS_PATH = os.path.join(PROJECT_ROOT, "results", "sensitivity", "bootstrap_results.json")
BINNING_RESULTS_PATH = os.path.join(PROJECT_ROOT, "results", "sensitivity", "binning_results.csv")


def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the YAML schema definition."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


def validate_json_against_schema(json_path: str, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a JSON file against the provided schema.
    Returns a list of validation errors (empty if valid).
    """
    errors = []

    if not os.path.exists(json_path):
        errors.append(f"File not found: {json_path}")
        return errors

    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {json_path}: {e}")
        return errors

    # Check top-level required keys
    required_keys = schema.get('required_keys', [])
    if isinstance(data, dict):
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required key: {key}")
    else:
        # If schema expects a list but got something else
        if schema.get('type') == 'list' and not isinstance(data, list):
             errors.append(f"Expected list at top level, got {type(data)}")

    # Check structure of specific keys if defined
    key_definitions = schema.get('key_definitions', {})
    for key, definition in key_definitions.items():
        if key in data:
            value = data[key]
            expected_type = definition.get('type')
            
            if expected_type == 'object' and not isinstance(value, dict):
                errors.append(f"Key '{key}' should be an object, got {type(value)}")
            elif expected_type == 'list' and not isinstance(value, list):
                errors.append(f"Key '{key}' should be a list, got {type(value)}")
            elif expected_type == 'number' and not isinstance(value, (int, float)):
                errors.append(f"Key '{key}' should be a number, got {type(value)}")
            elif expected_type == 'string' and not isinstance(value, str):
                errors.append(f"Key '{key}' should be a string, got {type(value)}")
            
            # Check nested required keys for objects
            if expected_type == 'object' and isinstance(value, dict):
                nested_required = definition.get('required_keys', [])
                for n_key in nested_required:
                    if n_key not in value:
                        errors.append(f"Missing nested required key in '{key}': {n_key}")

    return errors


def validate_csv_against_schema(csv_path: str, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a CSV file against the provided schema.
    Returns a list of validation errors (empty if valid).
    """
    errors = []

    if not os.path.exists(csv_path):
        errors.append(f"File not found: {csv_path}")
        return errors

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames

        if not headers:
            errors.append("CSV file is empty or has no headers")
            return errors

        required_columns = schema.get('required_columns', [])
        for col in required_columns:
            if col not in headers:
                errors.append(f"Missing required column: {col}")

    return errors


@pytest.mark.contract
def test_statistics_json_schema():
    """Test that statistics.json conforms to the analysis output schema."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip(f"Schema file missing: {SCHEMA_PATH}")

    schema = load_schema(SCHEMA_PATH)
    errors = validate_json_against_schema(STATISTICS_JSON_PATH, schema)

    assert not errors, f"Statistics JSON schema validation failed:\n" + "\n".join(errors)


@pytest.mark.contract
def test_vif_report_schema():
    """Test that vif_report.json conforms to the analysis output schema."""
    # Assuming a specific key or structure for VIF in the main schema, 
    # or a separate validation rule if the schema supports multiple file types.
    # For this implementation, we assume the general schema covers it or specific checks are added.
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip(f"Schema file missing: {SCHEMA_PATH}")
    
    schema = load_schema(SCHEMA_PATH)
    errors = validate_json_against_schema(VIF_REPORT_PATH, schema)
    
    assert not errors, f"VIF Report JSON schema validation failed:\n" + "\n".join(errors)


@pytest.mark.contract
def test_multiplicity_table_schema():
    """Test that multiplicity_table.csv conforms to the analysis output schema."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip(f"Schema file missing: {SCHEMA_PATH}")

    schema = load_schema(SCHEMA_PATH)
    # We might need a specific schema section for CSVs if not defined in the main one
    # Assuming the schema has a 'csv_validation' key or similar logic
    errors = validate_csv_against_schema(MULTIPLICITY_TABLE_PATH, schema)

    assert not errors, f"Multiplicity table CSV schema validation failed:\n" + "\n".join(errors)


@pytest.mark.contract
def test_bootstrap_results_schema():
    """Test that bootstrap_results.json conforms to the analysis output schema."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip(f"Schema file missing: {SCHEMA_PATH}")

    schema = load_schema(SCHEMA_PATH)
    errors = validate_json_against_schema(BOOTSTRAP_RESULTS_PATH, schema)

    assert not errors, f"Bootstrap results JSON schema validation failed:\n" + "\n".join(errors)


@pytest.mark.contract
def test_binning_results_schema():
    """Test that binning_results.csv conforms to the analysis output schema."""
    if not os.path.exists(SCHEMA_PATH):
        pytest.skip(f"Schema file missing: {SCHEMA_PATH}")

    schema = load_schema(SCHEMA_PATH)
    errors = validate_csv_against_schema(BINNING_RESULTS_PATH, schema)

    assert not errors, f"Binning results CSV schema validation failed:\n" + "\n".join(errors)
