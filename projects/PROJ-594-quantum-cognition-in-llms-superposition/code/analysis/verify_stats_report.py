"""
Task T032: Verify stats_report.json contains p-value, t-statistic, Cohen's d, and confidence interval.

This script validates the output of the statistical analysis (T031) to ensure
all required fields are present and populated by the bootstrap logic.
"""
import os
import sys
import json
import argparse

# Add project root to path if not already present
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

REPORT_PATH = "data/results/stats_report.json"

REQUIRED_KEYS = [
    "p_value",
    "t_statistic",
    "cohens_d",
    "ci_lower",
    "ci_upper",
    "conclusion"
]

def verify_report(report_path: str) -> bool:
    """
    Verify that the stats report JSON exists and contains all required fields
    with non-null values. Specifically checks that ci_lower and ci_upper are
    populated (not None/Null) as required by T030b bootstrap logic.

    Args:
        report_path: Path to the stats_report.json file.

    Returns:
        bool: True if validation passes, False otherwise.
    """
    if not os.path.exists(report_path):
        print(f"ERROR: Report file not found at {report_path}")
        return False

    try:
        with open(report_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        print(f"ERROR: Failed to parse JSON at {report_path}: {e}")
        return False

    missing_keys = []
    null_keys = []

    for key in REQUIRED_KEYS:
        if key not in data:
            missing_keys.append(key)
        elif data[key] is None:
            null_keys.append(key)

    if missing_keys:
        print(f"ERROR: Missing required keys in {report_path}: {missing_keys}")
        return False

    if null_keys:
        print(f"ERROR: Found null values for required keys in {report_path}: {null_keys}")
        return False

    # Specific check for CI bounds as per T030b requirement
    if not isinstance(data.get("ci_lower"), (int, float)):
        print(f"ERROR: ci_lower is not a valid number: {data.get('ci_lower')}")
        return False
    if not isinstance(data.get("ci_upper"), (int, float)):
        print(f"ERROR: ci_upper is not a valid number: {data.get('ci_upper')}")
        return False

    print(f"SUCCESS: {report_path} is valid.")
    print(f"  - p_value: {data['p_value']}")
    print(f"  - t_statistic: {data['t_statistic']}")
    print(f"  - cohens_d: {data['cohens_d']}")
    print(f"  - ci_lower: {data['ci_lower']}")
    print(f"  - ci_upper: {data['ci_upper']}")
    print(f"  - conclusion: {data['conclusion']}")
    return True

def main():
    parser = argparse.ArgumentParser(description="Verify stats_report.json structure and content.")
    parser.add_argument(
        "--report-path",
        type=str,
        default=REPORT_PATH,
        help=f"Path to the stats report JSON (default: {REPORT_PATH})"
    )
    args = parser.parse_args()

    success = verify_report(args.report_path)
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()