"""
Task T043: Run full pipeline on the dataset subset and verify audit_report.md is produced.

This script orchestrates the execution of the full pipeline steps in the correct order,
handles errors explicitly, and verifies that the final artifact (audit_report.md) exists.
"""
import os
import sys
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path to allow imports from code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
PROCESSED_DIR = DATA_DIR / "processed"
RAW_DIR = DATA_DIR / "raw"

# Ensure paths are in sys.path for relative imports if running as script
if str(CODE_DIR) not in sys.path:
    sys.path.insert(0, str(CODE_DIR))

from utils.logging_config import setup_logging

# Configure logging for this orchestration script
logger = setup_logging("pipeline_orchestrator", log_file=DATA_DIR / "pipeline_run.log")


def run_step(step_name: str, script_name: str, module_name: str, args: Optional[List[str]] = None) -> bool:
    """
    Executes a pipeline step as a Python module.
    Returns True if successful, False otherwise.
    """
    logger.info(f"Starting step: {step_name} ({script_name})")
    try:
        # Construct the command to run the module
        cmd = [sys.executable, "-m", module_name]
        if args:
            cmd.extend(args)

        # Run the subprocess
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=3600  # 1 hour timeout per step
        )

        if result.returncode != 0:
            logger.error(f"Step {step_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False

        logger.info(f"Step {step_name} completed successfully.")
        return True

    except subprocess.TimeoutExpired:
        logger.error(f"Step {step_name} timed out.")
        return False
    except Exception as e:
        logger.error(f"Step {step_name} raised an exception: {str(e)}")
        return False


def verify_artifact(path: Path, description: str) -> bool:
    """Verifies that a required artifact exists."""
    if path.exists():
        logger.info(f"Verified artifact: {description} at {path}")
        return True
    else:
        logger.error(f"Missing required artifact: {description} at {path}")
        return False


def main():
    logger.info("=" * 60)
    logger.info("Starting Full Pipeline Execution (T043)")
    logger.info("=" * 60)

    # Ensure output directories exist
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    # Define the pipeline steps in execution order
    # Note: We assume T012-T016 (Ingest), T021 (Parse), T031-T033 (Compute), T036 (MDes), T034-T037 (Report) are implemented as modules.
    # Based on the API surface, we map tasks to modules.
    
    steps = [
        {
            "name": "Ingest OpenML Data",
            "script": "01_ingest_openml.py",
            "module": "01_ingest_openml",
            "args": []
        },
        {
            "name": "Parse Publications",
            "script": "02_parse_publications.py",
            "module": "02_parse_publications",
            "args": []
        },
        {
            "name": "Compute Sensitivity (Power & MDES)",
            "script": "03_compute_sensitivity.py",
            "module": "03_compute_sensitivity",
            "args": []
        },
        {
            "name": "Generate MDES Histogram",
            "script": "06_generate_mdes_histogram.py",
            "module": "06_generate_mdes_histogram",
            "args": []
        },
        {
            "name": "Generate Final Report",
            "script": "04_generate_report.py",
            "module": "04_generate_report",
            "args": []
        },
        {
            "name": "Append Disclaimer",
            "script": "04_append_disclaimer.py",
            "module": "04_append_disclaimer",
            "args": []
        }
    ]

    all_success = True

    for step in steps:
        success = run_step(step["name"], step["script"], step["module"], step.get("args"))
        if not success:
            all_success = False
            logger.error(f"Pipeline stopped due to failure in step: {step['name']}")
            break

    if not all_success:
        logger.error("Full pipeline execution FAILED.")
        sys.exit(1)

    # Verification Phase
    logger.info("Verifying final artifacts...")
    
    audit_report_path = PROCESSED_DIR / "audit_report.md"
    success = verify_artifact(audit_report_path, "audit_report.md")

    if not success:
        logger.error("Final verification FAILED: audit_report.md not found.")
        sys.exit(1)

    # Optional: Check for other key intermediate files if needed for robustness
    key_files = [
        RAW_DIR / "openml_metadata_filtered.json",
        PROCESSED_DIR / "extracted_params.json",
        PROCESSED_DIR / "power_audit_results.json",
        PROCESSED_DIR / "mdes_histogram.png",
        PROCESSED_DIR / "power_histogram.png"
    ]

    for f in key_files:
        if not f.exists():
            logger.warning(f"Intermediate artifact missing (non-fatal for T043 success): {f}")
        else:
            logger.info(f"Found intermediate artifact: {f}")

    logger.info("=" * 60)
    logger.info("Full Pipeline Execution (T043) COMPLETED SUCCESSFULLY")
    logger.info(f"Output: {audit_report_path}")
    logger.info("=" * 60)
    
    sys.exit(0)


if __name__ == "__main__":
    main()
