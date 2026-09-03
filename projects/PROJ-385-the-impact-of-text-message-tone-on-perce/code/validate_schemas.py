"""
Utility module for loading and validating data against YAML/JSON schemas.
"""
import csv
import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import yaml

try:
    import jsonschema
except ImportError:
    jsonschema = None


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load a schema from a YAML or JSON file."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, "r", encoding="utf-8") as f:
        if schema_path.suffix in [".yaml", ".yml"]:
            return yaml.safe_load(f)
        else:
            return json.load(f)


def validate_json_against_schema(json_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """Validate a JSON file against a schema."""
    errors = []
    
    if not json_path.exists():
        return False, [f"JSON file not found: {json_path}"]
    
    if not schema_path.exists():
        return False, [f"Schema file not found: {schema_path}"]
    
    if jsonschema is None:
        return False, ["jsonschema library not installed. Install with: pip install jsonschema"]
    
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        schema = load_schema(schema_path)
        jsonschema.validate(instance=data, schema=schema)
        return True, []
    except jsonschema.ValidationError as e:
        errors.append(f"Validation error: {e.message} at path {list(e.path)}")
        return False, errors
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON: {e}")
        return False, errors


def validate_csv_against_schema(csv_path: Path, schema_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate a CSV file against a schema.
    Checks that all required columns exist and that data types are consistent.
    """
    errors = []
    
    if not csv_path.exists():
        return False, [f"CSV file not found: {csv_path}"]
    
    if not schema_path.exists():
        return False, [f"Schema file not found: {schema_path}"]
    
    schema = load_schema(schema_path)
    required_columns = schema.get("required", [])
    properties = schema.get("properties", {})
    
    try:
        with open(csv_path, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if headers is None:
                return False, ["CSV file is empty or has no headers"]
            
            # Check required columns
            missing_columns = set(required_columns) - set(headers)
            if missing_columns:
                errors.append(f"Missing required columns: {missing_columns}")
                return False, errors
            
            # Validate data types row by row (basic check)
            for row_num, row in enumerate(reader, start=2):
                for col_name, col_schema in properties.items():
                    if col_name in row:
                        value = row[col_name]
                        expected_type = col_schema.get("type")
                        
                        if expected_type == "integer":
                            try:
                                int(value)
                            except ValueError:
                                errors.append(f"Row {row_num}, column '{col_name}': expected integer, got '{value}'")
                        elif expected_type == "number":
                            try:
                                float(value)
                            except ValueError:
                                errors.append(f"Row {row_num}, column '{col_name}': expected number, got '{value}'")
                        elif expected_type == "string":
                            if not isinstance(value, str):
                                errors.append(f"Row {row_num}, column '{col_name}': expected string, got {type(value)}")
                        
                        # Check enum constraints
                        if "enum" in col_schema:
                            if value not in col_schema["enum"]:
                                errors.append(f"Row {row_num}, column '{col_name}': value '{value}' not in allowed values {col_schema['enum']}")
                        
                        # Check minimum/maximum for numbers
                        if expected_type in ["integer", "number"]:
                            num_val = float(value)
                            if "minimum" in col_schema and num_val < col_schema["minimum"]:
                                errors.append(f"Row {row_num}, column '{col_name}': value {num_val} below minimum {col_schema['minimum']}")
                            if "maximum" in col_schema and num_val > col_schema["maximum"]:
                                errors.append(f"Row {row_num}, column '{col_name}': value {num_val} above maximum {col_schema['maximum']}")
    
    except csv.Error as e:
        errors.append(f"CSV parsing error: {e}")
        return False, errors
    
    if errors:
        return False, errors
    
    return True, []


def main():
    """CLI entry point for schema validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate data files against schemas")
    parser.add_argument("--data", type=str, required=True, help="Path to data file (CSV or JSON)")
    parser.add_argument("--schema", type=str, required=True, help="Path to schema file (YAML or JSON)")
    parser.add_argument("--output", type=str, default=None, help="Output file for errors (optional)")
    
    args = parser.parse_args()
    
    data_path = Path(args.data)
    schema_path = Path(args.schema)
    
    is_valid, errors = [], []
    
    if data_path.suffix == ".csv":
        is_valid, errors = validate_csv_against_schema(data_path, schema_path)
    elif data_path.suffix in [".json"]:
        is_valid, errors = validate_json_against_schema(data_path, schema_path)
    else:
        print(f"Unsupported file type: {data_path.suffix}")
        sys.exit(1)
    
    if is_valid:
        print(f"Validation successful: {data_path}")
        sys.exit(0)
    else:
        print(f"Validation failed for {data_path}:")
        for err in errors:
            print(f"  - {err}")
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                json.dump({"valid": False, "errors": errors}, f, indent=2)
        sys.exit(1)


if __name__ == "__main__":
    main()