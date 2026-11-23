"""
T050: Verify Regression Implementation

This script verifies that the regression implementation components are present,
non-empty, and valid per FR-005 before the regression model can be executed.

Checks:
1. src/analysis/regression.py exists and is non-empty
2. data/results/filtered_features.json exists, is non-empty, and contains valid JSON
3. Validates that filtered features do not include excluded metrics (Max_ACF_Lag, spectral_density)

Output:
- data/results/regression_verification.json with status "PASS" or "FAIL"
"""
import os
import sys
import json
import logging
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.utils.logging import setup_logger, log_info, log_error, log_warning, log_critical
from src.utils.config import get_path

def verify_regression_implementation():
    """
    Verify that regression implementation components are present and valid.

    Returns:
        dict: Verification results with status and details
    """
    results = {
        "status": "FAIL",
        "checks": {},
        "errors": [],
        "warnings": []
    }

    # Setup logger
    logger = setup_logger("verify_regression")

    log_info(logger, "Starting regression implementation verification (T050)")

    # Check 1: Verify src/analysis/regression.py exists and is non-empty
    regression_file = project_root / "src" / "analysis" / "regression.py"
    if not regression_file.exists():
        error_msg = "src/analysis/regression.py does not exist"
        log_error(logger, error_msg)
        results["errors"].append(error_msg)
        results["checks"]["regression_file_exists"] = False
    else:
        file_size = regression_file.stat().st_size
        if file_size == 0:
            error_msg = "src/analysis/regression.py exists but is empty"
            log_error(logger, error_msg)
            results["errors"].append(error_msg)
            results["checks"]["regression_file_exists"] = False
        else:
            log_info(logger, f"src/analysis/regression.py found ({file_size} bytes)")
            results["checks"]["regression_file_exists"] = True

    # Check 2: Verify data/results/filtered_features.json exists and is valid
    filtered_features_file = project_root / "data" / "results" / "filtered_features.json"
    if not filtered_features_file.exists():
        error_msg = "data/results/filtered_features.json does not exist"
        log_error(logger, error_msg)
        results["errors"].append(error_msg)
        results["checks"]["filtered_features_file_exists"] = False
    else:
        file_size = filtered_features_file.stat().st_size
        if file_size == 0:
            error_msg = "data/results/filtered_features.json exists but is empty"
            log_error(logger, error_msg)
            results["errors"].append(error_msg)
            results["checks"]["filtered_features_file_exists"] = False
        else:
            try:
                with open(filtered_features_file, 'r') as f:
                    filtered_features = json.load(f)

                log_info(logger, f"data/results/filtered_features.json found ({file_size} bytes)")
                results["checks"]["filtered_features_file_exists"] = True
                results["checks"]["filtered_features_valid_json"] = True

                # Check 3: Verify excluded features are not present
                excluded_features = ["Max_ACF_Lag", "spectral_density"]
                features_list = filtered_features.get("features", [])

                found_excluded = []
                for excluded in excluded_features:
                    if excluded in features_list:
                        found_excluded.append(excluded)

                if found_excluded:
                    warning_msg = f"Excluded features found in filtered_features.json: {found_excluded}"
                    log_warning(logger, warning_msg)
                    results["warnings"].append(warning_msg)
                    results["checks"]["excluded_features_removed"] = False
                else:
                    log_info(logger, "Excluded features correctly removed from filtered_features.json")
                    results["checks"]["excluded_features_removed"] = True

                # Verify required keys exist
                required_keys = ["features", "excluded_features", "reason"]
                missing_keys = [key for key in required_keys if key not in filtered_features]
                if missing_keys:
                    warning_msg = f"Missing required keys in filtered_features.json: {missing_keys}"
                    log_warning(logger, warning_msg)
                    results["warnings"].append(warning_msg)
                    results["checks"]["required_keys_present"] = False
                else:
                    log_info(logger, "All required keys present in filtered_features.json")
                    results["checks"]["required_keys_present"] = True

            except json.JSONDecodeError as e:
                error_msg = f"data/results/filtered_features.json contains invalid JSON: {str(e)}"
                log_error(logger, error_msg)
                results["errors"].append(error_msg)
                results["checks"]["filtered_features_valid_json"] = False

    # Determine overall status
    if not results["errors"]:
        # Check if all critical checks passed
        critical_checks = [
            results["checks"].get("regression_file_exists", False),
            results["checks"].get("filtered_features_file_exists", False),
            results["checks"].get("filtered_features_valid_json", False),
            results["checks"].get("excluded_features_removed", True),  # Default to True if not checked
            results["checks"].get("required_keys_present", True)  # Default to True if not checked
        ]

        if all(critical_checks):
            results["status"] = "PASS"
            log_info(logger, "Regression implementation verification PASSED")
        else:
            log_warning(logger, "Some critical checks failed, but no errors encountered")
            results["warnings"].append("Some critical checks failed")
    else:
        log_critical(logger, f"Verification FAILED with {len(results['errors'])} error(s)")

    return results

def main():
    """Main entry point for T050 verification script."""
    results = verify_regression_implementation()

    # Write results to output file
    output_file = Path("data/results/regression_verification.json")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)

    log_info(None, f"Verification results written to {output_file}")

    # Exit with appropriate code
    if results["status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()