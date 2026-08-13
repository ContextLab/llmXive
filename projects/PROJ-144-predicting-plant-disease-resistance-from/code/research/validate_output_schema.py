"""
Validates the output schema defined in contracts/output.schema.yaml.
Uses jsonschema to validate the structure and yamllint to check syntax.
"""
import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Ensure we can import from code/utils
sys.path.insert(0, str(Path(__file__).parent.parent))

def load_yaml_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> List[str]:
    """Validate that the schema has required top-level keys."""
    errors = []
    
    if '$schema' not in schema:
        errors.append("Missing '$schema' key")
    
    if 'type' not in schema:
        errors.append("Missing 'type' key")
    elif schema['type'] != 'object':
        errors.append(f"Expected type 'object', got '{schema['type']}'")
    
    if 'properties' not in schema:
        errors.append("Missing 'properties' key")
    
    return errors

def validate_with_jsonschema(schema_path: str, test_data: Optional[Dict] = None) -> List[str]:
    """
    Validate the schema structure using jsonschema library.
    If test_data is provided, also validate that data against the schema.
    """
    errors = []
    
    try:
        import jsonschema
    except ImportError:
        return ["jsonschema library not installed. Install with: pip install jsonschema"]
    
    try:
        schema = load_yaml_schema(schema_path)
    except Exception as e:
        return [f"Failed to load schema: {str(e)}"]
    
    # Validate schema structure
    structure_errors = validate_schema_structure(schema)
    errors.extend(structure_errors)
    
    # If schema is valid, try to compile it
    try:
        validator = jsonschema.Draft7Validator(schema)
        validator.check_schema(schema)
    except jsonschema.exceptions.SchemaError as e:
        errors.append(f"Schema validation error: {str(e)}")
    
    # If test data is provided, validate against it
    if test_data is not None:
        try:
            errors_list = list(jsonschema.validate(test_data, schema))
            if errors_list:
                errors.extend([str(e) for e in errors_list])
        except jsonschema.exceptions.ValidationError as e:
            errors.append(f"Data validation error: {str(e)}")
    
    return errors

def run_yamllint(schema_path: str) -> List[str]:
    """Run yamllint on the schema file if available."""
    errors = []
    
    try:
        result = subprocess.run(
            ['yamllint', schema_path],
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            errors.append(f"yamllint found issues:\n{result.stdout}\n{result.stderr}")
    except FileNotFoundError:
        errors.append("yamllint not installed. Install with: pip install yamllint")
    except subprocess.TimeoutExpired:
        errors.append("yamllint timed out")
    
    return errors

def main():
    """Main entry point for schema validation."""
    schema_path = "contracts/output.schema.yaml"
    output_path = "state/schema_validation_log.txt"
    
    # Ensure output directory exists
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    log_lines = []
    log_lines.append(f"Schema Validation Report")
    log_lines.append(f"Schema: {schema_path}")
    log_lines.append(f"Timestamp: {Path(schema_path).stat().st_mtime}")
    log_lines.append("=" * 50)
    log_lines.append("")
    
    # Run yamllint
    log_lines.append("Running yamllint...")
    yamllint_errors = run_yamllint(schema_path)
    if yamllint_errors:
        log_lines.append("FAILED:")
        for err in yamllint_errors:
            log_lines.append(f"  - {err}")
    else:
        log_lines.append("PASSED: No yamllint issues found.")
    log_lines.append("")
    
    # Validate with jsonschema
    log_lines.append("Validating with jsonschema...")
    try:
        schema = load_yaml_schema(schema_path)
        jsonschema_errors = validate_schema_structure(schema)
        
        if jsonschema_errors:
            log_lines.append("FAILED: Schema structure issues found:")
            for err in jsonschema_errors:
                log_lines.append(f"  - {err}")
        else:
            log_lines.append("PASSED: Schema structure is valid.")
            
            # Try to compile the schema
            try:
                import jsonschema
                validator = jsonschema.Draft7Validator(schema)
                validator.check_schema(schema)
                log_lines.append("PASSED: Schema compiles successfully.")
            except jsonschema.exceptions.SchemaError as e:
                log_lines.append(f"FAILED: Schema compilation error: {str(e)}")
    except FileNotFoundError as e:
        log_lines.append(f"FAILED: {str(e)}")
    except Exception as e:
        log_lines.append(f"FAILED: Unexpected error: {str(e)}")
    
    log_lines.append("")
    log_lines.append("=" * 50)
    log_lines.append("Validation Complete")
    
    # Write log
    with open(output_file, 'w') as f:
        f.write('\n'.join(log_lines))
    
    print(f"Validation log written to: {output_path}")
    
    # Return exit code based on errors
    all_errors = yamllint_errors + jsonschema_errors if 'jsonschema_errors' in locals() else yamllint_errors
    return 0 if not all_errors else 1

if __name__ == "__main__":
    sys.exit(main())
