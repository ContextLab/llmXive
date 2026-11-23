import os
import sys
import json
import argparse
from pathlib import Path
import yaml

# Import JSON Schema validation
try:
    import jsonschema
except ImportError:
    print("ERROR: jsonschema library required. Install via: pip install jsonschema")
    sys.exit(1)

# Import Config for paths (tolerant of missing attributes)
from config import Config

def check_file_exists(file_path: str) -> bool:
    """Check if the specified file exists on disk."""
    path = Path(file_path)
    if not path.exists():
        print(f"ERROR: File not found: {file_path}")
        return False
    if not path.is_file():
        print(f"ERROR: Path exists but is not a file: {file_path}")
        return False
    return True

def load_schema(schema_path: str) -> dict:
    """Load a JSON Schema from a YAML or JSON file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        elif path.suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported schema format: {path.suffix}")

def validate_schema_compliance(input_file: str, schema_file: str) -> tuple[bool, list]:
    """
    Validate that the input JSONL file conforms to the provided JSON Schema.
    Returns (is_valid, list_of_errors).
    """
    errors = []
    try:
        schema = load_schema(schema_file)
    except Exception as e:
        return False, [f"Failed to load schema: {str(e)}"]

    if not os.path.exists(input_file):
        return False, [f"Input file not found: {input_file}"]

    line_count = 0
    valid_count = 0
    error_count = 0

    with open(input_file, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            line_count += 1
            try:
                record = json.loads(line)
                # Validate against schema
                jsonschema.validate(instance=record, schema=schema)
                valid_count += 1
            except jsonschema.exceptions.ValidationError as ve:
                error_count += 1
                errors.append(f"Line {line_num}: {ve.message}")
                # Stop early if too many errors to avoid log spam, but report the first few
                if len(errors) >= 10:
                    errors.append("... (truncated, see full log if needed)")
                    break
            except json.JSONDecodeError as je:
                error_count += 1
                errors.append(f"Line {line_num}: Invalid JSON - {str(je)}")
                if len(errors) >= 10:
                    errors.append("... (truncated)")
                    break

    is_valid = (error_count == 0)
    if not is_valid:
        print(f"Schema validation failed: {error_count} errors found in {line_count} lines.")
    else:
        print(f"Schema validation passed: {valid_count} records validated successfully.")
    
    return is_valid, errors

def run_dry_run(constraints_file: str, schema_file: str, output_file: str) -> bool:
    """
    Execute the dry-run validation.
    Checks file existence and schema compliance.
    Writes status to output_file.
    Returns True if dry-run passes (status: "pass"), False otherwise.
    """
    result = {
        "status": "fail",
        "checks": {},
        "errors": []
    }

    # Check 1: File Existence
    exists = check_file_exists(constraints_file)
    result["checks"]["file_exists"] = exists
    
    if not exists:
        result["errors"].append(f"Input file missing: {constraints_file}")
        # Still try to check schema file existence for completeness
        if not check_file_exists(schema_file):
            result["errors"].append(f"Schema file missing: {schema_file}")
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(result, f, indent=2)
        print(f"Dry-run status: FAIL (written to {output_file})")
        return False

    # Check 2: Schema Compliance
    is_valid, validation_errors = validate_schema_compliance(constraints_file, schema_file)
    result["checks"]["schema_valid"] = is_valid
    
    if not is_valid:
        result["errors"].extend(validation_errors)
    
    # Determine overall status
    if exists and is_valid:
        result["status"] = "pass"
        print("Dry-run status: PASS")
    else:
        result["status"] = "fail"
        print("Dry-run status: FAIL")

    # Write result
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2)
    
    print(f"Dry-run results written to: {output_file}")
    return result["status"] == "pass"

def main():
    parser = argparse.ArgumentParser(description="Dry-run validation for solver inputs.")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/derived/constraints.jsonl",
        help="Path to the constraints JSONL file to validate."
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="constraints.schema.yaml",
        help="Path to the JSON Schema file."
    )
    parser.add_argument(
        "--output",
        type=str,
        default="data/results/dry_run_status.json",
        help="Path to write the dry-run status JSON."
    )

    args = parser.parse_args()

    # Resolve paths relative to project root if absolute paths not provided
    # Assuming script runs from project root
    input_path = args.input
    schema_path = args.schema
    output_path = args.output

    success = run_dry_run(input_path, schema_path, output_path)
    
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
