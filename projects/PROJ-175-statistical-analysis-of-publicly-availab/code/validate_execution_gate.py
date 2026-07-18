"""
Execution Gate Pre-Check (T056)

Verifies the completion and validity of critical pipeline artifacts:
1. data/verification_report.json (status == "PASS" or "SUCCESS")
2. data/bayesian_convergence_log.json (status == "SUCCESS")
3. data/calibration_test_results.json (passed == true)
4. data/vif_scores_initial.json (exists)

Outputs: data/gate_validation_report.json
"""
import os
import sys
import json
from pathlib import Path

# Project root relative to script location
ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / "data"

def load_json(path: Path) -> dict:
    """Load JSON file, raise FileNotFoundError if missing."""
    if not path.exists():
        raise FileNotFoundError(f"Required artifact missing: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def check_verification_report(report: dict) -> bool:
    """Check if verification report status is PASS or SUCCESS."""
    status = report.get("status", "").upper()
    return status in ("PASS", "SUCCESS")

def check_bayesian_convergence(report: dict) -> bool:
    """Check if Bayesian convergence log status is SUCCESS."""
    status = report.get("status", "").upper()
    return status == "SUCCESS"

def check_calibration_results(report: dict) -> bool:
    """Check if calibration test passed."""
    return report.get("passed", False) is True

def check_vif_scores_exists(report: dict) -> bool:
    """Check if VIF scores file exists and is non-empty dict."""
    # The existence is checked by load_json, here we just ensure it's valid
    return isinstance(report, dict) and len(report) > 0

def main():
    print("Running Execution Gate Pre-Check (T056)...")
    
    results = {
        "status": "FAIL",
        "checks": {
            "verification": False,
            "bayesian": False,
            "calibration": False,
            "vif": False
        },
        "errors": []
    }

    try:
        # 1. Verify data/verification_report.json
        v_report_path = DATA_DIR / "verification_report.json"
        v_report = load_json(v_report_path)
        if check_verification_report(v_report):
            results["checks"]["verification"] = True
            print("[PASS] Verification report valid.")
        else:
            results["errors"].append("Verification report status is not PASS/SUCCESS")
            print("[FAIL] Verification report status invalid.")

        # 2. Verify data/bayesian_convergence_log.json
        b_report_path = DATA_DIR / "bayesian_convergence_log.json"
        b_report = load_json(b_report_path)
        if check_bayesian_convergence(b_report):
            results["checks"]["bayesian"] = True
            print("[PASS] Bayesian convergence log valid.")
        else:
            results["errors"].append("Bayesian convergence log status is not SUCCESS")
            print("[FAIL] Bayesian convergence log status invalid.")

        # 3. Verify data/calibration_test_results.json
        c_report_path = DATA_DIR / "calibration_test_results.json"
        c_report = load_json(c_report_path)
        if check_calibration_results(c_report):
            results["checks"]["calibration"] = True
            print("[PASS] Calibration test results valid.")
        else:
            results["errors"].append("Calibration test did not pass.")
            print("[FAIL] Calibration test failed.")

        # 4. Verify data/vif_scores_initial.json
        vif_report_path = DATA_DIR / "vif_scores_initial.json"
        vif_report = load_json(vif_report_path)
        if check_vif_scores_exists(vif_report):
            results["checks"]["vif"] = True
            print("[PASS] VIF scores initial file valid.")
        else:
            results["errors"].append("VIF scores initial file is empty or invalid.")
            print("[FAIL] VIF scores initial file invalid.")

        # Determine overall status
        all_passed = all(results["checks"].values())
        results["status"] = "PASS" if all_passed else "FAIL"

        if all_passed:
            print("\n>>> EXECUTION GATE PASSED <<<")
        else:
            print(f"\n>>> EXECUTION GATE FAILED <<<")
            print(f"Errors: {results['errors']}")

    except FileNotFoundError as e:
        results["status"] = "FAIL"
        results["errors"].append(str(e))
        print(f"[CRITICAL] Missing artifact: {e}")
    except json.JSONDecodeError as e:
        results["status"] = "FAIL"
        results["errors"].append(f"JSON decode error: {e}")
        print(f"[CRITICAL] Invalid JSON format: {e}")
    except Exception as e:
        results["status"] = "FAIL"
        results["errors"].append(f"Unexpected error: {e}")
        print(f"[CRITICAL] Unexpected error: {e}")

    # Write output report
    output_path = DATA_DIR / "gate_validation_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)
    
    print(f"Gate validation report written to: {output_path}")

    # Exit with non-zero code if failed
    if results["status"] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()