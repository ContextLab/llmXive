import os
import sys
import csv
import json
import logging
import argparse
from pathlib import Path
from typing import List, Dict, Any

import yaml

from config import DataConfig
from utils.logger import get_logger


def setup_validation_logger() -> logging.Logger:
    """Setup logging for exclusion schema validation."""
    logger = get_logger("exclusion_schema_validation")
    logger.setLevel(logging.INFO)
    return logger


def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load the exclusion report schema from YAML."""
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    
    with open(schema_path, 'r') as f:
        schema = yaml.safe_load(f)
    
    return schema


def validate_row(row: Dict[str, Any], schema: Dict[str, Any], row_index: int) -> List[str]:
    """
    Validate a single row against the schema.
    Returns a list of error messages if validation fails, empty list otherwise.
    """
    errors = []
    schema_properties = schema.get("properties", {})
    
    required_fields = schema.get("required", [])
    
    # Check required fields
    for field in required_fields:
        if field not in row or row[field] is None:
            errors.append(f"Row {row_index}: Missing required field '{field}'")
    
    # Validate field types and constraints
    for field, value in row.items():
        if field not in schema_properties:
            # Optional field not in schema, or schema mismatch
            continue
        
        field_schema = schema_properties[field]
        
        # Check type
        expected_type = field_schema.get("type")
        if expected_type == "integer":
            if not isinstance(value, int):
                # Allow string if it looks like an integer, but strict check preferred
                try:
                    int(value)
                except ValueError:
                    errors.append(f"Row {row_index}: Field '{field}' must be integer, got {type(value)}")
        elif expected_type == "string":
            if not isinstance(value, str):
                errors.append(f"Row {row_index}: Field '{field}' must be string, got {type(value)}")
        
        # Check pattern/constraints if defined
        if "pattern" in field_schema and isinstance(value, str):
            import re
            if not re.match(field_schema["pattern"], value):
                errors.append(f"Row {row_index}: Field '{field}' does not match pattern '{field_schema['pattern']}'")
        
        if "enum" in field_schema:
            if value not in field_schema["enum"]:
                errors.append(f"Row {row_index}: Field '{field}' value '{value}' not in allowed values {field_schema['enum']}")
    
    return errors


def validate_exclusion_log(log_path: Path, schema_path: Path, output_path: Path) -> bool:
    """
    Validate the exclusion log against the schema.
    Writes validation results to the output log.
    Returns True if all rows are valid, False otherwise.
    """
    logger = setup_validation_logger()
    logger.info(f"Validating exclusion log: {log_path}")
    logger.info(f"Using schema: {schema_path}")
    
    if not log_path.exists():
        logger.error(f"Exclusion log not found: {log_path}")
        # Write error status to output
        with open(output_path, 'w') as f:
            f.write("status: FAIL\nreason: input_missing\n")
        return False
    
    schema = load_schema(schema_path)
    validation_errors = []
    valid_count = 0
    total_count = 0
    
    with open(log_path, 'r', newline='') as infile, open(output_path, 'w', newline='') as outfile:
        reader = csv.DictReader(infile)
        writer = csv.writer(outfile)
        
        # Write header for validation log
        writer.writerow(["row_index_in_file", "validation_status", "error_details"])
        
        for row_index, row in enumerate(reader, start=1):
            total_count += 1
            row_errors = validate_row(row, schema, row_index)
            
            if row_errors:
                validation_errors.extend(row_errors)
                writer.writerow([row_index, "FAIL", "; ".join(row_errors)])
            else:
                valid_count += 1
                writer.writerow([row_index, "PASS", ""])
    
    logger.info(f"Validation complete. Total: {total_count}, Valid: {valid_count}, Errors: {len(validation_errors)}")
    
    if validation_errors:
        logger.error("Validation failed with errors:")
        for err in validation_errors[:10]:  # Log first 10 errors
            logger.error(f"  - {err}")
        if len(validation_errors) > 10:
            logger.error(f"  ... and {len(validation_errors) - 10} more errors")
        
        # Write failure status
        with open(output_path, 'a') as f:
            f.write(f"\nstatus: FAIL\nreason: schema_violation\ncount: {len(validation_errors)}\n")
        return False
    else:
        logger.info("All rows validated successfully.")
        # Write success status
        with open(output_path, 'a') as f:
            f.write(f"\nstatus: PASS\ncount: {total_count}\n")
        return True


def main():
    """Main entry point for exclusion schema validation."""
    parser = argparse.ArgumentParser(description="Validate exclusion log against schema")
    parser.add_argument(
        "--log-path",
        type=str,
        default="data/processed/exclusion_raw.log",
        help="Path to the exclusion log file to validate"
    )
    parser.add_argument(
        "--schema-path",
        type=str,
        default="specs/001-predict-sn1-rate-constants/contracts/exclusion_report.schema.yaml",
        help="Path to the schema YAML file"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/processed/exclusion_validation.log",
        help="Path to write validation results"
    )
    
    args = parser.parse_args()
    
    log_path = Path(args.log_path)
    schema_path = Path(args.schema_path)
    output_path = Path(args.output_path)
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Check guard clause: schema must exist
    if not schema_path.exists():
        logger = setup_validation_logger()
        logger.error(f"Schema file missing: {schema_path}")
        # Write error to output
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            f.write("status: FAIL\nreason: schema_missing\n")
        sys.exit(1)
    
    success = validate_exclusion_log(log_path, schema_path, output_path)
    
    if not success:
        sys.exit(1)
    
    sys.exit(0)


if __name__ == "__main__":
    main()