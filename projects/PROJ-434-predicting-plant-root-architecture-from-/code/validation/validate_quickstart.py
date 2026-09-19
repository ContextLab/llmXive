import os
import sys
import subprocess
import json
import hashlib
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from utils.logging_utils import setup_logging, get_logger
from utils.exceptions import DataQualityError

# Configuration for expected outputs
EXPECTED_FILES = [
    "data/processed/merged_dataset.csv",
    "data/processed/soil_extracted.csv",
    "data/processed/soil_extracted.csv.sha256",
    "data/processed/species_counts.csv",
    "data/processed/excluded_species_summary.csv",
    "artifacts/model_metrics.json",
    "artifacts/loso_fold_scores.json",
    "artifacts/stratified_fold_scores.json",
    "artifacts/baseline_metrics.json",
    "artifacts/permutation_distributions.json",
    "artifacts/sc002_status.json",
    "artifacts/feature_importance.csv",
    "figures/feature_importance.png",
    "artifacts/sensitivity_report.md",
    "data/logs/source_validation.log",
    "data/logs/checksum_verification.log",
    "data/logs/record_exclusions.log",
    "data/logs/species_exclusions.log",
    "data/logs/api_errors.log",
    "data/logs/ingestion_summary.log",
    "data/logs/timing.log",
]

# Expected pipeline stages to execute (if not already run)
PIPELINE_STAGES = [
    {
        "name": "source_validation",
        "script": "ingestion.source_validation",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "soil_extraction",
        "script": "ingestion.soil_data",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "trait_loading",
        "script": "ingestion.trait_data",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "merge_and_filter",
        "script": "ingestion.merge",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "validation",
        "script": "ingestion.validation",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "model_training",
        "script": "modeling.train",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "baseline_analysis",
        "script": "modeling.baseline",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "permutation_tests",
        "script": "modeling.train",
        "env": {"RUN_MODE": "production", "STAGE": "permutation"}
    },
    {
        "name": "feature_importance",
        "script": "modeling.feature_importance",
        "env": {"RUN_MODE": "production"}
    },
    {
        "name": "sensitivity_analysis",
        "script": "modeling.sensitivity",
        "env": {"RUN_MODE": "production"}
    },
]

logger = None

def setup_validation_logging():
    global logger
    log_dir = PROJECT_ROOT / "data" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "quickstart_validation.log"
    logger = setup_logging(log_file, level=logging.INFO)
    return logger

def validate_file_exists(file_path: str) -> Tuple[bool, str]:
    """Check if a file exists and has non-zero size."""
    full_path = PROJECT_ROOT / file_path
    if not full_path.exists():
        return False, f"File not found: {file_path}"
    if full_path.stat().st_size == 0:
        return False, f"File is empty: {file_path}"
    return True, "OK"

