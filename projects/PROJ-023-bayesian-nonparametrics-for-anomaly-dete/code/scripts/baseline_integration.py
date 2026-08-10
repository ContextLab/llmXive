"""
Baseline Integration Script

This script integrates baseline anomaly detection methods (Shewhart, CUSUM, VAE)
with the shared data loader and anomaly injection pipeline from User Story 1.

It ensures that the required processed data exists (produced by T014) and
orchestrates the execution of all baseline scripts in sequence.
"""
import os
import sys
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DATA_DIR = PROJECT_ROOT / "data" / "processed"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Required input files from US1 (T014)
REQUIRED_INPUT_FILES = {
    "series_with_anomalies": PROCESSED_DATA_DIR / "series_with_anomalies.csv",
    "ground_truth": PROCESSED_DATA_DIR / "ground_truth.csv"
}

# Baseline scripts to run
BASELINE_SCRIPTS = [
    "baseline_shewhart.py",
    "baseline_cusum.py",
    "baseline_vae.py"
]

def ensure_processed_data_exists() -> bool:
    """
    Verify that the processed data files from T014 (inject_anomalies.py) exist.
    These files are required inputs for all baseline detection scripts.

    Returns:
        True if all required files exist, False otherwise.
    """
    missing_files = []
    for name, path in REQUIRED_INPUT_FILES.items():
        if not path.exists():
            missing_files.append(f"{name}: {path}")
            logger.error(f"Missing required input file: {path}")
        else:
            logger.info(f"Found required input file: {path}")

    if missing_files:
        logger.error(
            f"Missing {len(missing_files)} required input files. "
            "Please run 'inject_anomalies.py' (T014) first."
        )
        return False

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    return True

def run_baseline_script(script_name: str) -> bool:
    """
    Execute a specific baseline detection script.

    Args:
        script_name: Name of the script file in code/scripts/

    Returns:
        True if the script executed successfully, False otherwise.
    """
    script_path = PROJECT_ROOT / "code" / "scripts" / script_name

    if not script_path.exists():
        logger.error(f"Baseline script not found: {script_path}")
        return False

    logger.info(f"Running baseline script: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            check=True,
            capture_output=False,
            text=True
        )
        logger.info(f"Successfully completed: {script_name}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Failed to execute {script_name}: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error running {script_name}: {e}")
        return False

def check_output_files() -> Dict[str, bool]:
    """
    Verify that all baseline scripts produced their expected output files.

    Returns:
        Dictionary mapping script name to success status.
    """
    expected_outputs = {
        "baseline_shewhart.py": RESULTS_DIR / "shewhart_predictions.csv",
        "baseline_cusum.py": RESULTS_DIR / "cusum_predictions.csv",
        "baseline_vae.py": RESULTS_DIR / "vae_predictions.csv"
    }

    results = {}
    for script, output_path in expected_outputs.items():
        if output_path.exists():
            logger.info(f"Verified output: {output_path}")
            results[script] = True
        else:
            logger.warning(f"Missing expected output: {output_path}")
            results[script] = False

    return results

def main():
    """
    Main entry point for baseline integration.

    1. Ensures processed data from T014 exists.
    2. Runs all baseline scripts (Shewhart, CUSUM, VAE).
    3. Verifies output files were created.
    """
    parser = argparse.ArgumentParser(
        description="Integrate baseline anomaly detection scripts with US1 pipeline."
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="Skip input file verification and run all baselines anyway."
    )
    args = parser.parse_args()

    logger.info("Starting baseline integration pipeline...")

    # Step 1: Verify input data exists (unless skipped)
    if not args.skip_check:
        if not ensure_processed_data_exists():
            logger.error("Input data verification failed. Aborting.")
            sys.exit(1)
    else:
        logger.warning("Skipping input data verification as requested.")

    # Step 2: Run all baseline scripts
    success_count = 0
    total_count = len(BASELINE_SCRIPTS)

    for script in BASELINE_SCRIPTS:
        if run_baseline_script(script):
            success_count += 1
        else:
            logger.error(f"Script {script} failed. Continuing with others...")

    # Step 3: Verify outputs
    logger.info("Verifying baseline output files...")
    output_status = check_output_files()
    verified_count = sum(1 for status in output_status.values() if status)

    # Summary
    logger.info("-" * 50)
    logger.info(f"Baseline Integration Summary:")
    logger.info(f"  Scripts executed: {success_count}/{total_count}")
    logger.info(f"  Outputs verified: {verified_count}/{total_count}")
    logger.info("-" * 50)

    if success_count == total_count and verified_count == total_count:
        logger.info("SUCCESS: All baseline scripts completed and outputs verified.")
        sys.exit(0)
    else:
        logger.error("FAILURE: Some baseline scripts failed or outputs are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()