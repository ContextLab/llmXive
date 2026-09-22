"""
Baseline Integration Script (T023).

This script integrates the baseline anomaly detection algorithms (Shewhart, CUSUM, VAE)
with the shared data loader and anomaly injection pipeline from User Story 1.

It ensures that the processed data (with injected anomalies) exists, runs the baseline
scripts in sequence, and validates that the expected output files are generated.
"""
import os
import sys
import logging
import argparse
import subprocess
from pathlib import Path
from typing import List, Optional

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Project root relative to script
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROCESSED_DATA_PATH = PROJECT_ROOT / "data" / "processed" / "series_with_anomalies.csv"
GROUND_TRUTH_PATH = PROJECT_ROOT / "data" / "processed" / "ground_truth.csv"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Baseline scripts to integrate
BASELINE_SCRIPTS = [
    "baseline_shewhart.py",
    "baseline_cusum.py",
    "baseline_vae.py"
]

def ensure_processed_data_exists() -> bool:
    """
    Verify that the processed data from US1 (T014) exists.
    
    Returns:
        bool: True if files exist, False otherwise.
    """
    if not PROCESSED_DATA_PATH.exists():
        logger.error(f"Processed data not found: {PROCESSED_DATA_PATH}")
        logger.error("Please run 'inject_anomalies.py' (T014) first to generate this file.")
        return False
    
    if not GROUND_TRUTH_PATH.exists():
        logger.warning(f"Ground truth file not found: {GROUND_TRUTH_PATH}")
        logger.warning("Some evaluation metrics might be unavailable, but baseline execution can proceed.")
    
    logger.info(f"Verified processed data exists: {PROCESSED_DATA_PATH}")
    return True

def run_baseline_script(script_name: str) -> bool:
    """
    Execute a specific baseline script.
    
    Args:
        script_name: Name of the script in code/scripts/
        
    Returns:
        bool: True if script completed successfully (exit code 0), False otherwise.
    """
    script_path = PROJECT_ROOT / "code" / "scripts" / script_name
    
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running {script_name}...")
    
    try:
        # Run the script using the same python interpreter
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=str(PROJECT_ROOT),
            capture_output=False,
            text=True
        )
        
        if result.returncode == 0:
            logger.info(f"{script_name} completed successfully.")
            return True
        else:
            logger.error(f"{script_name} failed with exit code {result.returncode}")
            return False
            
    except Exception as e:
        logger.error(f"Exception running {script_name}: {e}")
        return False

def check_output_files(script_name: str) -> bool:
    """
    Verify that the expected output file for a baseline script was created.
    
    Args:
        script_name: Name of the script (e.g., 'baseline_shewhart.py')
        
    Returns:
        bool: True if output file exists, False otherwise.
    """
    # Map script names to expected output files
    output_map = {
        "baseline_shewhart.py": "shewhart_predictions.csv",
        "baseline_cusum.py": "cusum_predictions.csv",
        "baseline_vae.py": "vae_predictions.csv"
    }
    
    expected_file = output_map.get(script_name)
    if not expected_file:
        logger.warning(f"No output mapping found for {script_name}")
        return True # Don't fail if we don't know the output
    
    output_path = RESULTS_DIR / expected_file
    
    if output_path.exists():
        logger.info(f"Verified output exists: {output_path}")
        return True
    else:
        logger.error(f"Expected output file missing: {output_path}")
        return False

def main(args: Optional[argparse.Namespace] = None) -> int:
    """
    Main entry point for the baseline integration pipeline.
    
    Orchestrates the execution of all baseline scripts after ensuring
    the prerequisite data from US1 is available.
    """
    parser = argparse.ArgumentParser(
        description="Integrate and run baseline anomaly detection scripts."
    )
    parser.add_argument(
        "--skip-check",
        action="store_true",
        help="Skip the check for processed data existence (use with caution)."
    )
    
    parsed_args = parser.parse_args() if args is None else args

    # Ensure results directory exists
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Step 1: Verify prerequisite data from US1
    if not parsed_args.skip_check:
        if not ensure_processed_data_exists():
            logger.error("Prerequisite data missing. Aborting.")
            return 1

    # Step 2: Run all baseline scripts
    success_count = 0
    failed_scripts = []

    for script in BASELINE_SCRIPTS:
        logger.info(f"--- Processing {script} ---")
        
        if run_baseline_script(script):
            if check_output_files(script):
                success_count += 1
            else:
                failed_scripts.append(f"{script} (output missing)")
        else:
            failed_scripts.append(f"{script} (execution failed)")

    # Step 3: Summary
    logger.info("=" * 40)
    logger.info(f"Integration Summary: {success_count}/{len(BASELINE_SCRIPTS)} scripts successful.")
    
    if failed_scripts:
        logger.error("Failed scripts:")
        for fail in failed_scripts:
            logger.error(f"  - {fail}")
        return 1
    else:
        logger.info("All baseline scripts executed and outputs verified successfully.")
        return 0

if __name__ == "__main__":
    sys.exit(main())