import os
import sys
import json
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from config import get_config_dict

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load the JSON schema from a YAML file."""
    if not os.path.exists(schema_path):
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_field_presence(data: Dict[str, Any], schema: Dict[str, Any], path: str = "") -> List[str]:
    """Recursively validate that all required fields in the schema are present in the data."""
    errors = []
    required_fields = schema.get('required', [])
    
    for field in required_fields:
        current_path = f"{path}.{field}" if path else field
        if field not in data:
            errors.append(f"Missing required field: {current_path}")
        else:
            # Recurse into object properties if it's an object
            if schema.get('type') == 'object' and 'properties' in schema:
                if field in schema['properties']:
                    nested_schema = schema['properties'][field]
                    nested_errors = validate_field_presence(data[field], nested_schema, current_path)
                    errors.extend(nested_errors)
            # Handle array items if schema defines 'items'
            elif schema.get('type') == 'array' and 'items' in schema:
                if isinstance(data[field], list):
                    for i, item in enumerate(data[field]):
                        item_path = f"{current_path}[{i}]"
                        # Check if item is an object with requirements
                        if isinstance(item, dict) and 'properties' in schema['items']:
                            item_errors = validate_field_presence(item, schema['items'], item_path)
                            errors.extend(item_errors)
    return errors

def validate_report_structure(report_data: Dict[str, Any], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validate the structure of the report against the schema."""
    errors = validate_field_presence(report_data, schema)
    is_valid = len(errors) == 0
    return is_valid, errors

def validate_report_file(report_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """Load a report JSON file and validate it against the schema."""
    if not os.path.exists(report_path):
        return False, [f"Report file not found: {report_path}"]
    
    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        return False, [f"Invalid JSON in report file: {e}"]
    
    schema = load_schema(schema_path)
    is_valid, errors = validate_report_structure(report_data, schema)
    return is_valid, errors

def main():
    """Main entry point for report validation."""
    config = get_config_dict()
    report_path = config.get('report_output_path', 'data/reports/final_report.json')
    schema_path = config.get('schema_path', 'contracts/output.schema.yaml')
    
    print(f"Validating report: {report_path}")
    print(f"Against schema: {schema_path}")
    
    is_valid, errors = validate_report_file(report_path, schema_path)
    
    if is_valid:
        print("✓ Validation PASSED: Report structure is valid.")
        return 0
    else:
        print("✗ Validation FAILED:")
        for error in errors:
            print(f"  - {error}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
