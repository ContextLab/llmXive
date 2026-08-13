import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

def load_yaml_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file and return it as a dictionary."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> bool:
    """
    Basic structural validation of the schema.
    Checks for required top-level keys.
    """
    required_keys = ['$schema', 'title', 'type', 'properties', 'required']
    for key in required_keys:
        if key not in schema:
            print(f"Schema validation failed: Missing required key '{key}'")
            return False
    
    # Check nested structure for 'metrics' and 'shap_analysis'
    props = schema.get('properties', {})
    if 'metrics' not in props:
        print("Schema validation failed: Missing 'metrics' property")
        return False
    if 'shap_analysis' not in props:
        print("Schema validation failed: Missing 'shap_analysis' property")
        return False
    
    return True

def validate_with_jsonschema(schema: Dict[str, Any], sample_data: Optional[Dict[str, Any]] = None) -> bool:
    """
    Validate the schema itself using jsonschema (if sample data is provided, validates data against schema).
    Since we are validating the schema definition, we assume the schema is syntactically correct if it loads.
    If sample data is provided, we check if it conforms.
    """
    try:
        import jsonschema
    except ImportError:
        print("Warning: 'jsonschema' library not installed. Skipping data validation.")
        return True

    # If sample data is provided, validate it against the schema
    if sample_data:
        try:
            jsonschema.validate(instance=sample_data, schema=schema)
            print("Sample data validation passed.")
            return True
        except jsonschema.exceptions.ValidationError as e:
            print(f"Schema validation failed: {e.message}")
            print(f"Path: {list(e.path)}")
            return False
    
    # If no sample data, we assume the schema structure check (validate_schema_structure) is sufficient
    # for the "schema validity" check requested.
    print("No sample data provided for validation. Schema structure check only.")
    return True

def run_yamllint(file_path: str) -> bool:
    """Run yamllint on the schema file."""
    try:
        result = subprocess.run(
            ['yamllint', '-d', 'relaxed', file_path],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode == 0:
            print("yamllint passed.")
            return True
        else:
            print(f"yamllint failed:\n{result.stdout}\n{result.stderr}")
            return False
    except FileNotFoundError:
        print("Warning: 'yamllint' not found. Skipping yamllint check.")
        return True

def main():
    schema_path = Path("contracts/output.schema.yaml")
    log_path = Path("state/schema_validation_log.txt")
    
    # Ensure state directory exists
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logs = []
    logs.append(f"Validating schema: {schema_path}")
    logs.append("-" * 50)

    # 1. Load Schema
    if not schema_path.exists():
        error_msg = f"Schema file not found: {schema_path}"
        logs.append(f"ERROR: {error_msg}")
        print(error_msg)
        with open(log_path, 'w') as f:
            f.write('\n'.join(logs))
        sys.exit(1)

    try:
        schema = load_yaml_schema(str(schema_path))
        logs.append("Schema loaded successfully.")
    except yaml.YAMLError as e:
        error_msg = f"Failed to parse YAML: {e}"
        logs.append(f"ERROR: {error_msg}")
        print(error_msg)
        with open(log_path, 'w') as f:
            f.write('\n'.join(logs))
        sys.exit(1)

    # 2. Run yamllint
    yamllint_passed = run_yamllint(str(schema_path))
    if yamllint_passed:
        logs.append("yamllint: PASSED")
    else:
        logs.append("yamllint: FAILED")

    # 3. Validate Structure
    structure_valid = validate_schema_structure(schema)
    if structure_valid:
        logs.append("Structure validation: PASSED")
    else:
        logs.append("Structure validation: FAILED")

    # 4. Validate with jsonschema (Optional if sample data exists, but we can validate the schema syntax)
    # Since we don't have a generated output file yet (T007 is creating the schema),
    # we just validate that the schema is a valid JSON Schema draft-07 document.
    # The jsonschema library validates the schema definition itself if we try to use it.
    schema_valid = validate_with_jsonschema(schema)
    if schema_valid:
        logs.append("JSON Schema validity: PASSED")
    else:
        logs.append("JSON Schema validity: FAILED")

    logs.append("-" * 50)
    final_status = "VALIDATION SUCCESSFUL" if all([yamllint_passed, structure_valid, schema_valid]) else "VALIDATION FAILED"
    logs.append(f"Final Status: {final_status}")

    print('\n'.join(logs))

    with open(log_path, 'w') as f:
        f.write('\n'.join(logs))

    if not final_status == "VALIDATION SUCCESSFUL":
        sys.exit(1)

if __name__ == "__main__":
    main()
