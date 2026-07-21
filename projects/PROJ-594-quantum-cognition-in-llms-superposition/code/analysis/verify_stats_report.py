"""
Verification script for T032: Verify stats_report.json schema.

This script loads the generated stats report and asserts the presence
of required statistical fields: p-value, t-statistic, Cohen's d, and 95% CI.

It exits with code 0 if valid, or code 1 with a descriptive error if missing.
"""
import os
import sys
import json
import argparse

# Add parent directory to path to allow imports if run as script
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

REQUIRED_FIELDS = [
    "p_value",
    "t_statistic",
    "cohens_d",
    "confidence_interval_95"
]

def verify_report(report_path: str) -> bool:
    """
    Verifies that the stats report contains all required statistical fields.
    
    Args:
        report_path: Path to the stats_report.json file.
        
    Returns:
        True if all fields are present and non-null, False otherwise.
    """
    if not os.path.exists(report_path):
        print(f"ERROR: Report file not found: {report_path}")
        return False

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {report_path}: {e}")
        return False

    missing_fields = []
    null_fields = []

    for field in REQUIRED_FIELDS:
        if field not in data:
            missing_fields.append(field)
        elif data[field] is None:
            null_fields.append(field)

    if missing_fields:
        print(f"FAIL: Missing required fields: {missing_fields}")
        return False

    if null_fields:
        print(f"FAIL: Fields present but null: {null_fields}")
        return False

    # Validate structure of CI if it's a list
    ci = data.get("confidence_interval_95")
    if isinstance(ci, list):
        if len(ci) != 2:
            print(f"FAIL: confidence_interval_95 must be a list of 2 elements (lower, upper). Got {len(ci)}.")
            return False
        if not all(isinstance(x, (int, float)) for x in ci):
            print(f"FAIL: confidence_interval_95 elements must be numbers.")
            return False
    else:
        # Check if it's a dict with lower/upper keys
        if isinstance(ci, dict):
            if "lower" not in ci or "upper" not in ci:
                print(f"FAIL: confidence_interval_95 dict must have 'lower' and 'upper' keys.")
                return False
        else:
            print(f"FAIL: confidence_interval_95 must be a list or dict.")
            return False

    print("SUCCESS: stats_report.json contains all required fields:")
    print(f"  - p_value: {data['p_value']}")
    print(f"  - t_statistic: {data['t_statistic']}")
    print(f"  - cohens_d: {data['cohens_d']}")
    print(f"  - confidence_interval_95: {data['confidence_interval_95']}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Verify stats_report.json schema")
    parser.add_argument(
        "--report-path",
        type=str,
        default="projects/PROJ-594-quantum-cognition-in-llms-superposition/data/results/stats_report.json",
        help="Path to the stats_report.json file to verify"
    )
    args = parser.parse_args()

    success = verify_report(args.report_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()