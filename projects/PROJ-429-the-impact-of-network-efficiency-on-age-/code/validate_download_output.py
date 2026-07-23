"""
Validate the output of the data download and preprocessing pipeline.

This script verifies:
1. The existence and structure of the data/raw/ directory containing TUH corpus files.
2. The existence and schema compliance of data/quality/download_report.json.

It does NOT generate data; it only validates what has been produced by download.py.
"""
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

from config import ensure_dirs

# Expected schema for download_report.json
REPORT_SCHEMA_KEYS = {
    "valid_count": int,
    "invalid_instrument_count": int,
    "missing_cognitive_count": int,
    "total_count": int
}

def validate_schema(report_data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validate that the report data matches the expected schema.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not isinstance(report_data, dict):
        errors.append("Report data is not a dictionary")
        return False, errors
    
    for key, expected_type in REPORT_SCHEMA_KEYS.items():
        if key not in report_data:
            errors.append(f"Missing required key: {key}")
        elif not isinstance(report_data[key], expected_type):
            errors.append(f"Key '{key}' has wrong type: expected {expected_type.__name__}, got {type(report_data[key]).__name__}")
        elif report_data[key] < 0:
            errors.append(f"Key '{key}' has negative value: {report_data[key]}")
    
    # Cross-validation: sum check
    if "valid_count" in report_data and "invalid_instrument_count" in report_data and "missing_cognitive_count" in report_data and "total_count" in report_data:
        calculated_sum = report_data["valid_count"] + report_data["invalid_instrument_count"] + report_data["missing_cognitive_count"]
        if calculated_sum != report_data["total_count"]:
            errors.append(f"Count mismatch: valid({report_data['valid_count']}) + invalid({report_data['invalid_instrument_count']}) + missing({report_data['missing_cognitive_count']}) != total({report_data['total_count']})")
    
    return len(errors) == 0, errors

def validate_raw_directory_structure(raw_dir: Path) -> Tuple[bool, List[str]]:
    """
    Validate that the raw data directory contains expected TUH corpus structure.
    
    Checks for:
    - Presence of subdirectories (e.g., 'abnormal', 'normal' or similar TUH structure)
    - Presence of at least one .edf or .bdf file
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not raw_dir.exists():
        errors.append(f"Raw directory does not exist: {raw_dir}")
        return False, errors
    
    if not raw_dir.is_dir():
        errors.append(f"Raw path is not a directory: {raw_dir}")
        return False, errors
    
    # Look for common TUH EEG subdirectories
    expected_subdirs = ['abnormal', 'normal', 'train', 'test']
    found_subdirs = [d for d in raw_dir.iterdir() if d.is_dir()]
    
    if not found_subdirs:
        errors.append(f"No subdirectories found in {raw_dir}. Expected TUH corpus structure (e.g., 'abnormal', 'normal').")
    else:
        # Check if any subdirectory matches expected TUH patterns
        matched = False
        for subdir in found_subdirs:
            if any(expected in subdir.name.lower() for expected in expected_subdirs):
                matched = True
                break
        
        if not matched:
            errors.append(f"Subdirectories found but none match expected TUH patterns: {[d.name for d in found_subdirs]}")
    
    # Check for EEG files
    eeg_extensions = ['.edf', '.bdf', '.vhdr']
    eeg_files = []
    for ext in eeg_extensions:
        eeg_files.extend(list(raw_dir.rglob(f'*{ext}')))
    
    if not eeg_files:
        errors.append(f"No EEG files (.edf, .bdf, .vhdr) found in {raw_dir}")
    else:
        # Report count of found files (info, not error)
        print(f"  Found {len(eeg_files)} EEG files in {raw_dir}")
    
    return len(errors) == 0, errors

def validate_report_file(report_path: Path) -> Tuple[bool, List[str]]:
    """
    Validate the download_report.json file.
    
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    if not report_path.exists():
        errors.append(f"Report file does not exist: {report_path}")
        return False, errors
    
    try:
        with open(report_path, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"Invalid JSON in report file: {e}")
        return False, errors
    except Exception as e:
        errors.append(f"Error reading report file: {e}")
        return False, errors
    
    # Validate schema
    is_valid, schema_errors = validate_schema(report_data)
    if not is_valid:
        errors.extend(schema_errors)
    
    return len(errors) == 0, errors

def main():
    """Main validation entry point."""
    print("=== Validating Download Output ===")
    
    # Ensure directories exist (though we are validating, not creating)
    ensure_dirs()
    
    project_root = Path(__file__).resolve().parent.parent
    raw_dir = project_root / 'data' / 'raw'
    report_path = project_root / 'data' / 'quality' / 'download_report.json'
    
    all_valid = True
    validation_results = {}
    
    # Validate raw directory structure
    print(f"\n1. Validating raw directory: {raw_dir}")
    raw_valid, raw_errors = validate_raw_directory_structure(raw_dir)
    validation_results['raw_directory'] = {
        'valid': raw_valid,
        'errors': raw_errors
    }
    if not raw_valid:
        all_valid = False
        print("   ❌ FAILED")
        for err in raw_errors:
            print(f"      - {err}")
    else:
        print("   ✅ PASSED")
    
    # Validate report file
    print(f"\n2. Validating report file: {report_path}")
    report_valid, report_errors = validate_report_file(report_path)
    validation_results['report_file'] = {
        'valid': report_valid,
        'errors': report_errors
    }
    if not report_valid:
        all_valid = False
        print("   ❌ FAILED")
        for err in report_errors:
            print(f"      - {err}")
    else:
        # Print summary from report
        with open(report_path, 'r') as f:
            report_data = json.load(f)
        print("   ✅ PASSED")
        print(f"   Summary: Total={report_data['total_count']}, "
              f"Valid={report_data['valid_count']}, "
              f"Invalid Instrument={report_data['invalid_instrument_count']}, "
              f"Missing Cognitive={report_data['missing_cognitive_count']}")
    
    print("\n=== Validation Summary ===")
    if all_valid:
        print("✅ All validations passed.")
        return 0
    else:
        print("❌ Some validations failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
