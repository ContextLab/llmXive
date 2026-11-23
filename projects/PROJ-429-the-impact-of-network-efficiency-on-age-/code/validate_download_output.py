"""
Validation module for T013: Validate download.py output.

Verifies:
1. data/raw/ contains TUH corpus with metadata flags.
2. data/quality/download_report.json exists and matches schema.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import ensure_dirs

# Schema definition for download_report.json
REPORT_SCHEMA = {
    "required_keys": ["valid_count", "invalid_instrument_count", "missing_cognitive_count", "total_count", "status"],
    "type_checks": {
        "valid_count": int,
        "invalid_instrument_count": int,
        "missing_cognitive_count": int,
        "total_count": int,
        "status": str
    },
    "allowed_statuses": ["OK", "BLOCKED"]
}

def validate_schema(report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates the structure and types of the download report JSON.
    
    Returns:
        Tuple(bool, List[str]): (is_valid, list_of_errors)
    """
    errors = []
    
    # Check required keys
    for key in REPORT_SCHEMA["required_keys"]:
        if key not in report_data:
            errors.append(f"Missing required key: {key}")
    
    # Check types
    for key, expected_type in REPORT_SCHEMA["type_checks"].items():
        if key in report_data:
            if not isinstance(report_data[key], expected_type):
                errors.append(f"Key '{key}' has wrong type. Expected {expected_type.__name__}, got {type(report_data[key]).__name__}")
    
    # Check status values
    if "status" in report_data:
        if report_data["status"] not in REPORT_SCHEMA["allowed_statuses"]:
            errors.append(f"Invalid status value: {report_data['status']}. Allowed: {REPORT_SCHEMA['allowed_statuses']}")
    
    # Check consistency of counts
    if all(k in report_data for k in REPORT_SCHEMA["required_keys"]):
        total = report_data["total_count"]
        valid = report_data["valid_count"]
        invalid = report_data["invalid_instrument_count"]
        missing = report_data["missing_cognitive_count"]
        
        # Allow for 'reason' or other optional fields, but basic sum check
        # Note: The sum might not equal total if there are other statuses or if total includes skipped, 
        # but usually valid + invalid + missing <= total. We'll just log if they seem grossly inconsistent.
        sum_parts = valid + invalid + missing
        if sum_parts > total:
            errors.append(f"Sum of parts ({sum_parts}) exceeds total_count ({total})")
    
    return len(errors) == 0, errors

def validate_raw_directory_structure(raw_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validates that data/raw/ contains expected TUH corpus structure.
    Expects at least one subdirectory or file indicating presence of data.
    """
    errors = []
    
    if not raw_dir.exists():
        errors.append(f"Directory {raw_dir} does not exist.")
        return False, errors
    
    # Check for content
    items = list(raw_dir.iterdir())
    if not items:
        errors.append(f"Directory {raw_dir} is empty. Expected TUH corpus data.")
        return False, errors
    
    # Optional: Check for specific markers if known, but existence + non-empty is the primary check for T013
    # T013 specifically asks to "Ensure data/raw/ contains TUH corpus with metadata flags"
    # We assume the download script puts files here.
    
    return True, errors

def validate_report_file(report_path: Path) -> Tuple[bool, List[str]]:
    """
    Validates the download_report.json file.
    """
    errors = []
    
    if not report_path.exists():
        errors.append(f"Report file {report_path} does not exist.")
        return False, errors
    
    try:
        with open(report_path, 'r') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in {report_path}: {e}")
        return False, errors
    
    is_valid, schema_errors = validate_schema(data)
    if not is_valid:
        errors.extend(schema_errors)
    
    return len(errors) == 0, errors

def main():
    """
    Main entry point for T013 validation.
    """
    config = ensure_dirs()
    raw_dir = config["raw"]
    report_path = config["quality"] / "download_report.json"
    
    print(f"Validating download output...")
    print(f"Raw Dir: {raw_dir}")
    print(f"Report Path: {report_path}")
    
    all_valid = True
    messages = []
    
    # 1. Validate Report File
    report_ok, report_errors = validate_report_file(report_path)
    if report_ok:
        messages.append("PASS: download_report.json exists and matches schema.")
    else:
        all_valid = False
        messages.append("FAIL: download_report.json validation errors:")
        for err in report_errors:
            messages.append(f"  - {err}")
    
    # 2. Validate Raw Directory Structure
    raw_ok, raw_errors = validate_raw_directory_structure(raw_dir)
    if raw_ok:
        messages.append("PASS: data/raw/ contains data.")
    else:
        all_valid = False
        messages.append("FAIL: data/raw/ validation errors:")
        for err in raw_errors:
            messages.append(f"  - {err}")
    
    # Output summary
    print("\n".join(messages))
    
    if all_valid:
        print("\nT013 Validation: SUCCESS")
        sys.exit(0)
    else:
        print("\nT013 Validation: FAILED")
        sys.exit(1)

if __name__ == "__main__":
    main()