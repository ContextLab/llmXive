import os
import sys
import csv
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

try:
    from jsonschema import validate, ValidationError, SchemaError
except ImportError:
    raise ImportError("The 'jsonschema' package is required. Install it via 'pip install jsonschema'.")

from utils.logging_config import setup_general_logger, get_logger

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
LOGS_DIR = PROJECT_ROOT / "logs"
LOGS_DIR.mkdir(parents=True, exist_ok=True)

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """
    Load a JSON Schema from a YAML or JSON file.
    """
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r', encoding='utf-8') as f:
        if schema_path.suffix in ['.yaml', '.yml']:
            schema = yaml.safe_load(f)
        else:
            schema = json.load(f)
    
    if not isinstance(schema, dict):
        raise ValueError(f"Schema file {schema_path} did not parse into a dictionary.")
    
    return schema

def validate_csv_against_schema(csv_path: Path, schema: Dict[str, Any]) -> List[str]:
    """
    Validates a CSV file against a JSON Schema.
    
    Since JSON Schema is for JSON, we treat each row of the CSV as a JSON object
    and validate it individually. We also validate that the required columns
    exist in the header.
    
    Returns a list of validation error messages.
    """
    errors = []
    
    if not csv_path.exists():
        errors.append(f"ERROR: CSV file not found: {csv_path}")
        return errors

    try:
        with open(csv_path, 'r', encoding='utf-8', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                errors.append("ERROR: CSV file is empty or has no headers.")
                return errors

            # 1. Validate Schema Structure (properties)
            schema_properties = schema.get("properties", {})
            schema_required = schema.get("required", [])
            
            missing_required_cols = set(schema_required) - set(headers)
            if missing_required_cols:
                errors.append(f"ERROR: Missing required columns in {csv_path.name}: {missing_required_cols}")
            
            # 2. Validate Row Data
            if "type" in schema and schema["type"] != "object":
                errors.append(f"WARNING: Schema type is '{schema['type']}', expected 'object' for row validation. Attempting anyway.")

            row_count = 0
            for row_idx, row in enumerate(reader, start=2): # Start at 2 because row 1 is header
                row_count += 1
                # Filter row to only include keys present in schema properties if strict mode desired,
                # but usually we validate what's there.
                # Ensure types match if specified
                for col, value in row.items():
                    if col not in schema_properties:
                        continue # Ignore extra columns not in schema unless 'additionalProperties': False
                    
                    prop_schema = schema_properties[col]
                    expected_type = prop_schema.get("type")
                    
                    if value is None or value == '':
                        if prop_schema.get("type") != "null" and not (expected_type == "string" and "null" in prop_schema.get("anyOf", [])):
                            # Check if it's allowed to be null/empty
                            if "null" not in [t if isinstance(t, str) else t.get("type") for t in prop_schema.get("anyOf", [])]:
                                errors.append(f"Row {row_idx}, Column '{col}': Value is empty, but schema expects '{expected_type}'")
                        continue

                    # Basic type coercion and validation
                    if expected_type == "number":
                        try:
                            float(value)
                        except ValueError:
                            errors.append(f"Row {row_idx}, Column '{col}': Value '{value}' is not a number")
                    elif expected_type == "integer":
                        try:
                            int(value)
                        except ValueError:
                            errors.append(f"Row {row_idx}, Column '{col}': Value '{value}' is not an integer")
                    elif expected_type == "boolean":
                        if value.lower() not in ['true', 'false', '1', '0']:
                            errors.append(f"Row {row_idx}, Column '{col}': Value '{value}' is not a boolean")
                    elif expected_type == "string":
                        pass # Strings are fine
                    
                    # Check patterns if defined
                    if "pattern" in prop_schema:
                        import re
                        if not re.match(prop_schema["pattern"], str(value)):
                            errors.append(f"Row {row_idx}, Column '{col}': Value '{value}' does not match pattern '{prop_schema['pattern']}'")
                    
                    # Check minimum/maximum for numbers
                    if expected_type in ["number", "integer"]:
                        num_val = float(value)
                        if "minimum" in prop_schema and num_val < prop_schema["minimum"]:
                            errors.append(f"Row {row_idx}, Column '{col}': Value {num_val} is below minimum {prop_schema['minimum']}")
                        if "maximum" in prop_schema and num_val > prop_schema["maximum"]:
                            errors.append(f"Row {row_idx}, Column '{col}': Value {num_val} is above maximum {prop_schema['maximum']}")

            if row_count == 0:
                errors.append("WARNING: CSV file contains no data rows.")
                
    except Exception as e:
        errors.append(f"ERROR reading CSV: {str(e)}")

    return errors

def main():
    logger = setup_general_logger("validate_csv_schema")
    logger.info("Starting CSV Schema Validation (T032a)")

    # Configuration based on task description
    schema_path = PROJECT_ROOT / "specs" / "001-neural-entropy-cognitive-flexibility" / "contracts" / "correlation_results.schema.yaml"
    csv_path = PROJECT_ROOT / "data" / "processed" / "correlation_results_fdr.csv"
    output_path = LOGS_DIR / "validation_results.txt"

    # Check existence
    if not schema_path.exists():
        msg = f"Schema file not found at {schema_path}. Task cannot proceed."
        logger.error(msg)
        # Write error to output file
        with open(output_path, 'w') as f:
            f.write(f"VALIDATION FAILED: {msg}\n")
        return 1

    if not csv_path.exists():
        msg = f"Data file not found at {csv_path}. Task cannot proceed."
        logger.error(msg)
        with open(output_path, 'w') as f:
            f.write(f"VALIDATION FAILED: {msg}\n")
        return 1

    try:
        schema = load_schema(schema_path)
        logger.info(f"Schema loaded successfully from {schema_path}")
        
        errors = validate_csv_against_schema(csv_path, schema)
        
        with open(output_path, 'w') as f:
            f.write(f"Validation Report for: {csv_path.name}\n")
            f.write(f"Schema: {schema_path.name}\n")
            f.write(f"Status: {'PASSED' if not errors else 'FAILED'}\n")
            f.write("-" * 50 + "\n")
            
            if errors:
                f.write(f"Found {len(errors)} error(s):\n")
                for err in errors:
                    f.write(f"  - {err}\n")
            else:
                f.write("No validation errors found. All rows conform to the schema.\n")
        
        if errors:
            logger.error(f"Validation FAILED with {len(errors)} errors. Check {output_path}")
            return 1
        else:
            logger.info("Validation PASSED. Results written to logs/validation_results.txt")
            return 0

    except Exception as e:
        logger.exception(f"Unexpected error during validation: {e}")
        with open(output_path, 'w') as f:
            f.write(f"VALIDATION ERROR: {str(e)}\n")
        return 1

if __name__ == "__main__":
    sys.exit(main())