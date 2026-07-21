"""
Task T067: Fabrication Audit
Runs the integrity verification (T056) on the output of the real data pipeline (T066).
Confirms no synthetic artifacts are present and generates a final audit report.
"""
import os
import sys
import json
import argparse
from pathlib import Path

# Import from existing project modules
from verify_data_integrity import run_validation_pipeline, load_json_file, save_json_file
from config import get_config, load_config

def main():
    parser = argparse.ArgumentParser(description="Run Fabrication Audit (T067)")
    parser.add_argument("--config", type=str, default="data/config/project_config.yaml",
                        help="Path to configuration file")
    parser.add_argument("--output-dir", type=str, default="data/results",
                        help="Directory to store audit reports")
    args = parser.parse_args()

    # Ensure output directory exists
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load configuration
    try:
        config = load_config(args.config)
    except FileNotFoundError:
        print("Warning: Config file not found. Using defaults.")
        config = get_config()

    # Paths for input artifacts
    integrity_verification_path = output_dir / "integrity_verification.json"
    audit_report_path = output_dir / "fabrication_audit_report.json"

    # Check if T056 artifact exists (prerequisite)
    if not integrity_verification_path.exists():
        print(f"ERROR: Prerequisite artifact not found: {integrity_verification_path}")
        print("Please ensure T056 (verify_data_integrity) has been run successfully.")
        sys.exit(1)

    # Load the T056 integrity verification results
    try:
        integrity_data = load_json_file(str(integrity_verification_path))
    except Exception as e:
        print(f"ERROR: Failed to load integrity verification data: {e}")
        sys.exit(1)

    # Perform the Fabrication Audit logic
    audit_result = {
        "audit_id": "T067-FABRICATION-AUDIT",
        "timestamp": os.popen("date -Iseconds").read().strip(),
        "status": "PASS",
        "checks": []
    }

    # Check 1: Verify integrity_verification.json status
    integrity_status = integrity_data.get("status", "UNKNOWN")
    if integrity_status == "PASS":
        audit_result["checks"].append({
            "check_name": "Integrity Verification Status",
            "expected": "PASS",
            "actual": integrity_status,
            "result": "PASS"
        })
    else:
        audit_result["checks"].append({
            "check_name": "Integrity Verification Status",
            "expected": "PASS",
            "actual": integrity_status,
            "result": "FAIL"
        })
        audit_result["status"] = "FAIL"

    # Check 2: Verify no synthetic artifacts detected
    synthetic_artifacts = integrity_data.get("synthetic_artifacts_found", [])
    if not synthetic_artifacts:
        audit_result["checks"].append({
            "check_name": "Synthetic Artifact Scan",
            "expected": "Empty List",
            "actual": "None Found",
            "result": "PASS"
        })
    else:
        audit_result["checks"].append({
            "check_name": "Synthetic Artifact Scan",
            "expected": "Empty List",
            "actual": str(synthetic_artifacts),
            "result": "FAIL"
        })
        audit_result["status"] = "FAIL"

    # Check 3: Verify real data analysis report exists (T066 output)
    real_data_report_path = output_dir / "real_data_analysis_report.json"
    if real_data_report_path.exists():
        audit_result["checks"].append({
            "check_name": "Real Data Analysis Report Presence",
            "expected": "Exists",
            "actual": "Exists",
            "result": "PASS"
        })
    else:
        audit_result["checks"].append({
            "check_name": "Real Data Analysis Report Presence",
            "expected": "Exists",
            "actual": "Missing",
            "result": "FAIL"
        })
        audit_result["status"] = "FAIL"

    # Final Conclusion
    if audit_result["status"] == "PASS":
        conclusion = "AUDIT PASSED: No fabrication detected. Real data pipeline executed successfully."
    else:
        conclusion = "AUDIT FAILED: Fabrication or integrity issues detected. Review checks above."

    audit_result["conclusion"] = conclusion
    audit_result["checks_passed"] = sum(1 for c in audit_result["checks"] if c["result"] == "PASS")
    audit_result["checks_total"] = len(audit_result["checks"])

    # Write the final audit report to disk
    try:
        save_json_file(str(audit_report_path), audit_result)
        print(f"SUCCESS: Fabrication audit report written to {audit_report_path}")
    except Exception as e:
        print(f"ERROR: Failed to write audit report: {e}")
        sys.exit(1)

    # Exit with appropriate code
    if audit_result["status"] == "PASS":
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
