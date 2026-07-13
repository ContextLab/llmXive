"""
validate_quickstart.py

Validates end-to-end reproducibility by executing the pipeline scripts in order
and verifying that all expected artifacts are generated.

This script implements Task T038: Run quickstart.md validation to ensure
end-to-end reproducibility on a fresh runner.
"""
import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Project root is the parent of 'code'
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
ARTIFACTS_DIR = DATA_DIR / "artifacts"
PROCESSED_DIR = DATA_DIR / "processed"

# Ensure output directories exist
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)
PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = ARTIFACTS_DIR / "quickstart_validation.log"
REPORT_FILE = ARTIFACTS_DIR / "quickstart_validation_report.json"

# Define the pipeline steps and their expected outputs
# Order matters: T017 -> T018 -> T019 -> T023 -> T024 -> T029 -> T030 -> T031 -> T032
PIPELINE_STEPS = [
    {
        "id": "T017",
        "script": "01_download_and_filter.py",
        "expected_outputs": [
            DATA_DIR / "processed" / "eligible_subjects.csv",
            DATA_DIR / "processed" / "excluded_subjects.log"
        ],
        "description": "Download and filter dataset"
    },
    {
        "id": "T018",
        "script": "02_preprocess_and_parcellate.py",
        "expected_outputs": [
            # Preprocessed data is typically stored in data/processed/preprocessed/ or similar
            # We check for the existence of the directory or a marker file
            DATA_DIR / "processed" / "preprocessed"
        ],
        "description": "Preprocess and parcellate fMRI data"
    },
    {
        "id": "T019",
        "script": "03_compute_graph_metrics.py",
        "expected_outputs": [
            DATA_DIR / "processed" / "graph_metrics.csv"
        ],
        "description": "Compute graph metrics"
    },
    {
        "id": "T023",
        "script": "04_train_model.py",
        "expected_outputs": [
            DATA_DIR / "processed" / "model.pkl"
        ],
        "description": "Train model with nested CV"
    },
    {
        "id": "T024",
        "script": "05_evaluate_model.py",
        "expected_outputs": [
            DATA_DIR / "processed" / "performance_report.json"
        ],
        "description": "Evaluate model performance"
    },
    {
        "id": "T029",
        "script": "06_permutation_test.py",
        "expected_outputs": [
            DATA_DIR / "processed" / "permutation_results.json"
        ],
        "description": "Run permutation test"
    },
    {
        "id": "T030",
        "script": "07_sensitivity_analysis.py",
        "expected_outputs": [
            DATA_DIR / "processed" / "sensitivity_report.json"
        ],
        "description": "Run sensitivity analysis"
    },
    {
        "id": "T031",
        "script": "09_generate_report.py",
        "expected_outputs": [
            ARTIFACTS_DIR / "final_report.md"
        ],
        "description": "Generate final report"
    },
    {
        "id": "T032",
        "script": "10_verify_success_criteria.py",
        "expected_outputs": [
            ARTIFACTS_DIR / "verification_status.txt",
            ARTIFACTS_DIR / "runtime_report.json"
        ],
        "description": "Verify success criteria"
    }
]

def log(message: str, log_handle):
    """Write a message to the log file and print to stdout."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line)
    log_handle.write(line + "\n")
    log_handle.flush()

def run_script(script_name: str, log_handle) -> bool:
    """
    Execute a script from the code directory.
    Returns True if exit code is 0, False otherwise.
    """
    script_path = CODE_DIR / script_name
    if not script_path.exists():
        log(f"ERROR: Script not found: {script_path}", log_handle)
        return False

    log(f"Executing: {script_name}...", log_handle)
    start_time = time.time()

    try:
        # Run the script with python
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(CODE_DIR),
            capture_output=False, # Stream output to console
            timeout=3600, # 1 hour timeout per script
            check=False
        )

        elapsed = time.time() - start_time
        if result.returncode == 0:
            log(f"SUCCESS: {script_name} completed in {elapsed:.2f}s", log_handle)
            return True
        else:
            log(f"FAILED: {script_name} exited with code {result.returncode}", log_handle)
            return False

    except subprocess.TimeoutExpired:
        log(f"FAILED: {script_name} timed out after 1 hour", log_handle)
        return False
    except Exception as e:
        log(f"FAILED: {script_name} raised exception: {e}", log_handle)
        return False

def check_artifacts(expected_outputs: list, log_handle) -> bool:
    """
    Verify that all expected output files/directories exist.
    Returns True if all exist, False otherwise.
    """
    all_exist = True
    for path in expected_outputs:
        if path.exists():
            log(f"  [OK] Found: {path}", log_handle)
        else:
            log(f"  [MISSING] Expected: {path}", log_handle)
            all_exist = False
    return all_exist

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart reproducibility")
    parser.add_argument("--skip-existing", action="store_true",
                      help="Skip scripts if all their expected outputs already exist")
    args = parser.parse_args()

    results = []
    overall_success = True

    # Open log file
    with open(LOG_FILE, "w") as log_handle:
        log("=" * 60, log_handle)
        log("QUICKSTART VALIDATION REPORT", log_handle)
        log("=" * 60, log_handle)
        log(f"Project Root: {PROJECT_ROOT}", log_handle)
        log(f"Start Time: {datetime.now().isoformat()}", log_handle)
        log("-" * 60, log_handle)

        for step in PIPELINE_STEPS:
            step_id = step["id"]
            script_name = step["script"]
            expected = step["expected_outputs"]
            description = step["description"]

            log(f"\n--- Step {step_id}: {description} ---", log_handle)

            # Check if we can skip
            if args.skip_existing:
                if all(p.exists() for p in expected):
                    log(f"Skipping {script_name} (outputs exist)", log_handle)
                    results.append({
                        "step": step_id,
                        "script": script_name,
                        "status": "skipped",
                        "artifacts_ok": True
                    })
                    continue

            # Run script
            success = run_script(script_name, log_handle)
            artifacts_ok = False

            if success:
                # Check artifacts
                log(f"Verifying artifacts for {script_name}...", log_handle)
                artifacts_ok = check_artifacts(expected, log_handle)
            else:
                overall_success = False

            results.append({
                "step": step_id,
                "script": script_name,
                "status": "success" if (success and artifacts_ok) else "failed",
                "artifacts_ok": artifacts_ok
            })

            if not (success and artifacts_ok):
                overall_success = False

        log("\n" + "=" * 60, log_handle)
        log("VALIDATION SUMMARY", log_handle)
        log("=" * 60, log_handle)

        for r in results:
            status_icon = "✓" if r["status"] == "success" else "✗"
            log(f"{status_icon} {r['step']}: {r['script']} ({r['status']})", log_handle)

        log("-" * 60, log_handle)
        if overall_success:
            log("RESULT: ALL STEPS PASSED", log_handle)
        else:
            log("RESULT: VALIDATION FAILED", log_handle)
        log(f"End Time: {datetime.now().isoformat()}", log_handle)

    # Write JSON report
    report_data = {
        "timestamp": datetime.now().isoformat(),
        "overall_success": overall_success,
        "steps": results
    }

    with open(REPORT_FILE, "w") as f:
        json.dump(report_data, f, indent=2)

    print(f"\nDetailed log: {LOG_FILE}")
    print(f"JSON report: {REPORT_FILE}")

    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())