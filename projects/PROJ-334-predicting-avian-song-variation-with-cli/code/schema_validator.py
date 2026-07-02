"""
Schema validation utilities for analysis outputs.
Validates CSVs against YAML schemas defined in specs/contracts.
"""
import os
import sys
import csv
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))

from utils import setup_logging

logger = setup_logging("schema_validation", "output/logs/schema_validation.log")

def load_schema(schema_path: str) -> Dict[str, Any]:
    """Load a YAML schema file."""
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def validate_csv_against_schema(csv_path: str, schema: Dict[str, Any]) -> List[str]:
    """
    Validate a CSV file against a JSON/YAML schema.
    Returns a list of error messages. Empty list means success.
    """
    errors = []
    csv_path = Path(csv_path)
    
    if not csv_path.exists():
        return [f"CSV file not found: {csv_path}"]

    # Read schema properties
    required_fields = schema.get("properties", {}).get("properties", {}).get("required", [])
    field_types = {}
    
    # Extract field type definitions from schema
    props = schema.get("properties", {}).get("properties", {}).get("properties", {})
    for field_name, field_def in props.items():
        if "type" in field_def:
            field_types[field_name] = field_def["type"]
        
        # Check for specific constraints
        if field_def.get("const") is not None:
            field_types[field_name] = "const"
            field_types[f"{field_name}_const"] = field_def["const"]

    try:
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return ["CSV file is empty or has no headers"]

            # Check required headers
            missing_headers = set(required_fields) - set(headers)
            if missing_headers:
                errors.append(f"Missing required columns: {missing_headers}")

            # Check for mandatory prefix in headers if specified
            # Note: The schema defines a column 'header_prefix' with const "Associational Analysis"
            # We check if this column exists and has the correct value in the first row
            if 'header_prefix' in headers:
                first_row = next(reader, None)
                if first_row:
                    if first_row.get('header_prefix') != "Associational Analysis":
                        errors.append("Column 'header_prefix' must have value 'Associational Analysis'")
                    # Reset reader to check data types (we consumed the first row)
                    # Re-open for simplicity or handle state
                    f.seek(0)
                    reader = csv.DictReader(f)
                    next(reader) # Skip header
            
            # Validate data types row by row
            row_num = 1
            for row in reader:
                row_num += 1
                for field, expected_type in field_types.items():
                    if field.startswith("properties."): continue # Skip nested schema defs
                    if field in ['header_prefix', 'properties', 'type']: continue # Skip schema metadata
                    
                    if field not in row:
                        continue # Already caught by missing_headers check
                    
                    value = row[field]
                    if value is None or value == '':
                        if field in required_fields:
                            errors.append(f"Row {row_num}: Column '{field}' is empty but required")
                        continue

                    if expected_type == "number":
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Row {row_num}: Column '{field}' is not a number: {value}")
                    
                    elif expected_type == "integer":
                        try:
                            int(value)
                        except ValueError:
                            errors.append(f"Row {row_num}: Column '{field}' is not an integer: {value}")
                    
                    elif expected_type == "boolean":
                        if value.lower() not in ('true', 'false', '1', '0'):
                            errors.append(f"Row {row_num}: Column '{field}' is not a boolean: {value}")
                    
                    elif expected_type == "const":
                        # This is handled by the specific const check above, but generic check here
                        pass

    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")

    return errors

def validate_task_output(csv_path: str, schema_path: str) -> bool:
    """
    Main entry point for validating the model_summary.csv.
    Returns True if valid, False otherwise.
    """
    logger.info(f"Validating {csv_path} against {schema_path}")
    try:
        schema = load_schema(schema_path)
        errors = validate_csv_against_schema(csv_path, schema)
        
        if errors:
            for err in errors:
                logger.error(err)
            return False
        
        logger.info("Validation successful.")
        return True
        
    except Exception as e:
        logger.error(f"Validation failed with exception: {e}")
        return False

if __name__ == "__main__":
    # Default paths relative to project root
    schema_file = "specs/001-predicting-avian-song-variation/contracts/analysis_output.schema.yaml"
    output_file = "output/models/model_summary.csv"
    
    # Allow override via args
    if len(sys.argv) > 1:
        output_file = sys.argv[1]
    if len(sys.argv) > 2:
        schema_file = sys.argv[2]

    success = validate_task_output(output_file, schema_file)
    sys.exit(0 if success else 1)
