"""
Script to validate that all schema files are syntactically correct
and can validate sample data as per task T005 requirements.
"""
import sys
import yaml
import jsonschema
from pathlib import Path

# Add project root to path if running as script
PROJECT_ROOT = Path(__file__).parent.parent
CONTRACTS_DIR = PROJECT_ROOT / "contracts"

SCHEMAS = [
    "dataset.schema.yaml",
    "analysis_log.schema.yaml",
    "analysis_results.schema.yaml",
    "dataset_manifest.schema.yaml",
    "statistical_report.schema.yaml",
    "tool_version.schema.yaml"
]

def load_schema(filename: str) -> dict:
    """Load a YAML schema file."""
    path = CONTRACTS_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")
    with open(path, "r") as f:
        return yaml.safe_load(f)

def generate_minimal_sample(schema: dict) -> dict:
    """Generate a minimal valid sample for validation testing."""
    sample = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])
    
    for key in required:
        prop = properties.get(key, {})
        p_type = prop.get("type")
        p_enum = prop.get("enum")
        p_format = prop.get("format")
        
        if p_enum:
            sample[key] = p_enum[0]
        elif p_type == "string":
            if p_format == "date-time":
                sample[key] = "2023-10-27T10:00:00Z"
            else:
                sample[key] = "sample-value"
        elif p_type == "integer":
            sample[key] = 1
        elif p_type == "number":
            sample[key] = 1.0
        elif p_type == "boolean":
            sample[key] = True
        elif p_type == "array":
            sample[key] = []
        elif p_type == "object":
            sample[key] = {}
    return sample

def main():
    print(f"Validating schemas in {CONTRACTS_DIR}...")
    all_valid = True
    
    for schema_file in SCHEMAS:
        try:
            schema = load_schema(schema_file)
            sample = generate_minimal_sample(schema)
            jsonschema.validate(instance=sample, schema=schema)
            print(f"✓ {schema_file} is valid.")
        except FileNotFoundError as e:
            print(f"✗ {schema_file} missing: {e}")
            all_valid = False
        except yaml.YAMLError as e:
            print(f"✗ {schema_file} YAML syntax error: {e}")
            all_valid = False
        except jsonschema.exceptions.ValidationError as e:
            print(f"✗ {schema_file} validation failed: {e.message}")
            all_valid = False
        except Exception as e:
            print(f"✗ {schema_file} unexpected error: {e}")
            all_valid = False
    
    if all_valid:
        print("\nAll schemas validated successfully.")
        return 0
    else:
        print("\nSchema validation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())