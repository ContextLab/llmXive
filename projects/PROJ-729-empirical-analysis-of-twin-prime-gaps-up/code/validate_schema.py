"""
Schema Validation for Twin Prime Data.

Validates generated CSV data against the defined schema.
"""
import sys
import csv
import json
from pathlib import Path
from typing import Dict, Any, List

import yaml

from config import get_config, get_schema_path
from utils import setup_logging, exit_with_error

def load_schema(schema_path: Path) -> Dict[str, Any]:
    """Load schema from YAML file."""
    with open(schema_path, 'r') as f:
        return yaml.safe_load(f)

def validate_field(value: Any, field_def: Dict[str, Any]) -> List[str]:
    """Validate a single field against its definition."""
    errors = []
    field_name = field_def['name']
    field_type = field_def['type']
    constraints = field_def.get('constraints', {})

    # Handle null/empty checks first
    if value is None or value == '':
        if not constraints.get('nullable', False):
            errors.append(f"{field_name}: Value cannot be null")
        return errors

    # Type checking
    if field_type == 'integer':
        try:
            int_val = int(value)
            # Ensure it's not a float string like "3.0" if strict integer is required
            # But typically CSV reads strings, so int("3") is fine.
            # We just need to ensure it parses as an integer.
        except (ValueError, TypeError):
            errors.append(f"{field_name}: Expected integer, got {type(value).__name__} (value: {value})")
            return errors
    elif field_type == 'number':
        try:
            float(value)
        except (ValueError, TypeError):
            errors.append(f"{field_name}: Expected number, got {type(value).__name__} (value: {value})")
            return errors
    elif field_type == 'string':
        if not isinstance(value, str):
            errors.append(f"{field_name}: Expected string, got {type(value).__name__}")
            return errors

    # Constraint checking
    if 'minimum' in constraints:
        try:
            num_val = float(value)
            if num_val < constraints['minimum']:
                errors.append(f"{field_name}: Value {num_val} is less than minimum {constraints['minimum']}")
        except (ValueError, TypeError):
            # Already handled by type check, but safety net
            pass

    if 'maximum' in constraints:
        try:
            num_val = float(value)
            if num_val > constraints['maximum']:
                errors.append(f"{field_name}: Value {num_val} is greater than maximum {constraints['maximum']}")
        except (ValueError, TypeError):
            pass

    if 'pattern' in constraints:
        import re
        if not re.match(constraints['pattern'], str(value)):
            errors.append(f"{field_name}: Value '{value}' does not match pattern {constraints['pattern']}")

    return errors

def validate_csv(data_path: Path, schema: Dict[str, Any]) -> bool:
    """Validate CSV data against schema."""
    logger = setup_logging("validate_schema")
    errors = []
    row_count = 0

    fields = schema.get('fields', [])
    if not fields:
        logger.warning("Schema has no fields defined.")
        return True

    field_names = [f['name'] for f in fields]
    field_defs = {f['name']: f for f in fields}

    try:
        with open(data_path, 'r', newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            
            # Check header
            if reader.fieldnames != field_names:
                errors.append(f"CSV header mismatch. Expected: {field_names}, Got: {reader.fieldnames}")
                return False

            for row in reader:
                row_count += 1
                row_errors = []

                for field_name in field_names:
                    value = row.get(field_name)
                    field_errors = validate_field(value, field_defs[field_name])
                    row_errors.extend(field_errors)

                if row_errors:
                    errors.extend([f"Row {row_count}: {err}" for err in row_errors])
                    if len(errors) > 10:  # Limit error output
                        errors.append("... (truncated)")
                        break

    except FileNotFoundError:
        errors.append(f"Data file not found: {data_path}")
        return False
    except Exception as e:
        errors.append(f"Error reading CSV: {e}")
        return False

    if errors:
        logger.error(f"Validation failed with {len(errors)} errors:")
        for err in errors[:10]:
            logger.error(f"  - {err}")
        return False
    else:
        logger.info(f"Validation successful for {row_count} rows.")
        return True

def main():
    """Main entry point for schema validation."""
    logger = setup_logging("validate_schema")
    
    config = get_config()
    schema_path = get_schema_path(config)
    
    if not schema_path or not schema_path.exists():
        exit_with_error(f"Schema file not found: {schema_path}")
    
    data_path = Path(config['data_raw']) / "twin_primes.csv"
    
    if not data_path.exists():
        exit_with_error(f"Data file not found: {data_path}")
    
    logger.info(f"Validating {data_path} against {schema_path}")
    
    schema = load_schema(schema_path)
    is_valid = validate_csv(data_path, schema)
    
    if is_valid:
        logger.info("Schema validation PASSED")
        sys.exit(0)
    else:
        logger.error("Schema validation FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()
