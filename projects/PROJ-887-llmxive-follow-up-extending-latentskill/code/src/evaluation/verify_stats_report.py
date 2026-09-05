import json
import sys
from pathlib import Path
from typing import Any, Dict, List

# Required fields as per T032a and T077
REQUIRED_FIELDS = [
    "mean_success_rate",
    "bh_corrected_primary",
    "bh_corrected_sensitivity",
    "linearity_correlation_coefficient",
    "reconstruction_error",
    "memory_footprint",
    "observed_success_rate_diff",
    "power_estimate",
    "bh_rejected_count",
    "status_linearity",
    "warnings"
]

def load_report(path: Path) -> Dict[str, Any]:
    """Load the stats report JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Results file not found: {path}")
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)

def validate_structure(report: Dict[str, Any]) -> List[str]:
    """
    Validate that the report contains all required fields.
    Returns a list of missing fields.
    """
    missing = []
    for field in REQUIRED_FIELDS:
        if field not in report:
            missing.append(field)
    return missing

def main():
    """
    Verify that data/results/stats_report.json contains all required fields.
    Exit with code 0 if valid, 1 if invalid or missing.
    """
    project_root = Path(__file__).resolve().parents[3]
    report_path = project_root / "data" / "results" / "stats_report.json"

    print(f"Verifying report at: {report_path}")

    try:
        report = load_report(report_path)
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in report: {e}")
        sys.exit(1)

    missing_fields = validate_structure(report)

    if missing_fields:
        print(f"VALIDATION FAILED: Missing required fields: {missing_fields}")
        sys.exit(1)

    # Additional specific checks for complex fields
    if not isinstance(report.get("warnings"), list):
        print("VALIDATION FAILED: 'warnings' must be a list.")
        sys.exit(1)

    if not isinstance(report.get("reconstruction_error"), dict):
        print("VALIDATION FAILED: 'reconstruction_error' must be an object.")
        sys.exit(1)
    else:
        re = report["reconstruction_error"]
        if "mean" not in re or "max" not in re:
            print("VALIDATION FAILED: 'reconstruction_error' must contain 'mean' and 'max'.")
            sys.exit(1)

    print("VALIDATION PASSED: All required fields present and valid.")
    print(f"  - linearity_valid: {report.get('status_linearity')}")
    print(f"  - power_estimate: {report.get('power_estimate')}")
    print(f"  - warnings count: {len(report.get('warnings', []))}")
    sys.exit(0)

if __name__ == "__main__":
    main()