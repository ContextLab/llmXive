"""
Main entry point for the Brain Dynamics and Creativity research pipeline.

This script orchestrates the full analysis workflow:
1. Validates data availability (CAQ field presence).
2. Loads and filters subject data.
3. Preprocesses fMRI data.
4. Computes connectivity and dynamics metrics.
5. Performs statistical analysis.
6. Generates visualizations.
"""
import sys
import logging
import json
from pathlib import Path

# Project utilities
from llmxive_toolkit import paths, get_logger

from config import get_config
from errors import DataMissingCreativityError
from data.loader import validate_caq_availability
from utils.logging import log_exclusion

log = get_logger(__name__)

def run_validation() -> None:
    """
    Perform CAQ availability validation.
    Exits the program with error code 1 if validation fails.
    """
    # Locate the behavioral JSON file in the raw data directory.
    # The exact filename may vary; we look for a file named
    # ``behavioral.json`` (or ``behav.json``) inside ``data/raw``.
    behavioral_candidates = [
        paths.data("raw", "behavioral.json"),
        paths.data("raw", "behav.json"),
    ]

    behavioral_path = None
    for candidate in behavioral_candidates:
        if candidate.is_file():
            behavioral_path = candidate
            break

    if behavioral_path is None:
        error_msg = "CRITICAL ERROR: Behavioral JSON file not found in raw data."
        print(error_msg)
        logging.error(error_msg)
        log_exclusion(reason="FILE_NOT_FOUND", subject_id="SYSTEM")
        sys.exit(1)

    # Load the behavioral JSON content
    try:
        with open(behavioral_path, "r") as f:
            behavioral_data = json.load(f)
    except Exception as e:
        error_msg = f"CRITICAL ERROR: Failed to read behavioral JSON – {e}"
        print(error_msg)
        logging.error(error_msg)
        log_exclusion(reason="FILE_READ_ERROR", subject_id="SYSTEM")
        sys.exit(1)

    logging.info(f"Validating CAQ availability in {behavioral_path}...")

    try:
        validate_caq_availability(behavioral_data)
        logging.info("CAQ validation successful.")
    except DataMissingCreativityError as e:
        # Log the missing field name and exit with the required code.
        error_msg = f"CRITICAL ERROR: {e}"
        print(error_msg)
        logging.error(error_msg)
        # Use the shared exclusion logger to record the failure.
        log_exclusion(reason="DATA_MISSING_CREATIVITY", subject_id="SYSTEM")
        sys.exit(1)
    except FileNotFoundError as e:
        error_msg = f"CRITICAL ERROR: Required data files not found. {e}"
        print(error_msg)
        logging.error(error_msg)
        log_exclusion(reason="FILE_NOT_FOUND", subject_id="SYSTEM")
        sys.exit(1)

def main():
    """
    Execute the research pipeline.
    """
    # Ensure the data directory exists so that the log file can be created.
    data_dir = Path(__file__).parents[2] / "data"
    data_dir.mkdir(parents=True, exist_ok=True)

    # Setup basic logging configuration for the pipeline
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(data_dir / "pipeline.log")
        ]
    )

    print("Starting Brain Dynamics and Creativity Pipeline...")
    logging.info("Pipeline execution started.")

    # 1. Pre‑condition: Validate CAQ availability before any data loading
    run_validation()

    # 2. Load and filter subjects
    # (Implementation of subsequent steps would follow here)
    print("Proceeding to data loading and processing...")
    logging.info("Proceeding to data loading and processing...")

    # Placeholder for future pipeline steps
    # fetch_hcp_data(...)
    # preprocess_fmri(...)
    # compute_connectivity(...)
    # fit_regression(...)
    # generate_plots(...)

    print("Pipeline execution complete.")
    logging.info("Pipeline execution completed successfully.")

if __name__ == "__main__":
    main()
