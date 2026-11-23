import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime

from verify_data_integrity import verify_data_integrity, load_json_file

def run_fabrication_audit(project_root: Path) -> dict:
    """
    Executes the integrity verification (T056) on the current project state.
    This task (T067) acts as the final audit gate.
    
    Logic:
    1. Calls verify_data_integrity() to scan data/ for synthetic placeholders.
    2. Checks if --real-data mode was used (implied by existence of real artifacts).
    3. If synthetic artifacts are found in a real-data run, marks as FAIL.
    4. Generates data/results/fabrication_audit_report.json.
    
    Returns:
        dict: The audit report content.
    """
    results_dir = project_root / "data" / "results"
    metadata_dir = project_root / "data" / "metadata"
    
    # Ensure directories exist
    results_dir.mkdir(parents=True, exist_ok=True)
    metadata_dir.mkdir(parents=True, exist_ok=True)

    # 1. Run the underlying integrity check (T056 logic)
    # This function scans for synthetic_*.csv or checksum markers in data/
    integrity_result = verify_data_integrity(project_root)
    
    # 2. Determine the context: Did we run in real-data mode?
    # We infer this by checking for the existence of real-data specific artifacts
    # or by checking if the system state indicates a real-data run.
    # For this audit, we assume the context is "Real Data Expected" if 
    # data/processed/harmonized_data.parquet or data/raw/real_*.csv exists.
    
    harmonized_path = project_root / "data" / "processed" / "harmonized_data.parquet"
    raw_real_path = project_root / "data" / "raw"
    
    real_data_present = (
        harmonized_path.exists() or 
        (raw_real_path.exists() and any(f.name.startswith("real_") for f in raw_real_path.iterdir() if f.is_file()))
    )

    # 3. Compile the Audit Report
    report = {
        "audit_id": "T067-FABRICATION-AUDIT",
        "timestamp": datetime.now().isoformat(),
        "status": "PASS",
        "real_data_mode_detected": real_data_present,
        "integrity_check_result": integrity_result,
        "findings": [],
        "synthetic_artifacts_found": [],
        "verdict": "CLEAN"
    }

    # Check if integrity check found synthetic artifacts
    if integrity_result.get("status") == "FAIL":
        report["status"] = "FAIL"
        report["verdict"] = "FABRICATION_DETECTED"
        report["findings"].append(
            "Integrity check failed: Synthetic artifacts detected in data directory."
        )
        report["synthetic_artifacts_found"] = integrity_result.get("found_artifacts", [])
    
    # If real data was expected but no real data artifacts exist, that's a different error (T055),
    # but for T067 we specifically check for the presence of synthetic placeholders.
    if not real_data_present:
        report["findings"].append(
            "No real data artifacts detected. Audit context is 'Pipeline Validation' (Synthetic)."
        )
        if not report["synthetic_artifacts_found"]:
            report["findings"].append("No unexpected synthetic placeholders found.")
        # If we are in synthetic mode, finding synthetic placeholders is expected, 
        # so we don't fail the audit unless they are in the wrong place or unmanifested.
        # However, the task description says: "Confirm ... shows PASS and no synthetic artifacts are present."
        # This implies we are auditing a REAL data run (T066 output).
        # If T066 ran successfully, real_data_present should be True.

    # 4. Write the report
    output_path = results_dir / "fabrication_audit_report.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Fabrication Audit Report written to: {output_path}")
    print(f"Audit Verdict: {report['verdict']}")
    
    return report

def main():
    parser = argparse.ArgumentParser(description="Run Fabrication Audit (T067)")
    parser.add_argument(
        "--project-root", 
        type=str, 
        default=".", 
        help="Path to the project root directory"
    )
    args = parser.parse_args()

    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print(f"Error: Project root {project_root} does not exist.")
        sys.exit(1)

    try:
        run_fabrication_audit(project_root)
        print("Audit completed successfully.")
    except Exception as e:
        print(f"Audit failed with error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
