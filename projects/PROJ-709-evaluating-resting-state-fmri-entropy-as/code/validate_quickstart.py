"""
T045: Run quickstart.md validation.

This script validates the Quickstart section of the project by:
1. Verifying that `python code/main.py --help` executes without error.
2. Verifying that `python code/main.py` (without args) runs the full pipeline
   and produces the expected output artifacts defined in tasks.md.
3. Asserting the existence of required output files.
"""

import os
import subprocess
import sys
import argparse
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root (assumed to be the parent of 'code')
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
DERIVED_DIR = DATA_DIR / "derived"

# Expected output artifacts from tasks.md (T018, T032, T038, T039)
EXPECTED_ARTIFACTS = [
    PROCESSED_DIR / "subject_entropy_features.csv",
    DERIVED_DIR / "model_metrics.json",
    DERIVED_DIR / "motion_confound_report.json",
    DERIVED_DIR / "valid_subjects.csv",
    DERIVED_DIR / "cohort_entropy_medians.csv",
]

def run_command(cmd: list, description: str) -> bool:
    """Run a shell command and return True if successful."""
    logger.info(f"Running: {description}")
    logger.info(f"Command: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=3600  # 1 hour timeout for full pipeline
        )
        if result.returncode != 0:
            logger.error(f"Command failed with return code {result.returncode}")
            logger.error(f"STDOUT:\n{result.stdout}")
            logger.error(f"STDERR:\n{result.stderr}")
            return False
        if result.stdout:
            logger.info(f"Output:\n{result.stdout}")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Command timed out: {description}")
        return False
    except Exception as e:
        logger.error(f"Exception running command: {e}")
        return False

def validate_help_command() -> bool:
    """Validate that main.py --help works."""
    cmd = [sys.executable, str(CODE_DIR / "main.py"), "--help"]
    return run_command(cmd, "Validate main.py --help")

def validate_full_pipeline() -> bool:
    """Validate that main.py runs the full pipeline."""
    cmd = [sys.executable, str(CODE_DIR / "main.py")]
    return run_command(cmd, "Run full pipeline via main.py")

def verify_artifacts() -> bool:
    """Verify that all expected output artifacts exist."""
    logger.info("Verifying expected output artifacts...")
    all_exist = True
    for artifact_path in EXPECTED_ARTIFACTS:
        if artifact_path.exists():
            logger.info(f"  [OK] Found: {artifact_path.relative_to(PROJECT_ROOT)}")
            # Check file size > 0
            if artifact_path.stat().st_size == 0:
                logger.error(f"  [FAIL] File is empty: {artifact_path}")
                all_exist = False
        else:
            logger.error(f"  [FAIL] Missing: {artifact_path.relative_to(PROJECT_ROOT)}")
            all_exist = False
    return all_exist

def main():
    logger.info("Starting Quickstart Validation (T045)...")
    logger.info(f"Project Root: {PROJECT_ROOT}")

    # Step 1: Validate --help
    if not validate_help_command():
        logger.error("Quickstart validation FAILED: --help command failed.")
        return 1

    # Step 2: Run full pipeline
    if not validate_full_pipeline():
        logger.error("Quickstart validation FAILED: Full pipeline execution failed.")
        return 1

    # Step 3: Verify artifacts
    if not verify_artifacts():
        logger.error("Quickstart validation FAILED: Expected artifacts missing or empty.")
        return 1

    logger.info("Quickstart validation PASSED successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())