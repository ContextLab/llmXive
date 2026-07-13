"""
Quickstart validation script for PROJ-029.
Executes the full pipeline end-to-end as described in quickstart.md
and verifies that all expected artifacts are produced.
"""
import os
import sys
import subprocess
import time
import json
import argparse
from pathlib import Path
from datetime import datetime

# Project root relative to this script
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
ARTIFACTS_DIR = DATA_DIR / "artifacts"

# Scripts to run in order
SCRIPTS = [
    "00_data_gate.py",
    "01_download_and_filter.py",
    "02_preprocess_and_parcellate.py",
    "03_compute_graph_metrics.py",
    "04_train_model.py",
    "05_evaluate_model.py",
    "06_runtime_verifier.py",  # Note: Task list had 06_permutation_test.py, but API shows 06_runtime_verifier. Using API.
    "07_sensitivity_analysis.py",
    "08_security_scan.py",
    "09_generate_report.py",
    "10_verify_success_criteria.py",
    "11_external_outcome_check.py",
]

# Expected output artifacts based on tasks.md and API surface
EXPECTED_ARTIFACTS = [
    "data/processed/eligible_subjects.csv",
    "data/processed/excluded_subjects.log",
    "data/processed/graph_metrics.csv",
    "data/processed/model.pkl",
    "data/processed/performance_report.json",
    "data/processed/permutation_results.json",  # From T029
    "data/processed/sensitivity_report.json",  # From T030
    "data/artifacts/limitations.txt",
    "data/artifacts/final_report.md",
    "data/artifacts/memory_profile.log",
    "data/artifacts/runtime_report.json",
]

def log(message: str):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{timestamp}] {message}")

def run_script(script_name: str) -> bool:
    """Run a specific script and return True if successful."""
    script_path = PROJECT_ROOT / "code" / script_name
    if not script_path.exists():
        log(f"ERROR: Script not found: {script_path}")
        return False

    log(f"Running {script_name}...")
    start_time = time.time()
    try:
        # Run with python, capturing output
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=3600,  # 1 hour timeout per script
        )

        elapsed = time.time() - start_time

        if result.returncode == 0:
            log(f"SUCCESS: {script_name} completed in {elapsed:.2f}s")
            if result.stdout:
                # Log last few lines of output for context
                lines = result.stdout.strip().split('\n')
                for line in lines[-3:]:
                    if line:
                        log(f"  > {line}")
            return True
        else:
            log(f"FAILED: {script_name} exited with code {result.returncode}")
            if result.stderr:
                log(f"STDERR: {result.stderr[-500:]}")  # Last 500 chars
            return False
    except subprocess.TimeoutExpired:
        log(f"TIMEOUT: {script_name} exceeded 1 hour limit")
        return False
    except Exception as e:
        log(f"ERROR: {script_name} raised exception: {e}")
        return False

def check_artifacts() -> dict:
    """Verify that all expected artifacts exist."""
    results = {}
    missing = []
    for artifact in EXPECTED_ARTIFACTS:
        full_path = PROJECT_ROOT / artifact
        exists = full_path.exists()
        results[artifact] = exists
        if not exists:
            missing.append(artifact)
        else:
            # Check file size > 0
            size = full_path.stat().st_size
            results[f"{artifact}_size"] = size
            if size == 0:
                log(f"WARNING: {artifact} exists but is empty")

    return results, missing

def main():
    parser = argparse.ArgumentParser(description="Validate quickstart.md reproducibility")
    parser.add_argument("--skip-scripts", action="store_true", help="Skip running scripts, only check artifacts")
    parser.add_argument("--output", type=str, default="data/artifacts/quickstart_validation_report.json",
                        help="Path to save validation report")
    args = parser.parse_args()

    log("="*60)
    log("Starting Quickstart Validation")
    log("="*60)

    validation_start = time.time()
    script_results = {}
    all_scripts_passed = True

    if not args.skip_scripts:
        for script in SCRIPTS:
            success = run_script(script)
            script_results[script] = "passed" if success else "failed"
            if not success:
                all_scripts_passed = False
                log("Stopping pipeline due to script failure.")
                break
    else:
        log("Skipping script execution (artifacts check only).")

    log("Checking expected artifacts...")
    artifact_results, missing_artifacts = check_artifacts()

    validation_end = time.time()
    total_duration = validation_end - validation_start

    # Compile report
    report = {
        "validation_timestamp": datetime.now().isoformat(),
        "total_duration_seconds": total_duration,
        "scripts_executed": not args.skip_scripts,
        "all_scripts_passed": all_scripts_passed,
        "script_results": script_results,
        "artifacts_present": artifact_results,
        "missing_artifacts": missing_artifacts,
        "overall_status": "passed" if (all_scripts_passed and not missing_artifacts) else "failed",
        "summary": {
            "total_scripts": len(SCRIPTS),
            "passed_scripts": sum(1 for r in script_results.values() if r == "passed"),
            "failed_scripts": sum(1 for r in script_results.values() if r == "failed"),
            "total_expected_artifacts": len(EXPECTED_ARTIFACTS),
            "missing_artifact_count": len(missing_artifacts),
        }
    }

    # Save report
    output_path = PROJECT_ROOT / args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(report, f, indent=2)

    log(f"Validation report saved to: {output_path}")
    log(f"Overall Status: {report['overall_status'].upper()}")

    if missing_artifacts:
        log(f"Missing artifacts ({len(missing_artifacts)}):")
        for m in missing_artifacts:
            log(f"  - {m}")

    if not all_scripts_passed:
        log("One or more scripts failed execution.")

    # Exit with error code if validation failed
    if report['overall_status'] == "failed":
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()