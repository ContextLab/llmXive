import sys
import json
import yaml
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

from utils.io import log_artifact

SCHEMA_PATH = Path("contracts/metadata.schema.yaml")
OUTPUT_LOG = Path("state/schema_validation_log.txt")

def load_yaml_schema(path: Path) -> Dict[str, Any]:
    """Load a YAML schema file."""
    with open(path, 'r') as f:
        return yaml.safe_load(f)

def validate_schema_structure(schema: Dict[str, Any]) -> List[str]:
    """Basic structural validation of the schema."""
    errors = []
    if "$schema" not in schema:
        errors.append("Missing '$schema' key.")
    if "type" not in schema:
        errors.append("Missing 'type' key at root.")
    if "$defs" not in schema:
        errors.append("Missing '$defs' key for definitions.")
    else:
        if "MetaboliteProfile" not in schema["$defs"]:
            errors.append("Missing 'MetaboliteProfile' definition.")
        if "ResistanceLabel" not in schema["$defs"]:
            errors.append("Missing 'ResistanceLabel' definition.")
    return errors

def validate_with_jsonschema(schema: Dict[str, Any]) -> List[str]:
    """Validate the schema syntax using jsonschema library."""
    try:
        import jsonschema
        # Validate the schema itself against the meta-schema
        jsonschema.validate(schema, jsonschema.Draft7Validator.META_SCHEMA)
        return []
    except ImportError:
        return ["jsonschema library not installed. Install with: pip install jsonschema"]
    except jsonschema.exceptions.SchemaError as e:
        return [f"Schema validation error: {e.message}"]
    except Exception as e:
        return [f"Unexpected error during schema validation: {e}"]

def run_yamllint(path: Path) -> List[str]:
    """Run yamllint on the schema file."""
    try:
        result = subprocess.run(
            ["yamllint", "-f", "parsable", str(path)],
            capture_output=True,
            text=True,
            check=False
        )
        if result.returncode != 0:
            return result.stdout.splitlines()
        return []
    except FileNotFoundError:
        return ["yamllint not found. Install with: pip install yamllint"]
    except Exception as e:
        return [f"Error running yamllint: {e}"]

def main():
    """Main entry point to validate the schema."""
    log_lines = []
    log_lines.append(f"Validating schema: {SCHEMA_PATH}")
    log_lines.append("-" * 40)

    if not SCHEMA_PATH.exists():
        log_lines.append(f"ERROR: Schema file not found at {SCHEMA_PATH}")
        OUTPUT_LOG.write_text("\n".join(log_lines))
        sys.exit(1)

    # 1. Load YAML
    try:
        schema = load_yaml_schema(SCHEMA_PATH)
        log_lines.append("YAML loaded successfully.")
    except Exception as e:
        log_lines.append(f"ERROR: Failed to load YAML: {e}")
        OUTPUT_LOG.write_text("\n".join(log_lines))
        sys.exit(1)

    # 2. Check Structure
    structural_errors = validate_schema_structure(schema)
    if structural_errors:
        log_lines.append("Structural validation failed:")
        for err in structural_errors:
            log_lines.append(f"  - {err}")
    else:
        log_lines.append("Structural validation passed.")

    # 3. Validate with jsonschema
    jsonschema_errors = validate_with_jsonschema(schema)
    if jsonschema_errors:
        log_lines.append("JSON Schema validation failed:")
        for err in jsonschema_errors:
            log_lines.append(f"  - {err}")
    else:
        log_lines.append("JSON Schema validation passed.")

    # 4. Run yamllint
    yamllint_errors = run_yamllint(SCHEMA_PATH)
    if yamllint_errors:
        log_lines.append("Yamllint found issues:")
        for err in yamllint_errors:
            log_lines.append(f"  - {err}")
    else:
        log_lines.append("Yamllint passed.")

    log_lines.append("-" * 40)
    if structural_errors or jsonschema_errors or yamllint_errors:
        log_lines.append("VALIDATION RESULT: FAILED")
        print("Validation FAILED. Check state/schema_validation_log.txt")
    else:
        log_lines.append("VALIDATION RESULT: PASSED")
        print("Validation PASSED. See state/schema_validation_log.txt")

    # Write log
    OUTPUT_LOG.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_LOG.write_text("\n".join(log_lines))
    
    # Log artifact hash
    from utils.io import compute_file_hash
    hash_val = compute_file_hash(str(OUTPUT_LOG))
    log_artifact(str(OUTPUT_LOG), hash_val)

if __name__ == "__main__":
    main()
