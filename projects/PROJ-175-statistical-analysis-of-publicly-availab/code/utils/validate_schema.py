import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
import yaml

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SchemaValidationError(Exception):
    """Custom exception for schema validation errors."""
    pass

def load_schema(schema_path: str) -> Dict[str, Any]:
    """
    Load a YAML schema definition from a file.

    Args:
        schema_path (str): Path to the schema YAML file.

    Returns:
        Dict[str, Any]: The schema definition as a dictionary.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the YAML file is malformed.
    """
    path = Path(schema_path)
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")

    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
        return schema
    except yaml.YAMLError as e:
        logger.error(f"Error parsing YAML schema: {e}")
        raise

def validate_field(value: Any, field_def: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate a single field value against its definition.

    Args:
        value (Any): The value to validate.
        field_def (Dict[str, Any]): The field definition from the schema.

    Returns:
        Tuple[bool, Optional[str]]: (is_valid, error_message)
    """
    field_name = field_def.get('name', 'unknown')
    field_type = field_def.get('type')
    nullable = field_def.get('nullable', False)
    enum = field_def.get('enum')
    min_value = field_def.get('min_value')
    max_value = field_def.get('max_value')

    # Check for null
    if value is None:
        if nullable:
            return True, None
        else:
            return False, f"Field '{field_name}' cannot be null."

    # Check type
    if field_type == 'string' and not isinstance(value, str):
        return False, f"Field '{field_name}' must be a string."
    elif field_type == 'integer' and not isinstance(value, int):
        return False, f"Field '{field_name}' must be an integer."
    elif field_type == 'float' and not isinstance(value, (int, float)):
        return False, f"Field '{field_name}' must be a float."
    elif field_type == 'boolean' and not isinstance(value, bool):
        return False, f"Field '{field_name}' must be a boolean."
    elif field_type == 'object' and not isinstance(value, dict):
        return False, f"Field '{field_name}' must be an object."

    # Check enum
    if enum is not None:
        if value not in enum:
            return False, f"Field '{field_name}' value '{value}' not in allowed enum: {enum}."

    # Check numeric bounds
    if isinstance(value, (int, float)):
        if min_value is not None and value < min_value:
            return False, f"Field '{field_name}' value {value} is below minimum {min_value}."
        if max_value is not None and value > max_value:
            return False, f"Field '{field_name}' value {value} is above maximum {max_value}."

    return True, None

def validate_dataframe(data: List[Dict[str, Any]], schema: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate a list of records (rows) against a schema.

    Args:
        data (List[Dict[str, Any]]): List of records to validate.
        schema (Dict[str, Any]): The schema definition.

    Returns:
        Tuple[bool, List[str]]: (is_valid, list_of_errors)
    """
    errors = []
    fields = schema.get('fields', [])
    constraints = schema.get('constraints', [])

    # Check required fields
    field_names = {f['name'] for f in fields}
    if not data:
        logger.warning("Data is empty. Skipping row validation.")
        # Still check constraints if any
        for constraint in constraints:
            if "No null values" in constraint:
                pass # Cannot verify without data
        return len(errors) == 0, errors

    for row_idx, row in enumerate(data):
        if not isinstance(row, dict):
            errors.append(f"Row {row_idx} is not a dictionary.")
            continue

        # Check for missing fields
        for field in fields:
            if field['name'] not in row:
                errors.append(f"Row {row_idx}: Missing field '{field['name']}'.")
                continue

            # Validate value
            is_valid, error_msg = validate_field(row[field['name']], field)
            if not is_valid:
                errors.append(f"Row {row_idx}: {error_msg}")

    # Check global constraints (simplified for this implementation)
    # In a real system, this might involve cross-field logic or complex queries
    for constraint in constraints:
        if "No null values" in constraint and data:
            # We already checked per-field nullability, but if a constraint says "No null values allowed in primary key"
            # we should ensure the primary key (usually first field or specified) is not null.
            pk_field = fields[0]['name'] if fields else None
            if pk_field:
                for row_idx, row in enumerate(data):
                    if row.get(pk_field) is None:
                        errors.append(f"Row {row_idx}: Primary key '{pk_field}' is null, violating constraint.")

    return len(errors) == 0, errors

def validate_schema(data_path: str, schema_path: str) -> Dict[str, Any]:
    """
    Main function to validate a data file against a schema.
    Assumes data is a JSON file containing a list of records.

    Args:
        data_path (str): Path to the data JSON file.
        schema_path (str): Path to the schema YAML file.

    Returns:
        Dict[str, Any]: Validation report.
    """
    report = {
        "schema_path": schema_path,
        "data_path": data_path,
        "is_valid": False,
        "errors": [],
        "row_count": 0
    }

    try:
        schema = load_schema(schema_path)
    except Exception as e:
        report["errors"].append(f"Failed to load schema: {str(e)}")
        return report

    try:
        with open(data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        report["errors"].append(f"Data file not found: {data_path}")
        return report
    except json.JSONDecodeError as e:
        report["errors"].append(f"Invalid JSON in data file: {str(e)}")
        return report

    if not isinstance(data, list):
        report["errors"].append("Data file must contain a list of records.")
        return report

    report["row_count"] = len(data)
    is_valid, errors = validate_dataframe(data, schema)
    report["is_valid"] = is_valid
    report["errors"] = errors

    return report

def save_validation_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Save the validation report to a JSON file.

    Args:
        report (Dict[str, Any]): The validation report.
        output_path (str): Path to save the report.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    logger.info(f"Validation report saved to {output_path}")

def main():
    """
    Command-line entry point for schema validation.
    Usage: python -m utils.validate_schema --data <data_path> --schema <schema_path> --output <output_path>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Validate data against a schema.")
    parser.add_argument("--data", required=True, help="Path to the data JSON file.")
    parser.add_argument("--schema", required=True, help="Path to the schema YAML file.")
    parser.add_argument("--output", required=True, help="Path to save the validation report.")

    args = parser.parse_args()

    try:
        report = validate_schema(args.data, args.schema)
        save_validation_report(report, args.output)

        if report["is_valid"]:
            print(f"Validation successful. {report['row_count']} rows validated.")
            sys.exit(0)
        else:
            print(f"Validation failed with {len(report['errors'])} errors.")
            for err in report["errors"]:
                print(f"  - {err}")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        sys.exit(2)

if __name__ == "__main__":
    main()