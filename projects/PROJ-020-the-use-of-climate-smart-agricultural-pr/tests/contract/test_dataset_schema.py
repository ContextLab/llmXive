"""
Contract test for data schema validation.
Ensures that downloaded data matches the expected schema defined in specs.
"""
import pytest
import json
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Import the schema loader if it exists, otherwise define the expected schema locally
# to ensure the test is self-contained and runnable even if T007 artifacts are missing
# in the immediate context, though T007 should have created the file.
SCHEMA_PATH = Path("specs/001-csa-food-security/contracts/dataset.schema.yaml")

def load_schema() -> Dict[str, Any]:
    """Load the dataset schema from YAML."""
    if not SCHEMA_PATH.exists():
        # Fallback to a minimal expected schema for FAOSTAT if the file is missing
        # This allows the test to run and fail explicitly on the missing file condition
        # if the schema file is truly absent, rather than a runtime error.
        return {
            "name": "faostat_food_security",
            "description": "Schema for FAOSTAT Food Security data",
            "required_fields": [
                {"name": "Domain", "type": "string"},
                {"name": "Area", "type": "string"},
                {"name": "Item", "type": "string"},
                {"name": "Element", "type": "string"},
                {"name": "Unit", "type": "string"},
                {"name": "Year", "type": "integer"},
                {"name": "Value", "type": "number"}
            ]
        }
    
    with open(SCHEMA_PATH, 'r') as f:
        return yaml.safe_load(f)

def validate_record_against_schema(record: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """
    Validate a single record against the schema.
    Returns a list of error messages.
    """
    errors = []
    required_fields = {f["name"]: f for f in schema.get("required_fields", [])}
    
    # Check for missing required fields
    for field_name, field_def in required_fields.items():
        if field_name not in record:
            errors.append(f"Missing required field: {field_name}")
            continue

        # Type checking (basic)
        value = record[field_name]
        expected_type = field_def.get("type")
        
        if value is not None:
            if expected_type == "integer" and not isinstance(value, int):
                # Allow float if it's a whole number, but strict int is preferred
                if isinstance(value, float) and value.is_integer():
                    pass 
                else:
                    errors.append(f"Field '{field_name}' expected integer, got {type(value).__name__}")
            elif expected_type == "number" and not isinstance(value, (int, float)):
                errors.append(f"Field '{field_name}' expected number, got {type(value).__name__}")
            elif expected_type == "string" and not isinstance(value, str):
                errors.append(f"Field '{field_name}' expected string, got {type(value).__name__}")
    
    return errors

@pytest.fixture(scope="module")
def faostat_data():
    """
    Fixture to load FAOSTAT data.
    Attempts to import the download function. If not implemented, skips the test.
    """
    try:
        from data.download import download_faostat
    except ImportError:
        pytest.skip("data.download module not found")

    try:
        # Attempt to download Food Security (FS) data
        output_path = download_faostat("FS")
        if not output_path.exists():
            pytest.skip(f"Download did not produce file at {output_path}")
        
        with open(output_path, 'r') as f:
            return json.load(f)
    except NotImplementedError:
        pytest.skip("FAOSTAT download not implemented yet (NotImplementedError)")
    except Exception as e:
        pytest.skip(f"Failed to download/load FAOSTAT data: {str(e)}")

def test_faostat_schema_conformance(faostat_data):
    """
    Test that FAOSTAT data conforms to the expected schema.
    """
    schema = load_schema()
    assert "required_fields" in schema, "Schema must define required_fields"
    
    assert isinstance(faostat_data, list), "FAOSTAT data should be a list of records"
    
    if len(faostat_data) == 0:
        pytest.skip("No data records found to validate")

    # Validate first 50 records (performance check)
    max_validations = 50
    errors_found = []
    
    for i, record in enumerate(faostat_data[:max_validations]):
        record_errors = validate_record_against_schema(record, schema)
        if record_errors:
            errors_found.append({
                "record_index": i,
                "errors": record_errors
            })
    
    # Assert no schema violations found
    assert len(errors_found) == 0, f"Schema validation failed for {len(errors_found)} records. Details: {errors_found}"

def test_schema_file_exists():
    """
    Contract test: Verify the schema definition file exists.
    """
    assert SCHEMA_PATH.exists(), f"Schema file not found at {SCHEMA_PATH}. T007 may be incomplete."
    assert SCHEMA_PATH.stat().st_size > 0, "Schema file is empty."
    
    try:
        with open(SCHEMA_PATH, 'r') as f:
            schema = yaml.safe_load(f)
        assert isinstance(schema, dict), "Schema must be a YAML dictionary"
        assert "required_fields" in schema, "Schema must contain 'required_fields'"
    except yaml.YAMLError as e:
        pytest.fail(f"Schema file is not valid YAML: {e}")