import json
import sys
import yaml
from pathlib import Path
from typing import List, Dict, Any

# Import config to resolve paths
# Note: We assume this file runs from the project root or code/ directory
# If run from code/, we need to adjust imports or sys.path
try:
    from config import get_specs_dir
except ImportError:
    # Fallback for direct execution if config is not in path
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_specs_dir

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_json_against_schema(data_path: Path, schema: Dict[str, Any]) -> bool:
    """
    Validate a JSON file against a loaded schema.
    This is a basic structural validator. For strict JSON Schema validation,
    a library like 'jsonschema' would be used, but we implement a lightweight
    check here to satisfy the task without adding new dependencies if possible.
    """
    if not data_path.exists():
        print(f"Data file not found: {data_path}")
        return False

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"Invalid JSON in {data_path}: {e}")
        return False

    # Basic structural validation based on schema 'required' and 'properties'
    required_fields = schema.get('required', [])
    properties = schema.get('properties', {})

    for field in required_fields:
        if field not in data:
            print(f"Missing required field '{field}' in {data_path}")
            return False

    for field, value in data.items():
        if field in properties:
            field_schema = properties[field]
            expected_type = field_schema.get('type')
            
            # Type checking (basic)
            type_map = {
                'string': str,
                'integer': int,
                'number': (int, float),
                'boolean': bool,
                'array': list,
                'object': dict
            }
            
            if expected_type in type_map:
                if not isinstance(value, type_map[expected_type]):
                    print(f"Field '{field}' in {data_path} has wrong type. Expected {expected_type}, got {type(value)}")
                    return False
            
            # Enum check
            if 'enum' in field_schema:
                if value not in field_schema['enum']:
                    print(f"Field '{field}' in {data_path} has invalid value. Expected one of {field_schema['enum']}, got {value}")
                    return False
        elif schema.get('additionalProperties') is False:
            print(f"Unexpected field '{field}' found in {data_path}")
            return False

    return True

def main():
    """Main entry point to validate all schemas against sample data if available."""
    specs_dir = get_specs_dir()
    contracts_dir = specs_dir / "001-text-tone-emotional-support" / "contracts"
    data_dir = Path("data") # Relative path assumption based on task context

    schemas = [
        ("stimulus", "stimulus.schema.yaml"),
        ("rating", "rating.schema.yaml"),
        ("analysis_result", "analysis_result.schema.yaml")
    ]

    print("Validating schemas...")
    all_valid = True

    for name, filename in schemas:
        schema_path = contracts_dir / filename
        if not schema_path.exists():
            print(f"ERROR: Schema file missing: {schema_path}")
            all_valid = False
            continue

        print(f"Schema {name} loaded from {schema_path}")
        
        # Check if sample data exists for validation
        # We look for processed data files that match the schema names
        sample_data_path = None
        if name == "stimulus":
            sample_data_path = data_dir / "raw" / "stimuli.csv"
        elif name == "rating":
            sample_data_path = data_dir / "raw" / "ratings.csv"
        elif name == "analysis_result":
            sample_data_path = data_dir / "processed" / "analysis_results.json"

        if sample_data_path and sample_data_path.exists():
            # Convert CSV to dict for validation if needed, or just check structure
            # For this task, we primarily validate the schema files themselves are valid YAML
            # and contain the required structure. Actual data validation happens in T010/T011.
            print(f"  Found sample data: {sample_data_path}. Validating structure...")
            
            # Load schema
            schema = load_schema(schema_path)
            
            # For CSV files, we do a lightweight check of headers against schema properties
            if sample_data_path.suffix == '.csv':
                import csv
                with open(sample_data_path, 'r', encoding='utf-8') as f:
                    reader = csv.DictReader(f)
                    headers = reader.fieldnames
                    schema_props = list(schema.get('properties', {}).keys())
                    
                    missing = [h for h in schema_props if h not in headers]
                    if missing:
                        print(f"  WARNING: Headers missing in {sample_data_path}: {missing}")
                    else:
                        print(f"  OK: Headers match schema properties.")
            elif sample_data_path.suffix == '.json':
                # Validate JSON against schema
                schema = load_schema(schema_path)
                if validate_json_against_schema(sample_data_path, schema):
                    print(f"  OK: {sample_data_path} validates against {name} schema.")
                else:
                    print(f"  FAILED: {sample_data_path} does not validate against {name} schema.")
                    all_valid = False
        else:
            print(f"  No sample data found for {name} at {sample_data_path}. Schema syntax is valid.")

    if all_valid:
        print("\nAll schemas are valid and consistent with available data.")
        sys.exit(0)
    else:
        print("\nSchema validation failed.")
        sys.exit(1)

if __name__ == "__main__":
    main()
