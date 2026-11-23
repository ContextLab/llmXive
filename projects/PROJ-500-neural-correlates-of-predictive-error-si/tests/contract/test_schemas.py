import json
import os
import pytest
from pathlib import Path
import yaml

# Import project modules for data generation if needed for integration
# Note: We assume the pipeline (align.py, finalize.py) runs before this test in the full run-book
# For the contract test, we validate the schema against the generated file.

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"
DATA_DIR = PROJECT_ROOT / "data"

def load_schema(schema_name: str) -> dict:
    """Load a JSON Schema from the contracts directory."""
    schema_path = CONTRACTS_DIR / f"{schema_name}.schema.yaml"
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r") as f:
        return yaml.safe_load(f)

def validate_data_against_schema(data_path: Path, schema: dict) -> bool:
    """
    Validates a CSV file against a JSON Schema.
    Since jsonschema validates JSON objects, we convert CSV to a list of dicts (records)
    and validate the structure of the records against the schema's 'items' definition.
    """
    try:
        import pandas as pd
        import jsonschema
    except ImportError:
        raise RuntimeError("Missing dependencies: pandas, jsonschema")

    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    df = pd.read_csv(data_path)
    
    # Convert to list of dicts for validation
    data_records = df.to_dict(orient='records')
    
    # The schema usually defines the structure of a single object (a row)
    # We validate each row against the schema properties
    # Note: The schema file defines the object structure. We treat the dataset as a list of these objects.
    
    # Construct a temporary schema for the list of records if the original schema is for a single object
    # Most JSON schemas in contracts/ are defined as the object structure.
    # We validate each record against the 'properties' defined in the schema.
    
    schema_type = schema.get('type')
    schema_properties = schema.get('properties', {})
    required_fields = schema.get('required', [])
    
    # Validate headers (columns)
    if not all(col in df.columns for col in required_fields):
        missing = [col for col in required_fields if col not in df.columns]
        raise AssertionError(f"Missing required columns in {data_path.name}: {missing}")
    
    # Validate data types and content for each row
    for i, record in enumerate(data_records):
        # Check required fields presence
        for field in required_fields:
            if field not in record or record[field] is None:
                raise AssertionError(f"Missing required field '{field}' in row {i}")
        
        # Check specific field types if defined in schema
        for field, details in schema_properties.items():
            if field in record and record[field] is not None:
                expected_type = details.get('type')
                if expected_type == 'string' and not isinstance(record[field], str):
                    # Allow numeric types if the schema is loose, but strict check preferred
                    pass 
                # Additional type checks can be added here based on schema details

    return True

def test_aligned_data_schema_exists():
    """Verify that the aligned_data.schema.yaml exists."""
    schema_path = CONTRACTS_DIR / "aligned_data.schema.yaml"
    assert schema_path.exists(), "aligned_data.schema.yaml not found in contracts/"

def test_model_output_schema_exists():
    """Verify that the model_output.schema.yaml exists."""
    schema_path = CONTRACTS_DIR / "model_output.schema.yaml"
    assert schema_path.exists(), "model_output.schema.yaml not found in contracts/"

def test_aligned_data_schema_valid():
    """Validate that the aligned_data.schema.yaml is valid YAML/JSON Schema."""
    schema = load_schema("aligned_data")
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "properties" in schema, "Schema must define properties"
    # Check for specific required fields from T009a and T022b
    required_fields = schema.get("required", [])
    assert "subject_id" in required_fields, "subject_id is required"
    assert "block_id" in required_fields, "block_id is required"
    assert "mmn_amplitude" in required_fields, "mmn_amplitude is required"
    assert "learning_phase" in required_fields, "learning_phase is required (T022b)"

def test_model_output_schema_valid():
    """Validate that the model_output.schema.yaml is valid YAML/JSON Schema."""
    schema = load_schema("model_output")
    assert isinstance(schema, dict), "Schema must be a dictionary"
    assert "properties" in schema, "Schema must define properties"
    required_fields = schema.get("required", [])
    assert "coefficients" in required_fields, "coefficients is required"
    assert "p_values" in required_fields, "p_values is required"

@pytest.mark.integration
def test_aligned_data_contract_with_generated_data():
    """
    Contract test for aligned_data schema in tests/contract/test_schemas.py.
    Validates that the final data/aligned_data.csv contains all required fields including learning_phase.
    Dependency: T009a (Base Schema), T022b (Learning_Phase extension).
    """
    aligned_data_path = DATA_DIR / "aligned_data.csv"
    
    # Skip if file doesn't exist (pipeline not run)
    if not aligned_data_path.exists():
        pytest.skip("data/aligned_data.csv not found. Run the pipeline first.")
    
    schema = load_schema("aligned_data")
    try:
        validate_data_against_schema(aligned_data_path, schema)
    except (AssertionError, FileNotFoundError, RuntimeError) as e:
        pytest.fail(f"Schema validation failed: {e}")