"""
Integration test script for T023: Verify all baseline scripts (T020-T022)
correctly consume the unified data format from T004 and produce outputs
compatible with the evaluation script (T026a).

This script:
1. Ensures processed data exists (via T004/T006).
2. Runs Shewhart (T020), CUSUM (T021), and VAE (T022) baselines.
3. Validates output file existence and schema compatibility with T026a.
4. Verifies column alignment and data types expected by evaluate.py.
"""

import os
import sys
import logging
import argparse
import json
import pandas as pd
from pathlib import Path
from typing import Dict, Any, List

# Add project root to path for imports
project_root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(project_root / "code"))

from scripts.baseline_shewhart import main as run_shewhart
from scripts.baseline_cusum import main as run_cusum
from scripts.baseline_vae import main as run_vae
from scripts.baseline_integration import ensure_processed_data_exists

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("baseline_integration_test")

# Expected output paths defined in tasks.md
OUTPUT_DIR = project_root / "data" / "results"
EXPECTED_OUTPUTS = {
    "shewhart": OUTPUT_DIR / "shewhart_predictions.csv",
    "cusum": OUTPUT_DIR / "cusum_predictions.csv",
    "vae": OUTPUT_DIR / "vae_predictions.csv"
}

# Schema expected by T026a (evaluate.py) based on contracts/evaluation.schema.yaml
# Typically requires: timestamp, anomaly_score, prediction (binary)
REQUIRED_COLUMNS = {"timestamp", "anomaly_score", "prediction"}

def check_output_files(method: str, output_path: Path) -> Dict[str, Any]:
    """
    Verify output file exists, is readable, and contains required columns.
    Returns a status dictionary.
    """
    status = {
        "method": method,
        "file_exists": False,
        "file_readable": False,
        "schema_valid": False,
        "errors": []
    }

    if not output_path.exists():
        status["errors"].append(f"Output file missing: {output_path}")
        return status

    status["file_exists"] = True

    try:
        df = pd.read_csv(output_path)
        status["file_readable"] = True
    except Exception as e:
        status["errors"].append(f"Failed to read CSV: {str(e)}")
        return status

    # Check for required columns
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        status["errors"].append(f"Missing columns: {missing_cols}")
    else:
        status["schema_valid"] = True

    # Check basic data types
    if 'anomaly_score' in df.columns:
        if not pd.api.types.is_numeric_dtype(df['anomaly_score']):
            status["errors"].append("anomaly_score must be numeric")
        else:
            status["schema_valid"] = status["schema_valid"] and True

    return status

def run_baseline_script(script_func, name: str) -> bool:
    """
    Execute a baseline script's main function.
    Returns True if execution completes without exception.
    """
    logger.info(f"Running {name} baseline script...")
    try:
        # Construct a minimal argparse namespace if the script expects one
        # Most scripts in this project accept --input and --output via argparse
        # We rely on default config paths as per T004/T006 setup
        script_func()
        logger.info(f"{name} baseline completed successfully.")
        return True
    except SystemExit as e:
        if e.code == 0:
            logger.info(f"{name} baseline completed successfully (exit 0).")
            return True
        else:
            logger.error(f"{name} baseline failed with exit code: {e.code}")
            return False
    except Exception as e:
        logger.error(f"{name} baseline raised exception: {str(e)}")
        return False

def main():
    logger.info("Starting T023 Baseline Integration Verification")

    # 1. Ensure processed data exists
    logger.info("Checking for processed data...")
    if not ensure_processed_data_exists():
        logger.error("Processed data not found. Please run T004 and T006 first.")
        sys.exit(1)
    logger.info("Processed data verified.")

    # 2. Run Baselines
    baselines = [
        ("Shewhart (T020)", run_shewhart, EXPECTED_OUTPUTS["shewhart"]),
        ("CUSUM (T021)", run_cusum, EXPECTED_OUTPUTS["cusum"]),
        ("VAE (T022)", run_vae, EXPECTED_OUTPUTS["vae"])
    ]

    results = {}
    all_passed = True

    for name, func, output_path in baselines:
        logger.info(f"--- Executing {name} ---")
        success = run_baseline_script(func, name)
        if not success:
            logger.error(f"Execution failed for {name}. Skipping validation.")
            all_passed = False
            results[name] = {"execution": "failed", "validation": "skipped"}
            continue

        # 3. Validate Output
        logger.info(f"--- Validating {name} Output ---")
        validation = check_output_files(name, output_path)
        results[name] = {
            "execution": "success",
            "validation": validation
        }

        if not validation["file_exists"] or not validation["schema_valid"]:
            logger.error(f"{name} validation FAILED: {validation['errors']}")
            all_passed = False
        else:
            logger.info(f"{name} validation PASSED.")

    # 4. Summary Report
    logger.info("=== T023 Integration Verification Summary ===")
    if all_passed:
        logger.info("SUCCESS: All baseline scripts (T020-T022) produced valid outputs compatible with T026a.")
        sys.exit(0)
    else:
        logger.error("FAILURE: One or more baselines failed execution or validation.")
        for name, res in results.items():
            logger.error(f"  {name}: {res}")
        sys.exit(1)

if __name__ == "__main__":
    main()