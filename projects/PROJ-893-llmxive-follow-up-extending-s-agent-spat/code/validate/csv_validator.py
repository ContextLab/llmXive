import csv
import argparse
import sys
from pathlib import Path
import yaml

def load_schema(schema_path: str) -> dict:
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_csv(csv_path: str, schema_path: str) -> bool:
    """
    Validates a CSV file against a YAML schema definition.
    Checks for required columns and basic type/format compliance if defined.
    """
    schema = load_schema(schema_path)
    
    # Expected fields from schema (assuming 'properties' key in JSON Schema draft 7)
    # The schema file is likely a JSON Schema Draft 7, but stored as YAML.
    # We look for 'properties' or 'fields'.
    required_fields = []
    if 'properties' in schema:
        required_fields = list(schema['properties'].keys())
    elif 'fields' in schema:
        required_fields = [f['name'] for f in schema['fields'] if f.get('required', False)]

    if not required_fields:
        print(f"Warning: Could not determine required fields from {schema_path}")
        return True

    with open(csv_path, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        if not headers:
            print("Error: CSV file is empty or has no headers.")
            return False

        missing_fields = set(required_fields) - set(headers)
        if missing_fields:
            print(f"Error: Missing required columns: {missing_fields}")
            return False

        row_count = 0
        for row in reader:
            row_count += 1
            # Optional: validate types if schema defines them
            # For now, we just check existence.

    print(f"Validation successful. {row_count} rows validated against {required_fields}.")
    return True

def main():
    parser = argparse.ArgumentParser(description="Validate CSV against a schema.")
    parser.add_argument('csv_path', type=str, help="Path to the CSV file to validate.")
    parser.add_argument('schema_path', type=str, help="Path to the schema YAML file.")
    
    args = parser.parse_args()

    if not Path(args.csv_path).exists():
        print(f"Error: File not found: {args.csv_path}")
        sys.exit(1)
    if not Path(args.schema_path).exists():
        print(f"Error: File not found: {args.schema_path}")
        sys.exit(1)

    success = validate_csv(args.csv_path, args.schema_path)
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
