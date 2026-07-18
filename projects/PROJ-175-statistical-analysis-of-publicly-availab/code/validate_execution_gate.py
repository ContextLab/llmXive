import os
import sys
import json
from pathlib import Path
from datetime import datetime

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

def load_json(path):
    """Load and return JSON data from a file path."""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError) as e:
        print(f"Error loading {path}: {e}")
        return None

def check_verification_report():
    """Check if verification_report.json exists and status is 'PASS' or 'SUCCESS'."""
    path = project_root / "data" / "verification_report.json"
    if not path.exists():
        print(f"Missing: {path}")
        return False
    data = load_json(path)
    if data is None:
        return False
    # Accept both 'PASS' and 'SUCCESS' as valid positive statuses based on project history
    status = data.get("status", "")
    return status in ("PASS", "SUCCESS")

def check_bayesian_convergence():
    """Check if bayesian_convergence_log.json exists and status is 'SUCCESS'."""
    path = project_root / "data" / "bayesian_convergence_log.json"
    if not path.exists():
        print(f"Missing: {path}")
        return False
    data = load_json(path)
    if data is None:
        return False
    status = data.get("status", "")
    return status == "SUCCESS"

def check_calibration_results():
    """Check if calibration_test_results.json exists and passed is True."""
    path = project_root / "data" / "calibration_test_results.json"
    if not path.exists():
        print(f"Missing: {path}")
        return False
    data = load_json(path)
    if data is None:
        return False
    return data.get("passed", False) is True

def check_vif_scores_exists():
    """Check if vif_scores_initial.json exists."""
    path = project_root / "data" / "vif_scores_initial.json"
    exists = path.exists()
    if not exists:
        print(f"Missing: {path}")
    return exists

def main():
    """Main gate validation entry point.
    
    Verifies:
    1. data/verification_report.json exists and status is "PASS"
    2. data/bayesian_convergence_log.json exists and status is "SUCCESS"
    3. data/calibration_test_results.json exists and passed is true
    4. data/vif_scores_initial.json exists
    
    Outputs: data/gate_validation_report.json
    Exits: 0 if PASS, 1 if FAIL
    """
    print("Running Execution Gate Pre-Check (T056)...")
    
    checks = {
        "verification": check_verification_report(),
        "bayesian": check_bayesian_convergence(),
        "calibration": check_calibration_results(),
        "vif": check_vif_scores_exists()
    }
    
    # Determine overall status
    all_passed = all(checks.values())
    status = "PASS" if all_passed else "FAIL"
    
    report = {
        "status": status,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat() + "Z"
    }
    
    # Ensure data directory exists
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Write report
    output_path = data_dir / "gate_validation_report.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    print(f"Gate validation result: {status}")
    print(f"Report written to: {output_path}")
    
    if not all_passed:
        failed_checks = [k for k, v in checks.items() if not v]
        print(f"Failed checks: {failed_checks}")
        sys.exit(1)
    
    print("All checks passed.")

if __name__ == "__main__":
    main()
