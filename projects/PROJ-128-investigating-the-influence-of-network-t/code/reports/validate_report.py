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
    """Load the JSON schema from a YAML or JSON file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)

def validate_field_presence(data: Dict[str, Any], required_fields: List[str], parent_path: str = "") -> List[str]:
    """Recursively validate that all required fields are present in the data."""
    errors = []
    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field: {parent_path + '.' + field if parent_path else field}")
    return errors

def validate_report_structure(data: Dict[str, Any], schema: Dict[str, Any]) -> List[str]:
    """Validate the report data against the provided schema."""
    errors = []
    
    # Check top-level required fields
    if 'required' in schema:
        errors.extend(validate_field_presence(data, schema['required']))
    
    # Validate properties recursively
    properties = schema.get('properties', {})
    for prop_name, prop_schema in properties.items():
        if prop_name in data:
            prop_data = data[prop_name]
            if 'required' in prop_schema:
                prop_errors = validate_field_presence(prop_data, prop_schema['required'], prop_name)
                errors.extend(prop_errors)
            
            # Handle nested objects
            if prop_schema.get('type') == 'object' and 'properties' in prop_schema:
                nested_errors = validate_report_structure(prop_data, prop_schema)
                errors.extend(nested_errors)
            
            # Handle arrays of objects
            if prop_schema.get('type') == 'array' and 'items' in prop_schema:
                item_schema = prop_schema['items']
                if item_schema.get('type') == 'object' and 'required' in item_schema:
                    for i, item in enumerate(prop_data):
                        item_errors = validate_field_presence(item, item_schema['required'], f"{prop_name}[{i}]")
                        errors.extend(item_errors)
                        if 'properties' in item_schema:
                            nested_errors = validate_report_structure(item, item_schema)
                            errors.extend(nested_errors)
    
    return errors

def validate_report_file(report_path: str, schema_path: str) -> Tuple[bool, List[str]]:
    """Validate a specific report file against the schema."""
    errors = []
    
    # Load schema
    try:
        schema = load_schema(schema_path)
    except Exception as e:
        return False, [f"Failed to load schema: {str(e)}"]
    
    # Load report
    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
    except Exception as e:
        return False, [f"Failed to load report file: {str(e)}"]
    
    # Validate structure
    validation_errors = validate_report_structure(report_data, schema)
    errors.extend(validation_errors)
    
    return len(errors) == 0, errors

def main():
    """Main entry point for report validation."""
    config = get_config_dict()
    report_path = config.get('final_report_path', 'data/reports/final_report.json')
    schema_path = config.get('output_schema_path', 'contracts/output.schema.yaml')
    
    print(f"Validating report: {report_path}")
    print(f"Against schema: {schema_path}")
    
    is_valid, errors = validate_report_file(report_path, schema_path)
    
    if is_valid:
        print("✓ Report validation PASSED.")
        print("All required fields (r, p, FDR, sensitivity, absolute difference) are present.")
        return 0
    else:
        print("✗ Report validation FAILED.")
        print("Errors found:")
        for err in errors:
            print(f"  - {err}")
        return 1

if __name__ == "__main__":
    sys.exit(main())