"""
Validators for schema validation and PII scanning.

This module provides utilities to:
1. Validate data records against expected schemas.
2. Scan text fields for potential Personally Identifiable Information (PII).
"""

import re
from typing import Any, Dict, List, Optional, Tuple

# Regex patterns for common PII
PII_PATTERNS = {
    "email": re.compile(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"),
    "us_ssn": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "credit_card": re.compile(r"\b(?:\d[ -]*?){13,16}\b"),
    "ip_address": re.compile(r"\b(?:\d{1,3}\.){3}\d{1,3}\b"),
    "phone_us": re.compile(r"(?:\+1[-.\s]?)?(?:\(?\d{3}\)?[-.\s]?)\d{3}[-.\s]?\d{4}"),
}

class ValidationError(Exception):
    """Raised when a record fails schema validation."""
    pass

def validate_schema(record: Dict[str, Any], schema: Dict[str, type]) -> Tuple[bool, List[str]]:
    """
    Validate a single record against a schema definition.

    Args:
        record: The data record (dict) to validate.
        schema: A dictionary mapping field names to expected types.

    Returns:
        Tuple of (is_valid, list_of_error_messages).
    """
    errors = []
    for field, expected_type in schema.items():
        if field not in record:
            errors.append(f"Missing required field: {field}")
            continue

        value = record[field]
        # Handle optional fields or allow None if type is not strictly enforced for None
        if value is None:
            continue

        # Basic type checking (str, int, float, bool, list, dict)
        if not isinstance(value, expected_type):
            # Special case: bool is a subclass of int in Python, so we check bool explicitly if needed
            if expected_type == int and isinstance(value, bool):
                errors.append(f"Field '{field}' is bool, expected int.")
            else:
                errors.append(f"Field '{field}' is {type(value).__name__}, expected {expected_type.__name__}.")

    is_valid = len(errors) == 0
    return is_valid, errors

def scan_pii(text: str) -> Dict[str, List[str]]:
    """
    Scan a text string for potential PII matches.

    Args:
        text: The text to scan.

    Returns:
        Dictionary mapping PII type to list of found values.
    """
    findings = {key: [] for key in PII_PATTERNS}
    for pii_type, pattern in PII_PATTERNS.items():
        matches = pattern.findall(text)
        if matches:
            findings[pii_type] = list(set(matches)) # Deduplicate
    return findings

def validate_batch(records: List[Dict[str, Any]], schema: Dict[str, type]) -> Dict[str, Any]:
    """
    Validate a batch of records against a schema.

    Args:
        records: List of records to validate.
        schema: Schema definition.

    Returns:
        Dictionary with 'valid_count', 'invalid_count', and 'errors' (list of dicts).
    """
    valid_count = 0
    invalid_count = 0
    errors = []

    for idx, record in enumerate(records):
        is_valid, record_errors = validate_schema(record, schema)
        if is_valid:
            valid_count += 1
        else:
            invalid_count += 1
            errors.append({
                "index": idx,
                "record_id": record.get("pr_id", record.get("snippet_id", "unknown")),
                "errors": record_errors
            })

    return {
        "valid_count": valid_count,
        "invalid_count": invalid_count,
        "errors": errors
    }

def scan_dataset_for_pii(records: List[Dict[str, Any]], text_fields: List[str]) -> Dict[str, Any]:
    """
    Scan specific text fields in a dataset for PII.

    Args:
        records: List of records.
        text_fields: List of field names to scan.

    Returns:
        Dictionary with 'total_scanned', 'pii_found_count', and 'findings' (list of dicts).
    """
    findings_list = []
    pii_found_count = 0

    for idx, record in enumerate(records):
        for field in text_fields:
            if field in record and isinstance(record[field], str):
                text = record[field]
                field_findings = scan_pii(text)
                # Flatten findings for this field
                found_items = {k: v for k, v in field_findings.items() if v}
                if found_items:
                    pii_found_count += 1
                    findings_list.append({
                        "index": idx,
                        "field": field,
                        "record_id": record.get("pr_id", record.get("snippet_id", "unknown")),
                        "findings": found_items
                    })

    return {
        "total_scanned": len(records),
        "pii_found_count": pii_found_count,
        "findings": findings_list
    }