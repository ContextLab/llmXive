"""
Data validation utilities for PII scanning and schema validation.

This module provides functions to scan data for Personally Identifiable Information (PII)
and validate data structures against expected schemas.
"""

import re
from typing import Dict, Any, List, Optional, Tuple, Set
from pathlib import Path
import json
import csv


# Common PII patterns
PII_PATTERNS: Dict[str, re.Pattern] = {
    "email": re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
    "ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "phone_us": re.compile(r"\b(?:\+1[-.\s]?)?(?:\(?\d{3}\)?)[-.\s]?\d{3}[-.\s]?\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d{4}[-\s]?){3}\d{4}\b"),
    "ip_address": re.compile(r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{36,}"),
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "jwt": re.compile(r"eyJ[A-Za-z0-9-_=]+\.eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_.+/=]*"),
}


class ValidationResult:
    """Container for validation results."""

    def __init__(self, is_valid: bool, errors: List[str], warnings: List[str]):
        self.is_valid = is_valid
        self.errors = errors
        self.warnings = warnings

    def __repr__(self) -> str:
        status = "valid" if self.is_valid else "invalid"
        return f"ValidationResult(status={status}, errors={len(self.errors)}, warnings={len(self.warnings)})"


def scan_for_pii(text: str) -> List[Dict[str, Any]]:
    """
    Scan a string for potential PII patterns.

    Args:
        text: The text to scan.

    Returns:
        A list of dictionaries containing the type of PII found and the matched value.
    """
    findings = []
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        for match in matches:
            findings.append({
                "type": pii_type,
                "value": match,
                "location": text.find(match)
            })
    return findings


def scan_file_for_pii(file_path: str) -> List[Dict[str, Any]]:
    """
    Scan a file for potential PII patterns.

    Args:
        file_path: Path to the file to scan.

    Returns:
        A list of dictionaries containing the type of PII found and the matched value.
    """
    findings = []
    path = Path(file_path)
    if not path.exists():
        return findings

    try:
        # Determine if file is binary
        with open(path, "rb") as f:
            chunk = f.read(1024)
            if b"\x00" in chunk:
                return findings  # Skip binary files

        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            content = f.read()
            findings = scan_for_pii(content)
    except Exception:
        pass  # Skip files that can't be read

    return findings


def validate_schema(data: Any, schema: Dict[str, Any]) -> ValidationResult:
    """
    Validate data against a simple schema definition.

    Supported schema types:
    - "dict": expects a dictionary
    - "list": expects a list
    - "str", "int", "float", "bool": expects respective types
    - "required": list of required keys (for dict type)
    - "fields": dict mapping field names to their expected types (for dict type)

    Args:
        data: The data to validate.
        schema: The schema definition.

    Returns:
        ValidationResult indicating validity and any errors/warnings.
    """
    errors = []
    warnings = []

    schema_type = schema.get("type")
    if not schema_type:
        errors.append("Schema must specify a 'type'")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Type checking
    type_mapping = {
        "dict": dict,
        "list": list,
        "str": str,
        "int": int,
        "float": float,
        "bool": bool,
    }

    expected_type = type_mapping.get(schema_type)
    if expected_type and not isinstance(data, expected_type):
        errors.append(f"Expected type '{schema_type}', got '{type(data).__name__}'")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    # Dict-specific validations
    if schema_type == "dict" and isinstance(data, dict):
        required_keys = schema.get("required", [])
        for key in required_keys:
            if key not in data:
                errors.append(f"Missing required field: '{key}'")

        fields = schema.get("fields", {})
        for field_name, field_schema in fields.items():
            if field_name in data:
                field_result = validate_schema(data[field_name], field_schema)
                if not field_result.is_valid:
                    errors.extend([f"{field_name}: {e}" for e in field_result.errors])
                warnings.extend([f"{field_name}: {w}" for w in field_result.warnings])

    # List-specific validations
    if schema_type == "list" and isinstance(data, list):
        item_schema = schema.get("items")
        if item_schema:
            for idx, item in enumerate(data):
                item_result = validate_schema(item, item_schema)
                if not item_result.is_valid:
                    errors.extend([f"[{idx}]: {e}" for e in item_result.errors])

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_csv_schema(file_path: str, schema: Dict[str, Any]) -> ValidationResult:
    """
    Validate a CSV file against a schema definition.

    Args:
        file_path: Path to the CSV file.
        schema: Schema definition with 'type': 'list' and 'items' containing field definitions.

    Returns:
        ValidationResult indicating validity and any errors/warnings.
    """
    path = Path(file_path)
    if not path.exists():
        return ValidationResult(
            is_valid=False,
            errors=[f"File not found: {file_path}"],
            warnings=[]
        )

    errors = []
    warnings = []

    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames

            if not headers:
                return ValidationResult(
                    is_valid=False,
                    errors=["CSV file is empty or has no headers"],
                    warnings=[]
                )

            # Validate headers against schema fields
            item_schema = schema.get("items", {})
            expected_fields = item_schema.get("fields", {})
            required_fields = item_schema.get("required", [])

            # Check required fields
            for req_field in required_fields:
                if req_field not in headers:
                    errors.append(f"Missing required column: '{req_field}'")

            # Check for unexpected fields (warning)
            for header in headers:
                if header not in expected_fields:
                    warnings.append(f"Unexpected column found: '{header}'")

            # Validate row data
            row_count = 0
            for row in reader:
                row_count += 1
                for field_name, field_schema in expected_fields.items():
                    if field_name in row:
                        value = row[field_name]
                        # Basic type validation
                        field_type = field_schema.get("type")
                        if field_type:
                            try:
                                if field_type == "int":
                                    int(value)
                                elif field_type == "float":
                                    float(value)
                                elif field_type == "bool":
                                    if value.lower() not in ("true", "false", "1", "0"):
                                        warnings.append(f"Row {row_count}: '{field_name}' may not be a valid boolean")
                            except ValueError:
                                errors.append(f"Row {row_count}: '{field_name}' expected {field_type}, got '{value}'")
    except Exception as e:
        errors.append(f"Error reading CSV: {str(e)}")
        return ValidationResult(is_valid=False, errors=errors, warnings=warnings)

    if row_count == 0:
        warnings.append("CSV file has no data rows")

    return ValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings
    )


def validate_json_schema(file_path: str, schema: Dict[str, Any]) -> ValidationResult:
    """
    Validate a JSON file against a schema definition.

    Args:
        file_path: Path to the JSON file.
        schema: Schema definition.

    Returns:
        ValidationResult indicating validity and any errors/warnings.
    """
    path = Path(file_path)
    if not path.exists():
        return ValidationResult(
            is_valid=False,
            errors=[f"File not found: {file_path}"],
            warnings=[]
        )

    errors = []
    warnings = []

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Invalid JSON: {str(e)}"],
            warnings=[]
        )
    except Exception as e:
        return ValidationResult(
            is_valid=False,
            errors=[f"Error reading file: {str(e)}"],
            warnings=[]
        )

    return validate_schema(data, schema)


def generate_pii_report(scan_results: List[Dict[str, Any]], output_path: str) -> None:
    """
    Generate a PII scan report as a JSON file.

    Args:
        scan_results: List of PII findings from scan_file_for_pii.
        output_path: Path to write the report.
    """
    report = {
        "scan_summary": {
            "total_findings": len(scan_results),
            "findings_by_type": {}
        },
        "findings": scan_results
    }

    # Aggregate by type
    for finding in scan_results:
      pii_type = finding["type"]
      report["scan_summary"]["findings_by_type"][pii_type] = \
          report["scan_summary"]["findings_by_type"].get(pii_type, 0) + 1

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)