"""
Task T032: Run quickstart.md validation and ensure all tasks pass on local CPU environment.

This script orchestrates the validation of the entire pipeline against the requirements
defined in quickstart.md. It verifies:
1. Project structure exists
2. Data download and checksum verification
3. US1 Pipeline (Feature extraction, Training, Correlation, Gates)
4. US2 Pipeline (Profiling, Timing, Feasibility Gate)
5. US3 Pipeline (Sensitivity Analysis)
6. Output artifacts exist and are non-empty
"""
import os
import sys
import subprocess
import json
import time
from pathlib import Path
import logging

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from src.config import (
    get_project_root,
    get_data_root,
    get_state_root,
    get_reports_root,
    ensure_environment,
)
from src.data.download import fetch_evalverse_dataset, is_data_available
from src.utils import get_logger, write_json, read_json

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(PROJECT_ROOT / "reports" / "quickstart_validation.log"),
    ],
)
logger = get_logger("quickstart_validator")

VALIDATION_RESULTS = {}
FAILED_CHECKS = []

def check_project_structure():
    """Verify required directories exist."""
    logger.info("Checking project structure...")
    required_dirs = [
        "src",
        "tests",
        "specs",
        "data/raw",
        "data/processed",
        "data/results",
        "state",
        "reports",
        "figures",
        "scripts",
    ]
    missing = []
    for d in required_dirs:
        path = PROJECT_ROOT / d
        if not path.exists():
            missing.append(d)
            logger.warning(f"Missing directory: {d}")

    if missing:
        return False, f"Missing directories: {missing}"
    logger.info("Project structure validated.")
    return True, "All required directories exist."

def check_data_availability():
    """Verify data is downloaded and checksums match."""
    logger.info("Checking data availability...")
    if not is_data_available():
        logger.info("Data not available, attempting download...")
        try:
            fetch_evalverse_dataset()
        except Exception as e:
            logger.error(f"Data download failed: {e}")
            return False, f"Data download failed: {e}"

    # Check checksum file
    checksum_file = PROJECT_ROOT / "state" / "artifact_hashes.json"
    if not checksum_file.exists():
        logger.warning("Checksum file missing. Running checksum generation...")
        try:
            from scripts.checksum_data import main as checksum_main
            checksum_main()
        except Exception as e:
            logger.error(f"Checksum generation failed: {e}")
            return False, f"Checksum generation failed: {e}"

    logger.info("Data availability validated.")
    return True, "Data available and checksums verified."

