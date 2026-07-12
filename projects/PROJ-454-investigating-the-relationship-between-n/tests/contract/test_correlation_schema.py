"""
Contract test for correlation_results.schema.yaml validation.

This test verifies that the regression output artifacts conform to the 
defined JSON schema for correlation results.

Task: T018 [US2]
"""
import os
import sys
import json
import pytest
from pathlib import Path
import jsonschema
from jsonschema import validate, ValidationError, SchemaError

# Add project root to path if not already present
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root))

SCHEMA_PATH = project_root / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts" / "correlation_results.schema.yaml"
DATA_DIR = project_root / "data" / "processed"

# Helper to load YAML safely without external deps if possible, 
# but we assume pyyaml is installed per requirements.
try:
    import yaml
except ImportError:
    yaml = None

def load_schema(schema_path: Path) -> dict:
    """Load the JSON/YAML schema from disk."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            if yaml is None:
                raise ImportError("PyYAML is required to load .yaml schema files.")
            return yaml.safe_load(f)
        else:
            return json.load(f)

def load_data_file(data_path: Path) -> dict:
    """Load a JSON data file for validation."""
    if not data_path.exists():
        # If the data file doesn't exist yet, we skip the validation test 
        # or mark it as skipped depending on test strategy. 
        # For a contract test, we usually expect the file to exist if the pipeline ran.
        # However, to avoid failure in CI if data hasn't been generated yet, 
        # we might skip. But strictly, if the schema exists, we test against it.
        # Let's assume we are testing the *structure* if a sample exists, 
        # or we generate a minimal valid sample if none exists for validation purposes?
        # No, contract tests usually validate the output of the pipeline.
        # We will raise a clear error if the file is missing, as the pipeline should have created it.
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    with open(data_path, 'r', encoding='utf-8') as f:
        return json.load(f)

@pytest.fixture
def schema_dict():
    """Fixture to load the correlation results schema."""
    return load_schema(SCHEMA_PATH)

@pytest.mark.skipif(not SCHEMA_PATH.exists(), reason="Schema file not found")
def test_schema_is_valid_json_schema(schema_dict):
    """Verify the schema itself is a valid JSON Schema."""
    try:
        jsonschema.Draft7Validator.check_schema(schema_dict)
    except SchemaError as e:
        pytest.fail(f"Schema is not valid: {e}")

@pytest.mark.skipif(not (DATA_DIR / "correlation_results_fdr.csv").exists(), 
                    reason="Data file not generated yet")
def test_fdr_results_csv_matches_schema(schema_dict):
    """
    Validate the generated FDR-corrected correlation results against the schema.
    
    Note: jsonschema validates JSON objects. If the output is CSV, we must either:
    1. Convert CSV to JSON (list of dicts) for validation.
    2. Or ensure the schema is designed for a JSON representation of the CSV.
    
    The schema `correlation_results.schema.yaml` likely defines the structure of a 
    record (row). We will convert the CSV to a list of dicts and validate each record
    against the `items` definition or the record definition in the schema.
    """
    import pandas as pd
    
    csv_path = DATA_DIR / "correlation_results_fdr.csv"
    df = pd.read_csv(csv_path)
    
    # Convert to list of dicts
    records = df.to_dict('records')
    
    # Determine the schema part to validate against.
    # Usually, the schema defines an object structure for a single record.
    # If the schema is a list wrapper, use that. Otherwise, validate items.
    
    schema_to_use = schema_dict
    if schema_dict.get("type") == "array":
        # If the schema expects an array, we validate the whole list
        # But jsonschema.validate expects an instance matching the schema.
        # Let's assume the schema defines a single object (the row structure).
        # We will validate each row.
        item_schema = schema_dict.get("items", {})
        if not item_schema:
            pytest.fail("Schema defines an array but has no 'items' definition.")
        schema_to_use = item_schema
    
    for i, record in enumerate(records):
        try:
            validate(instance=record, schema=schema_to_use)
        except ValidationError as e:
            pytest.fail(f"Validation failed for record {i}: {e.message}. "
                        f"Instance: {record}")

@pytest.mark.skipif(not (DATA_DIR / "correlation_results_ols.csv").exists(), 
                    reason="OLS Data file not generated yet")
def test_ols_results_csv_matches_schema(schema_dict):
    """Validate OLS results against the same schema structure."""
    import pandas as pd
    
    csv_path = DATA_DIR / "correlation_results_ols.csv"
    df = pd.read_csv(csv_path)
    records = df.to_dict('records')
    
    schema_to_use = schema_dict
    if schema_dict.get("type") == "array":
        item_schema = schema_dict.get("items", {})
        if not item_schema:
            pytest.fail("Schema defines an array but has no 'items' definition.")
        schema_to_use = item_schema
    
    for i, record in enumerate(records):
        try:
            validate(instance=record, schema=schema_to_use)
        except ValidationError as e:
            pytest.fail(f"Validation failed for OLS record {i}: {e.message}. "
                        f"Instance: {record}")

@pytest.mark.skipif(not (DATA_DIR / "correlation_results_bonferroni_historical.csv").exists(), 
                    reason="Bonferroni Data file not generated yet")
def test_bonferroni_results_csv_matches_schema(schema_dict):
    """Validate Bonferroni historical results against the same schema structure."""
    import pandas as pd
    
    csv_path = DATA_DIR / "correlation_results_bonferroni_historical.csv"
    df = pd.read_csv(csv_path)
    records = df.to_dict('records')
    
    schema_to_use = schema_dict
    if schema_dict.get("type") == "array":
        item_schema = schema_dict.get("items", {})
        if not item_schema:
            pytest.fail("Schema defines an array but has no 'items' definition.")
        schema_to_use = item_schema
    
    for i, record in enumerate(records):
        try:
            validate(instance=record, schema=schema_to_use)
        except ValidationError as e:
            pytest.fail(f"Validation failed for Bonferroni record {i}: {e.message}. "
                        f"Instance: {record}")

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
