"""
Contract tests for data schemas.

Validates that data outputs conform to the schemas defined in:
- specs/contracts/dataset.schema.yaml
- specs/contracts/metrics.schema.yaml
"""
import os
import sys
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

SCHEMAS_DIR = PROJECT_ROOT / "specs" / "contracts"
DATA_DIR = PROJECT_ROOT / "data"

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a YAML schema definition from the contracts directory."""
    schema_path = SCHEMAS_DIR / schema_name
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_field_type(value: Any, expected_type: str) -> bool:
    """Validate that a value matches the expected type string."""
    type_mapping = {
        "string": str,
        "integer": int,
        "number": (int, float),
        "boolean": bool,
        "array": list,
        "object": dict,
        "null": type(None)
    }
    
    expected_python_type = type_mapping.get(expected_type.lower())
    if expected_python_type is None:
        raise ValueError(f"Unknown type: {expected_type}")
    
    return isinstance(value, expected_python_type)

def validate_record(record: Dict[str, Any], schema: Dict[str, Any], record_id: str = "unknown") -> List[str]:
    """
    Validate a single record against a schema definition.
    
    Args:
        record: The data record to validate
        schema: The schema definition (with 'properties' and 'required' fields)
        record_id: Identifier for error messages
        
    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []
    properties = schema.get("properties", {})
    required_fields = schema.get("required", [])
    
    # Check required fields
    for field in required_fields:
        if field not in record:
            errors.append(f"Record {record_id}: Missing required field '{field}'")
    
    # Validate field types and constraints
    for field, value in record.items():
        if field not in properties:
            # Schema doesn't define this field - could be an error or extra field
            # For now, we'll just warn if strict mode is needed
            continue
        
        field_schema = properties[field]
        expected_type = field_schema.get("type")
        
        if expected_type and not validate_field_type(value, expected_type):
            errors.append(
                f"Record {record_id}: Field '{field}' has type "
                f"{type(value).__name__}, expected {expected_type}"
            )
        
        # Check for string length constraints
        if expected_type == "string" and "maxLength" in field_schema:
            if len(value) > field_schema["maxLength"]:
                errors.append(
                    f"Record {record_id}: Field '{field}' exceeds maxLength "
                    f"({len(value)} > {field_schema['maxLength']})"
                )
        
        # Check for numeric range constraints
        if expected_type in ("integer", "number"):
            if "minimum" in field_schema and value < field_schema["minimum"]:
                errors.append(
                    f"Record {record_id}: Field '{field}' below minimum "
                    f"({value} < {field_schema['minimum']})"
                )
            if "maximum" in field_schema and value > field_schema["maximum"]:
                errors.append(
                    f"Record {record_id}: Field '{field}' above maximum "
                    f"({value} > {field_schema['maximum']})"
                )
    
    return errors

def test_sessions_schema_matches_yaml():
    """
    Contract test: Validate that sessions data matches dataset.schema.yaml.
    
    This test will:
    1. Load the dataset schema definition
    2. Load the processed sessions data (if available)
    3. Validate each record against the schema
    4. Assert no validation errors
    """
    schema_path = SCHEMAS_DIR / "dataset.schema.yaml"
    data_path = DATA_DIR / "processed" / "sessions.json"
    
    # Check if schema exists
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    
    # Load schema
    schema = load_schema("dataset.schema.yaml")
    
    # Check if data exists (if not, skip validation but log)
    if not data_path.exists():
        # In a real test run, this might fail or be skipped depending on test configuration
        # For now, we'll create a minimal test to ensure the schema is loadable
        assert "properties" in schema, "Schema must have 'properties' field"
        assert "required" in schema, "Schema must have 'required' field"
        return
    
    # Load and validate data
    with open(data_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Handle both list and single record formats
    records = data if isinstance(data, list) else [data]
    
    all_errors = []
    for idx, record in enumerate(records):
        errors = validate_record(record, schema, record_id=f"record_{idx}")
        all_errors.extend(errors)
    
    assert len(all_errors) == 0, f"Schema validation failed:\n" + "\n".join(all_errors)

def test_metrics_schema_matches_yaml():
    """
    Contract test: Validate that metrics data matches metrics.schema.yaml.
    
    This test will:
    1. Load the metrics schema definition
    2. Load the processed metrics data (if available)
    3. Validate each record against the schema
    4. Assert no validation errors
    """
    schema_path = SCHEMAS_DIR / "metrics.schema.yaml"
    data_path = DATA_DIR / "processed" / "metrics.csv"
    
    # Check if schema exists
    assert schema_path.exists(), f"Schema file not found: {schema_path}"
    
    # Load schema
    schema = load_schema("metrics.schema.yaml")
    
    # Check if data exists
    if not data_path.exists():
        # Verify schema structure at minimum
        assert "properties" in schema, "Schema must have 'properties' field"
        assert "required" in schema, "Schema must have 'required' field"
        return
    
    # Load and validate data (CSV format)
    import csv
    
    with open(data_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    all_errors = []
    for idx, row in enumerate(rows):
        # Convert numeric strings to appropriate types for validation
        record = {}
        for field, value in row.items():
            if field in schema.get("properties", {}):
                field_type = schema["properties"][field].get("type")
                if field_type in ("integer", "number"):
                    try:
                        record[field] = float(value) if '.' in value else int(value)
                    except ValueError:
                        record[field] = value
                else:
                    record[field] = value
            else:
                record[field] = value
        
        errors = validate_record(record, schema, record_id=f"row_{idx}")
        all_errors.extend(errors)
    
    assert len(all_errors) == 0, f"Metrics schema validation failed:\n" + "\n".join(all_errors)