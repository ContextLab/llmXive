"""
Network Schema Loader and Validator.

Provides utilities to load the network schema and validate CSV data
against the defined structure in contracts/network_schema.schema.yaml.
"""
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import csv
import json

SCHEMA_PATH = Path(__file__).parent.parent.parent / "contracts" / "network_schema.schema.yaml"


def load_schema(schema_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load the network schema from the YAML file.

    Args:
        schema_path: Optional path to the schema file. Defaults to the
                     project's contracts/network_schema.schema.yaml.

    Returns:
        Dictionary containing the loaded schema.

    Raises:
        FileNotFoundError: If the schema file does not exist.
        yaml.YAMLError: If the schema file is not valid YAML.
    """
    path = schema_path or SCHEMA_PATH
    if not path.exists():
        raise FileNotFoundError(f"Schema file not found: {path}")

    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _validate_row_against_schema(row: Dict[str, str], schema: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate a single row (dictionary) against the schema.

    Args:
        row: Dictionary representing a CSV row.
        schema: The loaded JSON schema.

    Returns:
        Tuple of (is_valid, error_message).
    """
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    # Check required fields
    missing = set(required) - set(row.keys())
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    # Validate types and constraints
    for field, value in row.items():
        if field not in properties:
            # Allow additional properties if not explicitly forbidden,
            # but schema says additionalProperties: false, so we should flag.
            # However, for robustness in validation, we might just warn or skip.
            # Strict adherence:
            return False, f"Unexpected field: {field}"

        prop_def = properties[field]
        p_type = prop_def.get("type")

        try:
            if p_type == "string":
                if not isinstance(value, str):
                    return False, f"Field '{field}' must be string"
                if "pattern" in prop_def:
                    import re
                    if not re.match(prop_def["pattern"], value):
                        return False, f"Field '{field}' does not match pattern"
                if "enum" in prop_def and value not in prop_def["enum"]:
                    return False, f"Field '{field}' value '{value}' not in enum {prop_def['enum']}"
                if "minLength" in prop_def and len(value) < prop_def["minLength"]:
                    return False, f"Field '{field}' too short"

            elif p_type == "integer":
                try:
                    int_val = int(value)
                    if "minimum" in prop_def and int_val < prop_def["minimum"]:
                        return False, f"Field '{field}' below minimum"
                    if "maximum" in prop_def and int_val > prop_def["maximum"]:
                        return False, f"Field '{field}' above maximum"
                except ValueError:
                    return False, f"Field '{field}' must be integer"

            elif p_type == "number":
                try:
                    float_val = float(value)
                    if "minimum" in prop_def:
                        if prop_def.get("exclusiveMinimum", False):
                            if float_val <= prop_def["minimum"]:
                                return False, f"Field '{field}' must be > {prop_def['minimum']}"
                        else:
                            if float_val < prop_def["minimum"]:
                                return False, f"Field '{field}' below minimum"
                    if "maximum" in prop_def and float_val > prop_def["maximum"]:
                        return False, f"Field '{field}' above maximum"
                except ValueError:
                    return False, f"Field '{field}' must be number"

        except Exception as e:
            return False, f"Validation error for '{field}': {str(e)}"

    return True, ""


def validate_csv_against_schema(
    csv_path: Path,
    schema: Optional[Dict[str, Any]] = None
) -> Tuple[bool, list]:
    """
    Validate a CSV file against the network schema.

    Args:
        csv_path: Path to the CSV file to validate.
        schema: Optional pre-loaded schema. If None, loads from default path.

    Returns:
        Tuple of (is_valid, list of error messages).
    """
    if schema is None:
        schema = load_schema()

    if not csv_path.exists():
        return False, [f"CSV file not found: {csv_path}"]

    errors = []
    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        # Check header matches expected fields
        expected_fields = set(schema.get("properties", {}).keys())
        actual_fields = set(reader.fieldnames or [])

        missing_headers = expected_fields - actual_fields
        if missing_headers:
            errors.append(f"Missing CSV columns: {', '.join(missing_headers)}")
            # If headers are missing, we can't validate rows properly
            return False, errors

        for i, row in enumerate(reader, start=2): # Start at 2 (1-based index + header)
            valid, msg = _validate_row_against_schema(row, schema)
            if not valid:
                errors.append(f"Row {i}: {msg}")
                # Fail fast on first error or collect all? Collect all for better debugging.
                # For strict validation, we might stop. Let's collect all.

    return len(errors) == 0, errors
