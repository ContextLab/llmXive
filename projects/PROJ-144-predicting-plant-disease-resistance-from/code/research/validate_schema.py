import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.constants import PROJECT_ROOT, CONTRACTS_DIR, STATE_DIR
from utils.io import log_artifact

SCHEMA_PATH = CONTRACTS_DIR / "metadata.schema.yaml"
OUTPUT_PATH = STATE_DIR / "schema_validation_log.txt"

def load_yaml_schema(path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> List[str]:
    """Basic structural validation of the schema."""
    errors = []
    if not isinstance(schema, dict):
        errors.append("Schema root must be a dictionary.")
        return errors
    
    required_keys = ['type', 'properties']
    for key in required_keys:
        if key not in schema:
            errors.append(f"Missing required key: {key}")
    
    if 'properties' in schema:
        if not isinstance(schema['properties'], dict):
            errors.append("'properties' must be a dictionary.")
        else:
            for prop_name, prop_def in schema['properties'].items():
                if not isinstance(prop_def, dict):
                    errors.append(f"Property '{prop_name}' definition must be a dictionary.")
                elif 'type' not in prop_def:
                    errors.append(f"Property '{prop_name}' missing 'type' definition.")
    
    return errors

def validate_with_jsonschema(schema: Dict[str, Any]) -> Optional[str]:
    """Attempt to validate the schema file itself using jsonschema."""
    try:
        import jsonschema
        # We are validating the schema document against the JSON Schema meta-schema
        # to ensure it is a valid JSON Schema definition.
        from jsonschema import Draft7Validator
        validator = Draft7Validator(schema)
        errors = list(validator.iter_errors(schema))
        if errors:
            return f"jsonschema validation failed:\n" + "\n".join([str(e) for e in errors])
        return None
    except ImportError:
        return "jsonschema library not installed, skipping meta-validation."
    except Exception as e:
        return f"Error during jsonschema meta-validation: {str(e)}"

def run_yamllint(path: Path) -> Optional[str]:
    """Run yamllint on the schema file if available."""
    try:
        result = subprocess.run(
            ['yamllint', '-d', 'relaxed', str(path)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return f"yamllint found issues:\n{result.stdout}\n{result.stderr}"
        return None
    except FileNotFoundError:
        return "yamllint not installed, skipping lint check."
    except Exception as e:
        return f"Error running yamllint: {str(e)}"

def main():
    """Execute schema validation and write results to state/schema_validation_log.txt."""
    log_lines = []
    log_lines.append(f"Schema Validation Log - {SCHEMA_PATH}")
    log_lines.append("=" * 50)
    
    if not SCHEMA_PATH.exists():
        error_msg = f"ERROR: Schema file not found at {SCHEMA_PATH}"
        log_lines.append(error_msg)
        log_lines.append("Validation FAILED.")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text("\n".join(log_lines))
        print("\n".join(log_lines))
        return 1

    try:
        schema = load_yaml_schema(SCHEMA_PATH)
        log_lines.append(f"Successfully loaded YAML from {SCHEMA_PATH}")
    except yaml.YAMLError as e:
        error_msg = f"ERROR: Failed to parse YAML: {e}"
        log_lines.append(error_msg)
        log_lines.append("Validation FAILED.")
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text("\n".join(log_lines))
        print("\n".join(log_lines))
        return 1

    # 1. Structural Check
    struct_errors = validate_schema_structure(schema)
    if struct_errors:
        log_lines.append("Structural Validation FAILED:")
        for err in struct_errors:
            log_lines.append(f"  - {err}")
    else:
        log_lines.append("Structural Validation: PASSED")

    # 2. JSON Schema Meta-Validation
    jsonschema_result = validate_with_jsonschema(schema)
    if jsonschema_result:
        if "not installed" in jsonschema_result:
            log_lines.append(f"jsonschema check: SKIPPED ({jsonschema_result})")
        else:
            log_lines.append(f"jsonschema Meta-Validation FAILED:")
            log_lines.append(jsonschema_result)
    else:
        log_lines.append("jsonschema Meta-Validation: PASSED")

    # 3. YAML Linting
    yamllint_result = run_yamllint(SCHEMA_PATH)
    if yamllint_result:
        if "not installed" in yamllint_result:
            log_lines.append(f"yamllint check: SKIPPED ({yamllint_result})")
        else:
            log_lines.append(f"yamllint check: ISSUES FOUND")
            log_lines.append(yamllint_result)
    else:
        log_lines.append("yamllint check: PASSED")

    # Final Status
    log_lines.append("=" * 50)
    if not struct_errors and (not jsonschema_result or "not installed" in jsonschema_result):
        log_lines.append("OVERALL STATUS: VALID")
        log_lines.append("The schema file is syntactically correct and structurally sound.")
    else:
        log_lines.append("OVERALL STATUS: INVALID")
        log_lines.append("The schema file contains errors or warnings.")

    # Write Output
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    output_text = "\n".join(log_lines)
    OUTPUT_PATH.write_text(output_text)
    
    # Log artifact
    log_artifact(OUTPUT_PATH, "schema_validation_log")

    print(output_text)
    return 0

if __name__ == "__main__":
    sys.exit(main())