def calculate_file_hash(file_path: str) -> Optional[str]:
    """Calculate SHA256 hash of a file."""
    full_path = PROJECT_ROOT / file_path
    if not full_path.exists():
        return None
    sha256_hash = hashlib.sha256()
    try:
        with open(full_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except Exception as e:
        logger.error(f"Error calculating hash for {file_path}: {e}")
        return None

def run_pipeline_stage(stage_info: Dict[str, Any]) -> Tuple[bool, str]:
    """Execute a single pipeline stage."""
    stage_name = stage_info["name"]
    script_module = stage_info["script"]
    env_vars = stage_info.get("env", {})

    logger.info(f"--- Running stage: {stage_name} ---")

    try:
        # Build command
        cmd = [sys.executable, "-m", script_module]

        # Prepare environment
        run_env = os.environ.copy()
        run_env.update(env_vars)

        # Execute
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            env=run_env,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout per stage
        )

        if result.returncode != 0:
            error_msg = f"Stage '{stage_name}' failed with exit code {result.returncode}.\nStderr: {result.stderr}"
            logger.error(error_msg)
            return False, error_msg

        logger.info(f"Stage '{stage_name}' completed successfully.")
        if result.stdout:
            for line in result.stdout.splitlines():
                logger.debug(f"  {line}")

        return True, "OK"

    except subprocess.TimeoutExpired:
        error_msg = f"Stage '{stage_name}' timed out after 3600 seconds."
        logger.error(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"Stage '{stage_name}' raised exception: {str(e)}"
        logger.error(error_msg)
        return False, error_msg

def verify_checksums() -> bool:
    """Verify checksums for critical data files."""
    logger.info("--- Verifying Checksums ---")
    checksum_file = PROJECT_ROOT / "data" / "processed" / "soil_extracted.csv.sha256"
    data_file = PROJECT_ROOT / "data" / "processed" / "soil_extracted.csv"

    if not checksum_file.exists() or not data_file.exists():
        logger.warning("Checksum file or data file missing. Skipping verification.")
        return True

    try:
        with open(checksum_file, "r") as f:
            stored_hash = f.read().split()[0]

        computed_hash = calculate_file_hash("data/processed/soil_extracted.csv")

        if computed_hash != stored_hash:
            logger.error(f"Checksum mismatch for soil_extracted.csv!")
            logger.error(f"  Stored:   {stored_hash}")
            logger.error(f"  Computed: {computed_hash}")
            return False

        logger.info("Checksum verification passed.")
        return True

    except Exception as e:
        logger.error(f"Error during checksum verification: {e}")
        return False

def validate_json_schema(file_path: str, required_keys: List[str]) -> Tuple[bool, str]:
    """Validate a JSON file contains required keys."""
    full_path = PROJECT_ROOT / file_path
    if not full_path.exists():
        return False, f"JSON file not found: {file_path}"

    try:
        with open(full_path, "r") as f:
            data = json.load(f)

        missing_keys = [k for k in required_keys if k not in data]
        if missing_keys:
            return False, f"Missing keys in {file_path}: {missing_keys}"

        return True, "OK"
    except json.JSONDecodeError as e:
        return False, f"Invalid JSON in {file_path}: {e}"
    except Exception as e:
        return False, f"Error reading {file_path}: {e}"

def main():
    """Main validation entry point."""
    setup_validation_logging()
    logger.info("=" * 60)
    logger.info("Starting quickstart.md validation (T034)")
    logger.info("=" * 60)

    validation_results = {
        "files_checked": [],
        "stages_executed": [],
        "checksums_verified": False,
        "json_validations": [],
        "overall_success": False,
        "errors": []
    }

    # 1. Check expected files exist
    logger.info("Step 1: Checking expected output files...")
    all_files_exist = True
    for file_path in EXPECTED_FILES:
        exists, msg = validate_file_exists(file_path)
        validation_results["files_checked"].append({"file": file_path, "status": "PASS" if exists else "FAIL"})
        if not exists:
            all_files_exist = False
            validation_results["errors"].append(msg)
            logger.warning(f"Missing/Invalid: {file_path} - {msg}")
        else:
            logger.info(f"Found: {file_path}")

    if not all_files_exist:
        logger.error("Not all expected files exist. Attempting to re-run pipeline stages.")
        # Attempt to re-run missing stages (simplified logic)
        for stage in PIPELINE_STAGES:
            success, msg = run_pipeline_stage(stage)
            validation_results["stages_executed"].append({"stage": stage["name"], "status": "PASS" if success else "FAIL"})
            if not success:
                validation_results["errors"].append(msg)

    # 2. Verify Checksums
    logger.info("Step 2: Verifying checksums...")
    checksum_ok = verify_checksums()
    validation_results["checksums_verified"] = checksum_ok
    if not checksum_ok:
        validation_results["errors"].append("Checksum verification failed.")

    # 3. Validate JSON schemas
    logger.info("Step 3: Validating JSON schemas...")
    json_checks = [
        ("artifacts/model_metrics.json", ["model_a_r2_primary", "model_b_r2_primary"]),
        ("artifacts/sc002_status.json", ["pass", "reason"]),
        ("artifacts/baseline_metrics.json", ["mean_baseline_r2"]),
    ]
    for file_path, keys in json_checks:
        valid, msg = validate_json_schema(file_path, keys)
        validation_results["json_validations"].append({"file": file_path, "status": "PASS" if valid else "FAIL"})
        if not valid:
            validation_results["errors"].append(msg)
            logger.warning(f"JSON validation failed for {file_path}: {msg}")
        else:
            logger.info(f"JSON valid: {file_path}")

    # 4. Final Report
    logger.info("Step 4: Generating validation report...")
    overall_success = (
        all(f["status"] == "PASS" for f in validation_results["files_checked"]) and
        checksum_ok and
        all(f["status"] == "PASS" for f in validation_results["json_validations"]) and
        len(validation_results["errors"]) == 0
    )

    validation_results["overall_success"] = overall_success

    report_path = PROJECT_ROOT / "artifacts" / "quickstart_validation_report.json"
    report_path.parent.mkdir(parents=True, exist_ok=True)
    with open(report_path, "w") as f:
        json.dump(validation_results, f, indent=2)

    logger.info("=" * 60)
    if overall_success:
        logger.info("VALIDATION PASSED: End-to-end reproducibility confirmed.")
        print("SUCCESS: Quickstart validation passed. All artifacts present and valid.")
        sys.exit(0)
    else:
        logger.error("VALIDATION FAILED: Reproducibility check failed.")
        for err in validation_results["errors"]:
            logger.error(f"  - {err}")
        print("FAILURE: Quickstart validation failed. See logs for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()