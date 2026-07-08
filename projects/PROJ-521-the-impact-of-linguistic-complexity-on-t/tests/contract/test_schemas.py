"""
Contract tests for data schema validation.
Validates JSON/CSV data against the YAML schemas defined in T005.
"""
import os
import json
import csv
import pytest
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional

# Try to import jsonschema, but provide a fallback if not installed
try:
    import jsonschema
    HAS_JSONSCHEMA = True
except ImportError:
    HAS_JSONSCHEMA = False


# --- Schema Loading Helpers ---

def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a schema from the specs/contracts directory.
    Expected schemas: text_sample, participant_response, analysis_result
    """
    # Determine project root (assuming this file is in tests/contract/)
    base_dir = Path(__file__).parent.parent.parent
    schema_path = base_dir / "specs" / "001-linguistic-complexity-trust" / "contracts" / f"{schema_name}.schema.yaml"
    
    if not schema_path.exists():
        # Fallback for T005 if the specific path structure is slightly different
        # Try a generic lookup in specs/contracts
        alt_path = base_dir / "specs" / "contracts" / f"{schema_name}.schema.yaml"
        if alt_path.exists():
            schema_path = alt_path
        else:
            raise FileNotFoundError(f"Schema file not found at {schema_path} or {alt_path}")

    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)


# --- Validation Logic ---

def validate_json_against_schema(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validates a single JSON object against a schema using jsonschema if available."""
    errors = []
    if HAS_JSONSCHEMA:
        try:
            jsonschema.validate(instance=data, schema=schema)
        except jsonschema.ValidationError as e:
            errors.append(f"JSON Validation Error: {e.message} at path {'/'.join(str(p) for p in e.path)}")
        except jsonschema.SchemaError as e:
            errors.append(f"Schema Definition Error: {e.message}")
    else:
        # Fallback: Basic structural check if jsonschema is missing
        # This ensures the test doesn't crash if dependencies are missing, 
        # though it's less rigorous.
        if 'required' in schema:
            for field in schema['required']:
                if field not in data:
                    errors.append(f"Missing required field: {field}")
    return errors


def validate_csv_row(row: Dict[str, str], schema: Dict[str, Any]) -> List[str]:
    """
    Validates a single CSV row (dict of strings) against a schema.
    Performs basic type coercion and required field checks.
    """
    errors = []
    properties = schema.get('properties', {})
    required_fields = schema.get('required', [])

    # Check required fields
    for field in required_fields:
        if field not in row or row[field] is None or row[field] == '':
            errors.append(f"Missing required field: {field}")

    # Type checking (basic string-to-type conversion)
    for field, value in row.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get('type', 'string')
            
            if value is None or value == '':
                if expected_type != 'null' and field not in required_fields:
                    continue # Optional empty field
                elif expected_type == 'null':
                    continue
                else:
                    errors.append(f"Field '{field}' is empty but required")
                    continue

            try:
                if expected_type == 'integer':
                    int(value)
                elif expected_type == 'number':
                    float(value)
                elif expected_type == 'boolean':
                    if value.lower() not in ('true', 'false', '1', '0'):
                        errors.append(f"Field '{field}' should be boolean, got: {value}")
                # string and null are default/implicit
            except ValueError:
                errors.append(f"Field '{field}' expected {expected_type}, got: {value}")

    return errors


# --- Test Cases ---

@pytest.mark.contract
def test_text_sample_schema_structure():
    """Verify the text_sample schema exists and has required structure."""
    schema = load_schema('text_sample')
    assert 'properties' in schema, "Schema must have 'properties'"
    assert 'required' in schema, "Schema must have 'required' fields"
    # Check for specific expected columns based on T013
    expected_cols = ['text_id', 'raw_text', 'source_id', 'flesch_kincaid', 'mtld', 'avg_sentence_length']
    for col in expected_cols:
        assert col in schema['properties'], f"Schema missing expected column: {col}"


@pytest.mark.contract
def test_generated_text_csv_validation():
    """
    T010: Contract test for generated_text.csv schema validation.
    Validates that data/raw/generated_text.csv (if it exists) conforms to text_sample.schema.yaml.
    If the file does not exist (e.g., T013 not run yet), this test is skipped.
    """
    base_dir = Path(__file__).parent.parent.parent
    data_path = base_dir / "data" / "raw" / "generated_text.csv"
    
    if not data_path.exists():
        pytest.skip(f"Data file not found at {data_path}. Run generation script first.")

    schema = load_schema('text_sample')
    errors = []
    row_count = 0

    with open(data_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        # Validate headers against schema properties
        schema_props = set(schema['properties'].keys())
        csv_headers = set(reader.fieldnames or [])
        
        # Check if all required schema fields are present in CSV
        missing_headers = schema['required'] - csv_headers
        if missing_headers:
            pytest.fail(f"CSV headers missing required fields from schema: {missing_headers}")

        for row in reader:
            row_count += 1
            row_errors = validate_csv_row(row, schema)
            if row_errors:
                errors.extend([f"Row {row_count}: {err}" for err in row_errors])
            if row_count > 100: # Limit check to first 100 rows for performance if file is huge
                break

    if errors:
        pytest.fail(f"Schema validation failed for {len(errors)} issues:\n" + "\n".join(errors))
    
    assert row_count > 0, "CSV file is empty"


@pytest.mark.contract
def test_participant_response_schema_structure():
    """Verify the participant_response schema exists."""
    schema = load_schema('participant_response')
    assert 'properties' in schema
    assert 'required' in schema


@pytest.mark.contract
def test_analysis_result_schema_structure():
    """Verify the analysis_result schema exists."""
    schema = load_schema('analysis_result')
    assert 'properties' in schema
    assert 'required' in schema


@pytest.mark.contract
def test_all_schemas_load_valid():
    """Ensure all defined schemas are valid YAML and parseable."""
    schemas = ['text_sample', 'participant_response', 'analysis_result']
    for s_name in schemas:
        try:
            s = load_schema(s_name)
            assert isinstance(s, dict), f"Schema {s_name} is not a dictionary"
            assert 'type' in s or 'properties' in s, f"Schema {s_name} missing type or properties"
        except Exception as e:
            pytest.fail(f"Failed to load schema {s_name}: {e}")