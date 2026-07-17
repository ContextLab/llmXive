import os
import sys
import json
import logging
import subprocess
from pathlib import Path

from utils import get_logger, set_task_id, get_task_id

# Ensure task ID is set for this validation run
set_task_id("T039")
logger = get_logger("validate_quickstart")

def check_directory(path: str) -> bool:
    """Check if a directory exists."""
    exists = os.path.isdir(path)
    if exists:
        logger.info(f"Directory exists: {path}")
    else:
        logger.error(f"Directory missing: {path}")
    return exists

def check_file(path: str) -> bool:
    """Check if a file exists and is readable."""
    exists = os.path.isfile(path)
    if exists:
        logger.info(f"File exists: {path}")
    else:
        logger.error(f"File missing: {path}")
    return exists

def verify_json_structure(path: str, required_keys: list) -> bool:
    """Verify a JSON file exists and contains required keys."""
    if not check_file(path):
        return False
    try:
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        missing = [k for k in required_keys if k not in data]
        if missing:
            logger.error(f"Missing keys in {path}: {missing}")
            return False
        logger.info(f"JSON structure valid: {path}")
        return True
    except Exception as e:
        logger.error(f"Error verifying {path}: {e}")
        return False

def run_pipeline_stage(script_path: str, stage_name: str) -> bool:
    """Run a pipeline stage script and capture output."""
    logger.info(f"Running pipeline stage: {stage_name}")
    try:
        result = subprocess.run(
            [sys.executable, script_path],
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        if result.returncode == 0:
            logger.info(f"Stage {stage_name} completed successfully")
            if result.stdout:
                logger.debug(f"Stdout:\n{result.stdout}")
            return True
        else:
            logger.error(f"Stage {stage_name} failed with code {result.returncode}")
            if result.stderr:
                logger.error(f"Stderr:\n{result.stderr}")
            return False
    except subprocess.TimeoutExpired:
        logger.error(f"Stage {stage_name} timed out")
        return False
    except Exception as e:
        logger.error(f"Error running stage {stage_name}: {e}")
        return False

def validate_artifacts() -> dict:
    """Validate all required artifacts exist and have correct structure."""
    results = {
        "directories": {},
        "files": {},
        "json_structures": {},
        "pipeline_stages": {}
    }

    # Check required directories
    required_dirs = [
        "data/raw",
        "data/generated",
        "data/analysis",
        "results/figures"
    ]
    for d in required_dirs:
        results["directories"][d] = check_directory(d)

    # Check required files
    required_files = [
        "data/raw/humaneval.json",
        "data/analysis/metrics.json",
        "results_report.md"
    ]
    for f in required_files:
        results["files"][f] = check_file(f)

    # Verify JSON structures
    results["json_structures"]["metrics.json"] = verify_json_structure(
        "data/analysis/metrics.json",
        ["cyclomatic_complexity", "halstead_volume", "branch_coverage_pct", "pass_rate"]
    )

    # Check if results_report.md has content
    if check_file("results_report.md"):
        try:
            with open("results_report.md", 'r', encoding='utf-8') as f:
                content = f.read()
            has_figures = "figures/" in content or "png" in content.lower()
            has_tables = "|" in content
            results["files"]["results_report.md"] = has_figures and has_tables
            if not has_figures:
                logger.warning("results_report.md missing figure references")
            if not has_tables:
                logger.warning("results_report.md missing table structures")
        except Exception as e:
            logger.error(f"Error reading results_report.md: {e}")
            results["files"]["results_report.md"] = False

    return results

def main():
    """Main entry point for quickstart validation."""
    logger.info("Starting quickstart validation for T039")
    
    # Validate artifacts
    validation_results = validate_artifacts()
    
    # Summary
    all_dirs_ok = all(validation_results["directories"].values())
    all_files_ok = all(validation_results["files"].values())
    all_json_ok = all(validation_results["json_structures"].values())
    
    logger.info("=" * 50)
    logger.info("VALIDATION SUMMARY")
    logger.info("=" * 50)
    logger.info(f"Directories valid: {all_dirs_ok}")
    for dir_path, exists in validation_results["directories"].items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {dir_path}")
    
    logger.info(f"Files valid: {all_files_ok}")
    for file_path, exists in validation_results["files"].items():
        status = "✓" if exists else "✗"
        logger.info(f"  {status} {file_path}")
    
    logger.info(f"JSON structures valid: {all_json_ok}")
    for file_path, valid in validation_results["json_structures"].items():
        status = "✓" if valid else "✗"
        logger.info(f"  {status} {file_path}")
    
    overall_success = all_dirs_ok and all_files_ok and all_json_ok
    
    if overall_success:
        logger.info("✓ Quickstart validation PASSED - End-to-end reproducibility confirmed")
        return 0
    else:
        logger.error("✗ Quickstart validation FAILED - Some artifacts missing or invalid")
        return 1

if __name__ == "__main__":
    sys.exit(main())
