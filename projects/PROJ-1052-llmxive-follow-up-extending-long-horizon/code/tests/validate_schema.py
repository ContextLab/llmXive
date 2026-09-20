import json
import sys
import argparse
from pathlib import Path
from jsonschema import validate, ValidationError, Draft7Validator

def validate_jsonl_against_schema(input_path: str, schema_path: str) -> bool:
    """
    Validates every line in a JSONL file against a JSON schema.
    """
    schema_path_obj = Path(schema_path)
    input_path_obj = Path(input_path)

    if not schema_path_obj.exists():
        print(f"ERROR: Schema file not found: {schema_path}")
        return False
    
    if not input_path_obj.exists():
        print(f"ERROR: Input file not found: {input_path}")
        return False

    # Load schema
    with open(schema_path_obj, 'r', encoding='utf-8') as f:
        schema = json.load(f)

    validator = Draft7Validator(schema)
    
    errors_found = 0
    total_lines = 0

    with open(input_path_obj, 'r', encoding='utf-8') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            
            total_lines += 1
            try:
                data = json.loads(line)
                errors = list(validator.iter_errors(data))
                if errors:
                    errors_found += 1
                    print(f"Line {line_num} validation failed:")
                    for error in errors:
                        print(f"  - {error.message} (path: {list(error.path)})")
            except json.JSONDecodeError as e:
                errors_found += 1
                print(f"Line {line_num} JSON decode error: {e}")

    print(f"Validation complete. Total lines: {total_lines}, Errors: {errors_found}")
    
    if errors_found > 0:
        print("VALIDATION FAILED")
        return False
    else:
        print("VALIDATION PASSED")
        return True

def main():
    parser = argparse.ArgumentParser(description="Validate JSONL file against JSON schema")
    parser.add_argument("--input", required=True, help="Path to input JSONL file")
    parser.add_argument("--schema", required=True, help="Path to JSON schema file")
    args = parser.parse_args()

    success = validate_jsonl_against_schema(args.input, args.schema)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
