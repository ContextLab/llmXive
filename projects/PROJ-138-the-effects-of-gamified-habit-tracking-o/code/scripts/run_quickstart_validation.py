"""
Quickstart Validation Script for PROJ-138.

This script executes the full pipeline as defined in quickstart.md,
verifies pre-flight dependencies, and asserts that all declared
artifacts are produced correctly.
"""
import os
import sys
import subprocess
import json
from pathlib import Path

# Add project root to path to allow imports if needed, though we use subprocess
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from code.utils.logging import setup_logger, log_pipeline_stage

logger = setup_logger("validation")

def run_command(cmd, description):
    """Run a shell command and return success status."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=True,
            text=True
        )
        logger.info(f"Success: {description}")
        if result.stdout:
            logger.debug(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed: {description}")
        logger.error(f"Return code: {e.returncode}")
        logger.error(f"Stdout: {e.stdout}")
        logger.error(f"Stderr: {e.stderr}")
        return False

def check_file_exists(path_str, description):
    """Check if a file exists."""
    path = PROJECT_ROOT / path_str
    if path.exists():
        logger.info(f"Verified: {description} exists at {path}")
        return True
    else:
        logger.error(f"Missing: {description} at {path}")
        return False

def check_file_not_empty(path_str, description):
    """Check if a file exists and has content."""
    path = PROJECT_ROOT / path_str
    if path.exists() and path.stat().st_size > 0:
        logger.info(f"Verified: {description} is not empty.")
        return True
    else:
        logger.error(f"Empty/Missing: {description} at {path}")
        return False

def main():
    """Execute the validation workflow."""
    log_pipeline_stage(logger, "START", "Quickstart Validation")
    
    success = True

    # 1. Pre-flight dependency checks
    logger.info("Performing pre-flight dependency checks...")
    
    deps = [
        ("contracts/dataset.schema.yaml", "Dataset Schema (T009)"),
        ("data/raw/synthetic_data_marker.json", "Synthetic Data Marker (T013a)"),
        ("data/processed/merged_data.csv", "Merged Data (T017) - Expected Output"),
        ("data/processed/psychometrics.json", "Psychometrics (T012c) - Expected Output"),
        ("code/data/synthetic_generator.py", "Synthetic Generator Script"),
        ("code/data/ingestion.py", "Ingestion Script"),
        ("code/data/aggregation.py", "Aggregation Script"),
        ("code/data/merge.py", "Merge Script"),
        ("code/data/validation.py", "Validation Script"),
        ("code/analysis/modeling.py", "Modeling Script"),
        ("code/analysis/survival.py", "Survival Script"),
        ("code/reports/generate_report.py", "Report Generation Script"),
    ]

    for dep_path, dep_desc in deps:
        if not check_file_exists(dep_path, dep_desc):
            # For expected outputs, we might not have them yet if running fresh,
            # but for scripts and configs, they must exist.
            if "Script" in dep_desc or "Schema" in dep_desc or "Marker" in dep_desc:
                success = False
                logger.error(f"Critical missing pre-flight dependency: {dep_desc}")
            else:
                logger.warning(f"Expected output not yet found (will be generated): {dep_desc}")

    if not success:
        logger.error("Pre-flight checks failed. Aborting validation.")
        return 1

    # 2. Execute the pipeline steps explicitly to ensure they run and produce artifacts
    # Note: The quickstart.sh might do this, but we run them explicitly here to 
    # ensure we catch errors and verify outputs immediately.
    
    pipeline_steps = [
        (["python", "code/data/synthetic_generator.py", "--seed", "42", "--n_users", "100", "--weeks", "50"], "Generate Synthetic Data (T013a)"),
        (["python", "code/data/ingestion.py"], "Run Ingestion (T013b)"),
        (["python", "code/data/aggregation.py"], "Run Aggregation (T014)"),
        (["python", "code/data/merge.py"], "Run Merge (T017)"),
        (["python", "code/data/validation.py", "--action", "cronbach"], "Calculate Cronbach's Alpha (T012b)"),
        (["python", "code/utils/versioning.py", "--action", "hash"], "Run Versioning (T033)"),
        (["python", "code/analysis/modeling.py"], "Run Modeling (T020)"),
        (["python", "code/analysis/survival.py"], "Run Survival Analysis (T025)"),
        (["python", "code/analysis/robustness.py"], "Run Robustness Check (T029)"),
        (["python", "code/reports/generate_report.py"], "Generate Final Report (T032)"),
    ]

    for cmd, desc in pipeline_steps:
        if not run_command(cmd, desc):
            success = False
            # We continue to run as much as possible to see cascade failures, 
            # but the final verdict will be failed.

    # 3. Verify declared deliverables
    logger.info("Verifying declared deliverables...")
    
    deliverables = [
        ("data/raw/synthetic_data.csv", "Raw Synthetic Data"),
        ("data/processed/merged_data.csv", "Merged Data CSV"),
        ("data/processed/psychometrics.json", "Psychometrics JSON"),
        ("data/reports/final_analysis.html", "Final HTML Report"),
        ("state.yaml", "Versioning State"),
    ]

    for path, desc in deliverables:
        if not check_file_exists(path, desc):
            success = False
        elif not check_file_not_empty(path, desc):
            success = False

    # 4. Final Summary
    if success:
        logger.info("VALIDATION SUCCESSFUL: All steps completed and artifacts verified.")
        return 0
    else:
        logger.error("VALIDATION FAILED: One or more steps failed or artifacts missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
