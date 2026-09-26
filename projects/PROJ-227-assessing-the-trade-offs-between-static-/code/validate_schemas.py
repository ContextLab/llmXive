import sys
import yaml
import jsonschema
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Load a JSON/YAML schema from disk."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            import json
            return json.load(f)

def generate_minimal_sample(schema: dict) -> dict:
    """Generate a minimal valid sample based on the schema structure."""
    # This is a helper for manual verification, not a full generator
    # It returns a placeholder structure that satisfies 'required' fields
    # with minimal valid types.
    
    sample = {}
    required_fields = schema.get('required', [])
    
    for field in required_fields:
        prop = schema['properties'].get(field, {})
        prop_type = prop.get('type')
        
        if prop_type == 'object':
            # Recursively generate minimal object for required sub-fields
            sample[field] = generate_minimal_sample(prop)
        elif prop_type == 'array':
            sample[field] = []
        elif prop_type == 'string':
            if 'enum' in prop:
                sample[field] = prop['enum'][0]
            elif 'format' in prop and prop['format'] == 'date-time':
                sample[field] = "2023-01-01T00:00:00Z"
            else:
                sample[field] = "minimal_value"
        elif prop_type == 'integer':
            sample[field] = 0
        elif prop_type == 'number':
            sample[field] = 0.0
        elif prop_type == 'boolean':
            sample[field] = False
        else:
            sample[field] = None
    
    return sample

def main():
    """Validate all schemas against minimal samples."""
    contracts_dir = Path(__file__).parent.parent / "contracts"
    schemas = [
        "dataset.schema.yaml",
        "analysis_log.schema.yaml",
        "analysis_results.schema.yaml",
        "dataset_manifest.schema.yaml",
        "statistical_report.schema.yaml",
        "tool_version.schema.yaml"
    ]
    
    print("Validating schemas...")
    all_valid = True
    
    for schema_name in schemas:
        schema_path = contracts_dir / schema_name
        if not schema_path.exists():
            print(f"FAIL: Schema missing: {schema_path}")
            all_valid = False
            continue
        
        try:
            schema = load_schema(str(schema_path))
            sample = generate_minimal_sample(schema)
            jsonschema.validate(instance=sample, schema=schema)
            print(f"PASS: {schema_name}")
        except jsonschema.exceptions.ValidationError as e:
            print(f"FAIL: {schema_name} - {e.message}")
            all_valid = False
        except Exception as e:
            print(f"ERROR: {schema_name} - {str(e)}")
            all_valid = False
    
    if all_valid:
        print("\nAll schemas are valid.")
        sys.exit(0)
    else:
        print("\nSome schemas failed validation.")
        sys.exit(1)

if __name__ == "__main__":
    main()