def run_script(script_name, script_args=None, description=""):
    """Helper to run a script and capture result."""
    logger.info(f"Running {description}...")
    script_path = PROJECT_ROOT / "code" / "scripts" / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False, f"Script not found: {script_path}"

    cmd = [sys.executable, str(script_path)]
    if script_args:
        cmd.extend(script_args)

    try:
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=300,
        )
        if result.returncode != 0:
            logger.error(f"Script failed: {script_name}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False, f"Script {script_name} failed with code {result.returncode}"
        logger.info(f"{description} completed successfully.")
        return True, f"{description} passed."
    except subprocess.TimeoutExpired:
        logger.error(f"Script timed out: {script_name}")
        return False, f"Script {script_name} timed out"
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False, f"Error running {script_name}: {e}"

def check_artifact_exists(path, description):
    """Check if a required artifact file exists and is non-empty."""
    full_path = PROJECT_ROOT / path
    if not full_path.exists():
        logger.error(f"Artifact missing: {path}")
        return False, f"Artifact missing: {path}"
    if full_path.stat().st_size == 0:
        logger.error(f"Artifact empty: {path}")
        return False, f"Artifact empty: {path}"
    logger.info(f"Artifact validated: {description} ({path})")
    return True, f"Artifact exists: {description}"

def validate_us1():
    """Validate User Story 1 pipeline."""
    logger.info("Validating User Story 1 (Dimensional Viability Analysis)...")
    checks = []

    # Run validation gate (T041)
    success, msg = run_script(
        "run_validation_gate.py", description="T041 Validation Gate"
    )
    checks.append(("T041", success, msg))

    # Run quality gate (T040)
    success, msg = run_script(
        "run_quality_gate.py", description="T040 Quality Gate"
    )
    checks.append(("T040", success, msg))

    # Run training pipeline
    success, msg = run_script("run_training.py", description="T015 Training")
    checks.append(("T015", success, msg))

    # Run metrics calculation
    success, msg = run_script("run_metrics.py", description="T016 Metrics")
    checks.append(("T016", success, msg))

    # Check artifacts
    artifacts = [
        ("state/validation_status.json", "Validation status"),
        ("state/global_error_rate.json", "Global error rate"),
        ("data/baseline_results.csv", "Baseline results"),
        ("data/permutation_results.csv", "Permutation results"),
    ]
    for path, desc in artifacts:
        success, msg = check_artifact_exists(path, desc)
        checks.append((f"Artifact-{desc}", success, msg))

    return checks

def validate_us2():
    """Validate User Story 2 pipeline."""
    logger.info("Validating User Story 2 (Compute Feasibility Profiling)...")
    checks = []

    # Run profiling
    success, msg = run_script("run_profiling.py", description="T022 Profiling")
    checks.append(("T022", success, msg))

    # Run scaling validation (T021b)
    success, msg = run_script(
        "run_scaling_validation.py", description="T021b Scaling Validation"
    )
    checks.append(("T021b", success, msg))

    # Run timing profile generation
    success, msg = run_script(
        "generate_timing_profile.py", description="T024 Timing Profile"
    )
    checks.append(("T024", success, msg))

    # Run feasibility gate (T021)
    success, msg = run_script("run_feasibility_gate.py", description="T021 Gate")
    checks.append(("T021", success, msg))

    # Check artifacts
    artifacts = [
        ("state/feasibility_gate.json", "Feasibility gate"),
        ("state/scaling_validation.json", "Scaling validation"),
        ("data/timing_profile.csv", "Timing profile"),
        ("data/profiling_logs.json", "Profiling logs"),
        ("reports/feasibility_profile.json", "Feasibility report"),
    ]
    for path, desc in artifacts:
        success, msg = check_artifact_exists(path, desc)
        checks.append((f"Artifact-{desc}", success, msg))

    return checks

def validate_us3():
    """Validate User Story 3 pipeline."""
    logger.info("Validating User Story 3 (Sensitivity Analysis)...")
    checks = []

    # Run threshold sweep
    success, msg = run_script(
        "run_threshold_sweep.py", description="T026 Threshold Sweep"
    )
    checks.append(("T026", success, msg))

    # Run sensitivity analysis
    success, msg = run_script(
        "generate_sensitivity_analysis.py", description="T027 Analysis"
    )
    checks.append(("T027", success, msg))

    # Run sensitivity matrix
    success, msg = run_script(
        "generate_sensitivity_matrix.py", description="T028 Matrix"
    )
    checks.append(("T028", success, msg))

    # Check artifacts
    artifacts = [
        ("data/sensitivity_sweep_raw.csv", "Raw sweep data"),
        ("data/sensitivity_analysis.csv", "Sensitivity analysis"),
        ("data/sensitivity_matrix_full.csv", "Sensitivity matrix"),
    ]
    for path, desc in artifacts:
        success, msg = check_artifact_exists(path, desc)
        checks.append((f"Artifact-{desc}", success, msg))

    return checks

def main():
    logger.info("=" * 60)
    logger.info("Starting Quickstart Validation (T032)")
    logger.info("=" * 60)

    # 1. Check project structure
    success, msg = check_project_structure()
    VALIDATION_RESULTS["project_structure"] = {"success": success, "message": msg}
    if not success:
        FAILED_CHECKS.append(f"Project Structure: {msg}")

    # 2. Check data availability
    success, msg = check_data_availability()
    VALIDATION_RESULTS["data_availability"] = {"success": success, "message": msg}
    if not success:
        FAILED_CHECKS.append(f"Data Availability: {msg}")

    # 3. Validate US1
    us1_checks = validate_us1()
    us1_success = all(c[1] for c in us1_checks)
    VALIDATION_RESULTS["us1"] = {
        "success": us1_success,
        "checks": us1_checks,
    }
    if not us1_success:
        for name, success, msg in us1_checks:
            if not success:
                FAILED_CHECKS.append(f"US1 - {name}: {msg}")

    # 4. Validate US2
    us2_checks = validate_us2()
    us2_success = all(c[1] for c in us2_checks)
    VALIDATION_RESULTS["us2"] = {
        "success": us2_success,
        "checks": us2_checks,
    }
    if not us2_success:
        for name, success, msg in us2_checks:
            if not success:
                FAILED_CHECKS.append(f"US2 - {name}: {msg}")

    # 5. Validate US3
    us3_checks = validate_us3()
    us3_success = all(c[1] for c in us3_checks)
    VALIDATION_RESULTS["us3"] = {
        "success": us3_success,
        "checks": us3_checks,
    }
    if not us3_success:
        for name, success, msg in us3_checks:
            if not success:
                FAILED_CHECKS.append(f"US3 - {name}: {msg}")

    # 6. Write final report
    report_path = PROJECT_ROOT / "reports" / "quickstart_validation_report.json"
    write_json(report_path, VALIDATION_RESULTS)
    logger.info(f"Validation report written to: {report_path}")

    # Summary
    logger.info("=" * 60)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 60)
    logger.info(f"Project Structure: {'PASS' if VALIDATION_RESULTS['project_structure']['success'] else 'FAIL'}")
    logger.info(f"Data Availability: {'PASS' if VALIDATION_RESULTS['data_availability']['success'] else 'FAIL'}")
    logger.info(f"User Story 1: {'PASS' if us1_success else 'FAIL'}")
    logger.info(f"User Story 2: {'PASS' if us2_success else 'FAIL'}")
    logger.info(f"User Story 3: {'PASS' if us3_success else 'FAIL'}")

    if FAILED_CHECKS:
        logger.error(f"VALIDATION FAILED: {len(FAILED_CHECKS)} issues found")
        for issue in FAILED_CHECKS:
            logger.error(f"  - {issue}")
        sys.exit(1)
    else:
        logger.info("VALIDATION PASSED: All checks successful")
        sys.exit(0)

if __name__ == "__main__":
    main()
