"""
Integration test suite for the full pipeline: US1 -> US2 -> US3.

This script verifies that:
1. Salience maps are generated (US1).
2. Fixation metrics are extracted and aligned (US2).
3. LMM models are fitted and results written (US3).

It relies on the existence of real data artifacts produced by previous tasks.
If data is missing, it attempts to run the ingestion/processing scripts 
to generate them, ensuring the full chain works.
"""
import os
import sys
import json
import logging
import traceback
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "code"))

from config import get_paths, load_config
from utils.logging import get_logger, setup_logging
from ingestion.download_data import main as download_main
from ingestion.salience_gen import main as salience_main
from ingestion.metadata_writer import main as metadata_writer_main
from processing.segmentation import main as segmentation_main
from processing.eye_tracking import main as eye_tracking_main
from processing.alignment import main as alignment_main
from analysis.lmm_fit import main as lmm_main
from analysis.robustness import main as robustness_main
from analysis.plot_sensitivity import main as plot_sensitivity_main

# Setup logging for the integration test
setup_logging(log_level=logging.INFO, log_file="data/logs/integration_test.log")
logger = get_logger("integration_test")

def check_artifact_exists(path_str: str, description: str) -> bool:
    """Check if an artifact exists and is non-empty."""
    p = Path(path_str)
    if not p.exists():
        logger.error(f"MISSING: {description} at {path_str}")
        return False
    if p.stat().st_size == 0:
        logger.error(f"EMPTY: {description} at {path_str}")
        return False
    logger.info(f"OK: {description} found at {path_str}")
    return True

def run_stage(stage_name: str, func, *args, **kwargs) -> bool:
    """Run a pipeline stage and catch errors."""
    logger.info(f"--- Running Stage: {stage_name} ---")
    try:
        func(*args, **kwargs)
        logger.info(f"Stage {stage_name} completed successfully.")
        return True
    except Exception as e:
        logger.error(f"Stage {stage_name} FAILED: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def verify_us1_outputs() -> bool:
    """Verify US1 outputs: Salience maps and metadata."""
    paths = get_paths()
    checks = [
        (str(paths["salience_maps_dir"] / "metadata.json"), "Salience Metadata"),
    ]
    # Check for at least one .npy file
    npy_files = list(paths["salience_maps_dir"].glob("*.npy"))
    if not npy_files:
        logger.error("No salience map .npy files found.")
        return False
    logger.info(f"Found {len(npy_files)} salience map files.")
    
    # Verify metadata content
    meta_path = paths["salience_maps_dir"] / "metadata.json"
    if meta_path.exists():
        try:
            with open(meta_path, 'r') as f:
                data = json.load(f)
                if "disclaimer" not in str(data).lower():
                    logger.warning("Metadata missing 'correlational only' disclaimer.")
        except Exception as e:
            logger.error(f"Failed to read metadata.json: {e}")
            return False
    return True

def verify_us2_outputs() -> bool:
    """Verify US2 outputs: Fixation metrics and aligned dataset."""
    paths = get_paths()
    checks = [
        (str(paths["interim_dir"] / "fixation_metrics.csv"), "Fixation Metrics CSV"),
        (str(paths["processed_dir"] / "aligned_metrics.csv"), "Aligned Metrics CSV"),
    ]
    for path_str, desc in checks:
        if not check_artifact_exists(path_str, desc):
            return False
    return True

def verify_us3_outputs() -> bool:
    """Verify US3 outputs: LMM results, sensitivity plot, final results."""
    paths = get_paths()
    checks = [
        (str(paths["processed_dir"] / "results.json"), "Final Results JSON"),
        (str(paths["processed_dir"] / "sensitivity_plot.png"), "Sensitivity Plot"),
    ]
    for path_str, desc in checks:
        if not check_artifact_exists(path_str, desc):
            return False
    return True

def main():
    logger.info("Starting Full Integration Test Suite (T040)")
    paths = get_paths()
    config = load_config()
    
    # 1. Ensure Data Exists (US1)
    # If salience maps are missing, run the ingestion pipeline
    salience_dir = paths["salience_maps_dir"]
    if not salience_dir.exists() or not list(salience_dir.glob("*.npy")):
        logger.warning("Salience maps missing. Running US1 pipeline...")
        # Note: In a real CI, we might skip this if data is expected to be pre-seeded.
        # For this integration test, we attempt to run the generators.
        # We assume download_data has already been run or data is present in data/raw.
        if not run_stage("US1: Salience Generation", salience_main):
            logger.error("US1 Salience Generation failed. Aborting.")
            return False
        
        if not run_stage("US1: Metadata Writing", metadata_writer_main):
            logger.error("US1 Metadata Writing failed. Aborting.")
            return False

    if not verify_us1_outputs():
        logger.error("US1 Verification Failed.")
        return False

    # 2. Ensure Processing Exists (US2)
    # If fixation metrics are missing, run processing
    fixation_file = paths["interim_dir"] / "fixation_metrics.csv"
    aligned_file = paths["processed_dir"] / "aligned_metrics.csv"
    
    if not fixation_file.exists() or not aligned_file.exists():
        logger.warning("US2 outputs missing. Running US2 pipeline...")
        if not run_stage("US2: Segmentation", segmentation_main):
            logger.error("US2 Segmentation failed. Aborting.")
            return False
        
        if not run_stage("US2: Eye Tracking", eye_tracking_main):
            logger.error("US2 Eye Tracking failed. Aborting.")
            return False
        
        if not run_stage("US2: Alignment", alignment_main):
            logger.error("US2 Alignment failed. Aborting.")
            return False

    if not verify_us2_outputs():
        logger.error("US2 Verification Failed.")
        return False

    # 3. Ensure Analysis Exists (US3)
    results_file = paths["processed_dir"] / "results.json"
    if not results_file.exists():
        logger.warning("US3 outputs missing. Running US3 pipeline...")
        if not run_stage("US3: LMM Fitting", lmm_main):
            logger.error("US3 LMM Fitting failed. Aborting.")
            return False
        
        if not run_stage("US3: Robustness/Sensitivity", robustness_main):
            logger.error("US3 Robustness failed. Aborting.")
            return False
        
        if not run_stage("US3: Plotting", plot_sensitivity_main):
            logger.error("US3 Plotting failed. Aborting.")
            return False

    if not verify_us3_outputs():
        logger.error("US3 Verification Failed.")
        return False

    logger.info("=" * 50)
    logger.info("INTEGRATION TEST SUITE PASSED")
    logger.info("All user stories (US1, US2, US3) executed and verified.")
    logger.info("=" * 50)
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)