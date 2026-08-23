"""
Final Power & Sensitivity Review Script (Task T132).

This script validates the presence and integrity of:
1. data/results/power_analysis_report.json
2. data/results/sensitivity_analysis.csv

It ensures these artifacts meet the requirements of SC-005 (Power Analysis)
and SC-002 (Sensitivity Analysis) by checking for required fields,
valid data types, and logical consistency.

It does NOT generate synthetic data or fake results. It only reads
existing artifacts produced by the pipeline (T080 and T078).
"""
import os
import sys
import json
import csv
from pathlib import Path
from typing import Dict, Any, List, Optional

# Project root relative to script location
PROJECT_ROOT = Path(__file__).parent.parent
DATA_RESULTS_DIR = PROJECT_ROOT / "data" / "results"

POWER_REPORT_PATH = DATA_RESULTS_DIR / "power_analysis_report.json"
SENSITIVITY_CSV_PATH = DATA_RESULTS_DIR / "sensitivity_analysis.csv"

# SC-005 Requirements (Power Analysis)
SC005_REQUIRED_FIELDS = [
    "observed_n",
    "required_n",
    "power_observed",
    "effect_size",
    "alpha",
    "status",  # e.g., "Underpowered", "Adequate"
    "minimum_n_calculated"
]

# SC-002 Requirements (Sensitivity Analysis)
SC002_REQUIRED_THRESHOLDS = ["p<0.01", "p<0.05", "p<0.10"]
SC002_REQUIRED_COLUMNS = ["threshold", "significant_count", "total_tests", "proportion"]


def check_file_exists(path: Path) -> bool:
    if not path.exists():
        print(f"CRITICAL: Required file not found: {path}")
        return False
    return True


def validate_power_report() -> Dict[str, Any]:
    """Validates data/results/power_analysis_report.json against SC-005."""
    errors = []
    warnings = []
    report_data = {}

    if not check_file_exists(POWER_REPORT_PATH):
        return {"valid": False, "errors": ["File missing"], "data": None}

    try:
        with open(POWER_REPORT_PATH, 'r') as f:
            report_data = json.load(f)
    except json.JSONDecodeError as e:
        return {"valid": False, "errors": [f"Invalid JSON: {e}"], "data": None}

    # Check required fields
    missing_fields = [field for field in SC005_REQUIRED_FIELDS if field not in report_data]
    if missing_fields:
        errors.append(f"Missing required SC-005 fields: {missing_fields}")

    # Validate types and logic
    if "observed_n" in report_data and "required_n" in report_data:
        obs_n = report_data["observed_n"]
        req_n = report_data["required_n"]
        if not isinstance(obs_n, (int, float)) or not isinstance(req_n, (int, float)):
            errors.append("observed_n and required_n must be numeric.")
        else:
            # Check consistency with status flag
            status = report_data.get("status", "")
            if obs_n < req_n and "Underpowered" not in status:
                warnings.append(f"Observed N ({obs_n}) < Required N ({req_n}), but status is '{status}'. Expected 'Underpowered'.")
            elif obs_n >= req_n and "Underpowered" in status:
                warnings.append(f"Observed N ({obs_n}) >= Required N ({req_n}), but status is '{status}'.")

    if "power_observed" in report_data:
        pow_val = report_data["power_observed"]
        if not isinstance(pow_val, (int, float)) or not (0 <= pow_val <= 1):
            errors.append(f"power_observed must be between 0 and 1. Got: {pow_val}")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data": report_data
    }


def validate_sensitivity_csv() -> Dict[str, Any]:
    """Validates data/results/sensitivity_analysis.csv against SC-002."""
    errors = []
    warnings = []
    row_count = 0

    if not check_file_exists(SENSITIVITY_CSV_PATH):
        return {"valid": False, "errors": ["File missing"], "data": None}

    try:
        with open(SENSITIVITY_CSV_PATH, 'r', newline='') as f:
            reader = csv.DictReader(f)
            headers = reader.fieldnames
            
            if not headers:
                return {"valid": False, "errors": ["CSV is empty or has no headers"], "data": None}

            missing_cols = [col for col in SC002_REQUIRED_COLUMNS if col not in headers]
            if missing_cols:
                errors.append(f"Missing required SC-002 columns: {missing_cols}")

            thresholds_found = []
            for row in reader:
                row_count += 1
                threshold = row.get("threshold", "")
                thresholds_found.append(threshold)
                
                # Validate numeric fields
                try:
                    sig_count = float(row.get("significant_count", 0))
                    total_tests = float(row.get("total_tests", 0))
                    if total_tests <= 0:
                        warnings.append(f"Row {row_count}: total_tests is {total_tests}, skipping proportion check.")
                    else:
                        calc_prop = sig_count / total_tests
                        reported_prop = float(row.get("proportion", 0))
                        if abs(calc_prop - reported_prop) > 0.001:
                            warnings.append(f"Row {row_count}: Proportion mismatch. Calculated {calc_prop:.4f}, Reported {reported_prop:.4f}")
                except ValueError:
                    errors.append(f"Row {row_count}: Non-numeric value in count/proportion columns.")

            # Check if all expected thresholds are present
            missing_thresholds = [t for t in SC002_REQUIRED_THRESHOLDS if t not in thresholds_found]
            if missing_thresholds:
                warnings.append(f"Missing expected thresholds in CSV: {missing_thresholds}")

    except Exception as e:
        return {"valid": False, "errors": [f"CSV parsing error: {e}"], "data": None}

    if row_count == 0:
        errors.append("CSV file contains no data rows.")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "data": {"row_count": row_count, "thresholds_found": thresholds_found}
    }


def main():
    print("=" * 60)
    print("FINAL POWER & SENSITIVITY REVIEW (T132)")
    print("=" * 60)

    # Validate Power Analysis (SC-005)
    print("\n[1/2] Validating Power Analysis Report (SC-005)...")
    power_result = validate_power_report()
    if power_result["valid"]:
        print("   ✓ Power report structure is valid.")
        if power_result["warnings"]:
            for w in power_result["warnings"]:
                print(f"   ! Warning: {w}")
        if power_result["data"]:
            print(f"   - Observed N: {power_result['data'].get('observed_n')}")
            print(f"   - Required N: {power_result['data'].get('required_n')}")
            print(f"   - Status: {power_result['data'].get('status')}")
    else:
        print("   ✗ Power report validation FAILED.")
        for e in power_result["errors"]:
            print(f"   - Error: {e}")

    # Validate Sensitivity Analysis (SC-002)
    print("\n[2/2] Validating Sensitivity Analysis CSV (SC-002)...")
    sens_result = validate_sensitivity_csv()
    if sens_result["valid"]:
        print("   ✓ Sensitivity CSV structure is valid.")
        if sens_result["warnings"]:
            for w in sens_result["warnings"]:
                print(f"   ! Warning: {w}")
        print(f"   - Rows analyzed: {sens_result['data'].get('row_count')}")
    else:
        print("   ✗ Sensitivity CSV validation FAILED.")
        for e in sens_result["errors"]:
            print(f"   - Error: {e}")

    # Final Verdict
    print("\n" + "=" * 60)
    if power_result["valid"] and sens_result["valid"]:
        print("RESULT: PASS - All artifacts meet SC-005 and SC-002 requirements.")
        sys.exit(0)
    else:
        print("RESULT: FAIL - One or more artifacts do not meet requirements.")
        sys.exit(1)


if __name__ == "__main__":
    main()