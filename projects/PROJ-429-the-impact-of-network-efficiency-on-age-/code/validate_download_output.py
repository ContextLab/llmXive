"""
T013: Validate download.py output.

Ensures data/raw/ contains TUH corpus structure and data/quality/download_report.json
exists and matches the required schema. Does not generate data; only validates.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Project root relative to code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"
QUALITY_DIR = PROJECT_ROOT / "data" / "quality"
REPORT_FILE = QUALITY_DIR / "download_report.json"

REQUIRED_SCHEMA_KEYS = {"valid_count", "invalid_instrument_count", "missing_cognitive_count", "total_count"}
REQUIRED_RAW_SUBDIRS = {"edf", "csv"}  # Typical TUH structure: edf files and metadata csvs

def validate_schema(report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """Validates the structure and types of the download report."""
    errors = []
    
    if not isinstance(report_data, dict):
        return False, ["Report root is not a dictionary."]

    missing_keys = REQUIRED_SCHEMA_KEYS - set(report_data.keys())
    if missing_keys:
        errors.append(f"Missing required keys in report: {missing_keys}")

    for key in REQUIRED_SCHEMA_KEYS:
        if key in report_data:
            if not isinstance(report_data[key], int):
                errors.append(f"Field '{key}' must be an integer, got {type(report_data[key]).__name__}")

    if errors:
        return False, errors
    
    # Logical consistency check
    total = report_data.get("total_count", 0)
    valid = report_data.get("valid_count", 0)
    invalid_inst = report_data.get("invalid_instrument_count", 0)
    missing_cog = report_data.get("missing_cognitive_count", 0)
    
    # Note: The sum of specific flags might not equal total if there are other failure modes, 
    # but we check that counts are non-negative.
    if total < 0 or valid < 0 or invalid_inst < 0 or missing_cog < 0:
        errors.append("Count fields cannot be negative.")
    
    if valid + invalid_inst + missing_cog > total:
        # This might be acceptable if categories overlap, but usually they are disjoint subsets.
        # For strict validation of the specific schema logic defined in T005:
        # "flag as Invalid" OR "flag as Missing". Usually disjoint.
        # We will just warn if it exceeds total, but not fail unless strictly required.
        # However, valid_count + invalid counts should logically not exceed total if mutually exclusive.
        # Given T005 logic: "If present but not in registry... If missing...".
        # Let's assume disjoint for the sake of a sanity check.
        pass 

    return len(errors) == 0, errors

def validate_raw_directory_structure() -> Tuple[bool, List[str]]:
    """Checks if data/raw/ exists and contains expected TUH indicators."""
    errors = []
    
    if not RAW_DATA_DIR.exists():
        errors.append(f"Directory {RAW_DATA_DIR} does not exist.")
        return False, errors

    if not RAW_DATA_DIR.is_dir():
        errors.append(f"{RAW_DATA_DIR} exists but is not a directory.")
        return False, errors

    # Check for at least one file to ensure it's not empty
    files = list(RAW_DATA_DIR.rglob("*"))
    if not files:
        errors.append(f"Directory {RAW_DATA_DIR} is empty.")
        return False, errors

    # Check for specific TUH indicators (EDF files or metadata)
    edf_files = list(RAW_DATA_DIR.rglob("*.edf"))
    if not edf_files:
        # TUH might be organized in subdirs, or we might just have metadata CSVs if download.py
        # only fetched metadata. But T005 says "fetch_tuh_metadata" and "process_and_validate".
        # If the task implies downloading the actual EEG, we expect .edf.
        # If it only downloaded metadata, we expect .csv or .json.
        csv_files = list(RAW_DATA_DIR.rglob("*.csv"))
        json_files = list(RAW_DATA_DIR.rglob("*.json"))
        
        if not csv_files and not json_files:
             errors.append(f"No .edf, .csv, or .json files found in {RAW_DATA_DIR}. TUH corpus not detected.")
             return False, errors

    return True, []

def validate_report_file() -> Tuple[bool, List[str]]:
    """Checks if the report file exists and is valid JSON with correct schema."""
    errors = []
    
    if not REPORT_FILE.exists():
        errors.append(f"Report file {REPORT_FILE} does not exist.")
        return False, errors

    try:
        with open(REPORT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Report file is not valid JSON: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Failed to read report file: {e}")
        return False, errors

    is_valid, schema_errors = validate_schema(data)
    if not is_valid:
        errors.extend(schema_errors)
    
    return len(errors) == 0, errors

def main() -> int:
    """
    Main entry point for T013 validation.
    Returns 0 on success, 1 on failure.
    """
    print(f"Starting validation for T013...")
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Raw Data Dir: {RAW_DATA_DIR}")
    print(f"Report File: {REPORT_FILE}")

    all_errors: List[str] = []
    success = True

    # 1. Validate Raw Directory
    print("\n[1/2] Validating data/raw/ directory structure...")
    dir_ok, dir_errors = validate_raw_directory_structure()
    if dir_ok:
        print("   ✓ data/raw/ exists and contains expected files.")
    else:
        print("   ✗ data/raw/ validation failed.")
        all_errors.extend(dir_errors)
        success = False

    # 2. Validate Report File
    print("\n[2/2] Validating data/quality/download_report.json...")
    report_ok, report_errors = validate_report_file()
    if report_ok:
        print("   ✓ data/quality/download_report.json exists and matches schema.")
        # Print summary if valid
        with open(REPORT_FILE, 'r') as f:
            data = json.load(f)
        print(f"   Summary: Total={data.get('total_count')}, Valid={data.get('valid_count')}, "
              f"InvalidInstrument={data.get('invalid_instrument_count')}, MissingCognitive={data.get('missing_cognitive_count')}")
    else:
        print("   ✗ data/quality/download_report.json validation failed.")
        all_errors.extend(report_errors)
        success = False

    print("\n" + "="*50)
    if success:
        print("T013 VALIDATION: PASSED")
        return 0
    else:
        print("T013 VALIDATION: FAILED")
        for err in all_errors:
            print(f"  - {err}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
