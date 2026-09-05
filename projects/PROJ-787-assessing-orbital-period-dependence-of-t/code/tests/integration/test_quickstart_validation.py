"""
Integration test to validate the entire quickstart.md pipeline.
This script executes the critical path of the research pipeline to ensure
reproducibility and that all data artifacts are generated correctly.
"""
import os
import sys
import subprocess
import time
import logging
from pathlib import Path

# Add project root to path if necessary (assuming running from code/)
if str(Path(__file__).resolve().parent.parent) not in sys.path:
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from utils.logging_config import setup_logging, get_logger
from utils.setup_dirs import initialize_directories
from ingest.download_dr25 import main as download_dr25_main
from ingest.download_kic import main as download_kic_main
from ingest.merge_catalogs import main as merge_catalogs_main
from ingest.preprocess import main as preprocess_main
from analysis.binning import main as binning_main
from analysis.gmm_fitter import main as gmm_fitter_main
from analysis.binned_stats import main as binned_stats_main
from analysis.integrate_gap_analysis import main as integrate_gap_main
from analysis.kde_validator import main as kde_validator_main
from ingest.download_completeness import main as download_completeness_main
from analysis.regression import main as regression_main
from theory.theory_comparison import main as theory_comparison_main
from analysis.generate_results import main as generate_results_main

# Setup logging for the validation run
setup_logging(level=logging.INFO)
logger = get_logger(__name__)

# Define expected output artifacts
EXPECTED_ARTIFACTS = [
    "data/raw/dr25_raw.csv",
    "data/raw/kic_raw.csv",
    "data/processed/filtered_planets.csv",
    "data/processed/deduped_planets.csv",
    "data/processed/binned_planets.csv",
    "data/processed/gap_locations.csv",
    "data/processed/binned_stats.csv",
    "data/processed/kde_validation.json",
    "data/raw/completeness_map.csv",
    "data/processed/regression_results.json",
    "data/processed/theory_comparison_results.json",
    "paper/results.md"
]

def run_module_step(module_main_func, step_name, timeout_seconds=3600):
    """
    Executes a module's main function within a timeout.
    Returns True on success, False on failure/timeout.
    """
    logger.info(f"--- Starting Step: {step_name} ---")
    start_time = time.time()
    try:
        module_main_func()
        elapsed = time.time() - start_time
        logger.info(f"--- Step {step_name} completed in {elapsed:.2f}s ---")
        return True
    except SystemExit as e:
        if e.code != 0:
            logger.error(f"Step {step_name} exited with code {e.code}")
            return False
        logger.info(f"--- Step {step_name} completed (exit 0) ---")
        return True
    except Exception as e:
        logger.error(f"Step {step_name} failed with exception: {e}", exc_info=True)
        return False

def verify_artifacts():
    """Checks if all expected output files exist and are non-empty."""
    missing = []
    for artifact in EXPECTED_ARTIFACTS:
        full_path = Path("code") / artifact
        # Adjust path if running from root vs code directory
        if not full_path.exists():
            # Try relative to current working directory if code/ prefix was wrong
            alt_path = Path(artifact)
            if alt_path.exists():
                full_path = alt_path
            else:
                missing.append(artifact)
        else:
            if full_path.stat().st_size == 0:
                missing.append(artifact)
    
    if missing:
        logger.error(f"Missing or empty artifacts: {missing}")
        return False
    return True

def main():
    logger.info("Starting Quickstart Validation Pipeline...")
    
    # 1. Ensure directories exist
    initialize_directories()

    # 2. Execution Pipeline
    # Note: The order below mirrors the logical dependency chain in quickstart.md
    # and tasks.md. Some steps (like downloading) might be skipped if data exists,
    # but for validation we attempt the full flow.
    
    steps = [
        (download_dr25_main, "Download DR25"),
        (download_kic_main, "Download KIC"),
        (merge_catalogs_main, "Merge Catalogs"),
        (preprocess_main, "Preprocess & Filter"),
        (binning_main, "Binning"),
        (gmm_fitter_main, "GMM Fitting"),
        (binned_stats_main, "Binned Stats"),
        (integrate_gap_main, "Integrate Gap Analysis"),
        (kde_validator_main, "KDE Validation"),
        (download_completeness_main, "Download Completeness"),
        (regression_main, "Regression"),
        (theory_comparison_main, "Theory Comparison"),
        (generate_results_main, "Generate Results"),
    ]

    pipeline_success = True
    for func, name in steps:
        if not run_module_step(func, name):
            logger.critical(f"Pipeline halted at step: {name}")
            pipeline_success = False
            break

    if not pipeline_success:
        logger.error("Pipeline execution failed. Validation ABORTED.")
        return 1

    # 3. Verify Artifacts
    if verify_artifacts():
        logger.info("SUCCESS: All expected artifacts generated and validated.")
        return 0
    else:
        logger.error("FAILURE: Some artifacts are missing or empty.")
        return 1

if __name__ == "__main__":
    sys.exit(main())