"""
Baseline Integration Script.

This script verifies that all baseline scripts (Shewhart, CUSUM, VAE) correctly
consume the unified data format from T004 and produce outputs compatible with
the evaluation script (T026a).

It acts as an integration test runner and verifier for User Story 2.
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
PROJECT_ROOT = Path(__file__).resolve().parents[2]
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = PROJECT_ROOT / "data"
RESULTS_DIR = DATA_DIR / "results"
SCRIPTS_DIR = CODE_DIR / "scripts"

# Baseline scripts to verify
BASELINE_SCRIPTS = [
    "baseline_shewhart.py",
    "baseline_cusum.py",
    "baseline_vae.py"
]

# Expected output files
EXPECTED_OUTPUTS = {
    "baseline_shewhart.py": "shewhart_predictions.csv",
    "baseline_cusum.py": "cusum_predictions.csv",
    "baseline_vae.py": "vae_predictions.csv"
}

def ensure_processed_data_exists() -> bool:
    """
    Verify that processed data required by baselines exists.
    
    Returns:
        True if data exists, False otherwise.
    """
    processed_dir = DATA_DIR / "processed"
    required_files = [
        "series_with_anomalies.csv",
        "ground_truth.csv"
    ]
    
    for file_name in required_files:
        file_path = processed_dir / file_name
        if not file_path.exists():
            logger.error(f"Required processed data file missing: {file_path}")
            return False
    
    logger.info("All required processed data files found.")
    return True

def run_baseline_script(script_name: str) -> bool:
    """
    Execute a baseline script and verify it runs without error.
    
    Args:
        script_name: Name of the script to run.
        
    Returns:
        True if script ran successfully, False otherwise.
    """
    script_path = SCRIPTS_DIR / script_name
    if not script_path.exists():
        logger.error(f"Script not found: {script_path}")
        return False
    
    logger.info(f"Running baseline script: {script_name}")
    try:
        result = subprocess.run(
            [sys.executable, str(script_path)],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            timeout=300  # 5 minute timeout
        )
        
        if result.returncode != 0:
            logger.error(f"Script {script_name} failed with return code {result.returncode}")
            logger.error(f"STDOUT: {result.stdout}")
            logger.error(f"STDERR: {result.stderr}")
            return False
        
        logger.info(f"Script {script_name} completed successfully.")
        return True
    except subprocess.TimeoutExpired:
        logger.error(f"Script {script_name} timed out.")
        return False
    except Exception as e:
        logger.error(f"Error running script {script_name}: {e}")
        return False

def check_output_files(script_name: str) -> bool:
    """
    Verify that a baseline script produced its expected output file.
    
    Args:
        script_name: Name of the script that should have produced the output.
        
    Returns:
        True if output file exists and is non-empty, False otherwise.
    """
    expected_file = EXPECTED_OUTPUTS.get(script_name)
    if not expected_file:
        logger.warning(f"No expected output defined for {script_name}")
        return True
    
    output_path = RESULTS_DIR / expected_file
    if not output_path.exists():
        logger.error(f"Expected output file missing: {output_path}")
        return False
    
    if output_path.stat().st_size == 0:
        logger.error(f"Expected output file is empty: {output_path}")
        return False
    
    logger.info(f"Output file verified: {output_path} ({output_path.stat().st_size} bytes)")
    return True

def verify_schema_compatibility() -> bool:
    """
    Verify that all baseline outputs have compatible schemas for evaluation.
    
    Checks:
    - All files exist
    - All files have the same number of rows
    - All files contain required columns (timestamp, prediction, score)
    
    Returns:
        True if schemas are compatible, False otherwise.
    """
    logger.info("Verifying schema compatibility across baseline outputs...")
    
    required_columns = ["timestamp", "prediction", "score"]
    row_counts = {}
    
    for script_name, file_name in EXPECTED_OUTPUTS.items():
        output_path = RESULTS_DIR / file_name
        if not output_path.exists():
            logger.error(f"Cannot verify schema: file missing {output_path}")
            return False
        
        try:
            import pandas as pd
            df = pd.read_csv(output_path)
            
            # Check required columns
            missing_cols = [col for col in required_columns if col not in df.columns]
            if missing_cols:
                logger.error(f"File {file_name} missing required columns: {missing_cols}")
                return False
            
            row_counts[script_name] = len(df)
            logger.info(f"  {file_name}: {len(df)} rows, columns: {list(df.columns)}")
            
        except Exception as e:
            logger.error(f"Error reading {output_path}: {e}")
            return False
    
    # Verify all files have the same number of rows
    if len(set(row_counts.values())) > 1:
        logger.error("Row count mismatch across baseline outputs:")
        for script, count in row_counts.items():
            logger.error(f"  {script}: {count} rows")
        return False
    
    logger.info(f"All outputs have consistent row count: {list(row_counts.values())[0]}")
    return True

def main(args: argparse.Namespace = None) -> int:
    """
    Main entry point for baseline integration verification.
    
    Returns:
        0 if all checks pass, 1 otherwise.
    """
    logger.info("Starting Baseline Integration Verification (T023)")
    
    # Step 1: Ensure processed data exists
    if not ensure_processed_data_exists():
        logger.error("Processed data not found. Please run data loading first.")
        return 1
    
    # Step 2: Run all baseline scripts
    all_scripts_ran = True
    for script_name in BASELINE_SCRIPTS:
        if not run_baseline_script(script_name):
            all_scripts_ran = False
    
    if not all_scripts_ran:
        logger.error("One or more baseline scripts failed to run.")
        return 1
    
    # Step 3: Verify output files exist
    all_outputs_exist = True
    for script_name in BASELINE_SCRIPTS:
        if not check_output_files(script_name):
            all_outputs_exist = False
    
    if not all_outputs_exist:
        logger.error("One or more baseline outputs are missing or empty.")
        return 1
    
    # Step 4: Verify schema compatibility
    if not verify_schema_compatibility():
        logger.error("Baseline outputs are not schema-compatible.")
        return 1
    
    logger.info("✓ All baseline integration checks passed.")
    logger.info("  - All scripts executed successfully")
    logger.info("  - All output files generated")
    logger.info("  - All outputs have compatible schemas for evaluation (T026a)")
    return 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Baseline Integration Verification")
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    sys.exit(main(args))
