import sys
import yaml
import json
import jsonschema
from pathlib import Path

def load_schema(schema_path: str) -> dict:
    """Load a JSON/YAML schema from a file."""
    path = Path(schema_path)
    with open(path, 'r') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        else:
            return json.load(f)

def generate_minimal_sample(schema: dict) -> dict:
    """Generate a minimal valid sample based on the schema properties."""
    sample = {}
    required = schema.get('required', [])
    properties = schema.get('properties', {})

    for prop_name, prop_def in properties.items():
        if prop_name in required:
            prop_type = prop_def.get('type')
            if prop_type == 'string':
                if prop_def.get('format') == 'date-time':
                    sample[prop_name] = "2023-01-01T00:00:00Z"
                else:
                    sample[prop_name] = "sample_string"
            elif prop_type == 'integer':
                sample[prop_name] = 0
            elif prop_type == 'number':
                sample[prop_name] = 0.0
            elif prop_type == 'boolean':
                sample[prop_name] = False
            elif prop_type == 'array':
                sample[prop_name] = []
            elif prop_type == 'object':
                sample[prop_name] = {}
            elif prop_type == 'null':
                sample[prop_name] = None
            else:
                sample[prop_name] = None
    return sample

def main():
    """Validate all schemas against sample data."""
    contracts_dir = Path(__file__).parent.parent / 'contracts'
    schema_files = [
        'dataset.schema.yaml',
        'analysis_log.schema.yaml',
        'analysis_results.schema.yaml',
        'dataset_manifest.schema.yaml',
        'statistical_report.schema.yaml',
        'tool_version.schema.yaml'
    ]

    all_valid = True

    for schema_file in schema_files:
        schema_path = contracts_dir / schema_file
        if not schema_path.exists():
            print(f"ERROR: Schema file not found: {schema_path}")
            all_valid = False
            continue

        try:
            schema = load_schema(str(schema_path))
            sample = generate_minimal_sample(schema)
            jsonschema.validate(instance=sample, schema=schema)
            print(f"OK: {schema_file} validated successfully.")
        except jsonschema.ValidationError as e:
            print(f"ERROR: Validation failed for {schema_file}: {e.message}")
            all_valid = False
        except Exception as e:
            print(f"ERROR: Failed to process {schema_file}: {e}")
            all_valid = False

    if not all_valid:
        sys.exit(1)
    else:
        print("All schemas validated successfully.")

if __name__ == '__main__':
    main()
