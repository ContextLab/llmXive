"""
Task T058: Run quickstart.md validation.

This script validates the project setup and data pipeline by:
1. Verifying required directories exist.
2. Checking that requirements.txt is valid.
3. Running the ingestion pipeline (generate_master_dataset).
4. Running the analysis pipeline (run_analysis).
5. Running the reporting pipeline (run_report_pipeline).
6. Verifying output artifacts exist.
"""

import os
import sys
import logging
import subprocess
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_RAW = PROJECT_ROOT / "data" / "raw"
DATA_DERIVED = PROJECT_ROOT / "data" / "derived"
DOCS_OUTPUT = PROJECT_ROOT / "docs" / "output"
REQUIREMENTS = PROJECT_ROOT / "requirements.txt"

# Expected output artifacts
EXPECTED_ARTIFACTS = [
    DATA_DERIVED / "master_dataset.csv",
    DATA_DERIVED / "analysis_results.json",
    DATA_DERIVED / "sensitivity_analysis.json",
    DOCS_OUTPUT / "final_report.pdf",
    REQUIREMENTS
]

def check_directory(path: Path) -> bool:
    """Check if a directory exists, create if missing."""
    if not path.exists():
        logger.info(f"Creating directory: {path}")
        path.mkdir(parents=True, exist_ok=True)
        return True
    return True

def check_requirements() -> bool:
    """Verify requirements.txt exists and is non-empty."""
    if not REQUIREMENTS.exists():
        logger.error(f"Missing requirements.txt at {REQUIREMENTS}")
        return False
    with open(REQUIREMENTS, 'r') as f:
        content = f.read().strip()
        if not content:
            logger.error("requirements.txt is empty")
            return False
    logger.info("requirements.txt validated")
    return True

def run_script(script_name: str, args: list = None) -> bool:
    """Run a Python script from the code directory."""
    script_path = PROJECT_ROOT / "code" / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False

    cmd = [sys.executable, str(script_path)]
    if args:
        cmd.extend(args)

    logger.info(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=False
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        logger.error(f"Script {script_name} failed with code {e.returncode}")
        return False
    except Exception as e:
        logger.error(f"Error running {script_name}: {e}")
        return False

def verify_outputs() -> bool:
    """Verify all expected output artifacts exist."""
    all_present = True
    for artifact in EXPECTED_ARTIFACTS:
        if artifact.exists():
            logger.info(f"Found: {artifact}")
        else:
            logger.warning(f"Missing: {artifact}")
            all_present = False
    return all_present

def main():
    logger.info("Starting Quickstart Validation (T058)")

    # 1. Ensure directories exist
    logger.info("Checking directories...")
    check_directory(DATA_RAW)
    check_directory(DATA_DERIVED)
    check_directory(DOCS_OUTPUT)

    # 2. Check requirements
    if not check_requirements():
        logger.error("Validation failed: requirements.txt issue")
        return 1

    # 3. Run Ingestion Pipeline
    logger.info("Running Ingestion Pipeline...")
    if not run_script("generate_master_dataset.py"):
        logger.error("Ingestion failed. Cannot proceed.")
        return 1

    # 4. Run Analysis Pipeline
    logger.info("Running Analysis Pipeline...")
    if not run_script("analyze.py"):
        logger.error("Analysis failed. Cannot proceed.")
        return 1

    # 5. Run Reporting Pipeline
    logger.info("Running Reporting Pipeline...")
    if not run_script("report.py"):
        logger.error("Reporting failed. Cannot proceed.")
        return 1

    # 6. Verify Outputs
    logger.info("Verifying output artifacts...")
    if not verify_outputs():
        logger.error("Validation failed: Missing output artifacts")
        return 1

    logger.info("Quickstart Validation (T058) PASSED successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())