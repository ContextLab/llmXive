"""
T027a: MMSE Robustness Data Prep

Reads primary and robustness datasets, checks flags for MMSE availability and simulation mode,
and logs appropriate skip conditions if necessary.
"""
import os
import json
import logging
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Define paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parents[2]
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
RAW_DIR = PROJECT_ROOT / "data" / "raw"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"

# Ensure results directory exists
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

# File paths
PRIMARY_DATASET_PATH = PROCESSED_DIR / "cleaned_dataset.csv"
ROBUSTNESS_DATASET_PATH = PROCESSED_DIR / "cleaned_dataset_no_mmse.csv"
MMSE_FLAG_PATH = PROCESSED_DIR / "mmse_flag.json"
METADATA_PATH = RAW_DIR / "metadata.json"
SKIP_LOG_PATH = RESULTS_DIR / "robustness_skip_log.json"

def load_json(path: Path) -> dict:
    """Load a JSON file."""
    if not path.exists():
        raise FileNotFoundError(f"Required file not found: {path}")
    with open(path, 'r') as f:
        return json.load(f)

def check_skip_conditions() -> bool:
    """
    Checks if the robustness analysis should be skipped.
    Returns True if skipped, False if analysis should proceed.
    """
    should_skip = False
    skip_reasons = []

    # Check 1: MMSE Availability
    try:
        mmse_flag_data = load_json(MMSE_FLAG_PATH)
        has_mmse = mmse_flag_data.get("has_mmse", False)
        
        if not has_mmse:
            logger.warning("WARN_MMSE_MISSING: MMSE flag indicates no MMSE data available. Skipping robustness comparison.")
            skip_reasons.append("WARN_MMSE_MISSING")
            should_skip = True
    except FileNotFoundError as e:
        logger.warning(f"WARN_MMSE_MISSING: {e}. Skipping robustness comparison.")
        skip_reasons.append("WARN_MMSE_MISSING")
        should_skip = True

    # Check 2: Simulation Mode
    if not should_skip:
        try:
            metadata = load_json(METADATA_PATH)
            is_simulation = metadata.get("simulation_mode", False)
            
            if is_simulation:
                logger.info("INFO_SIMULATION_SKIPPED: Simulation mode detected. Skipping robustness check.")
                skip_reasons.append("INFO_SIMULATION_SKIPPED")
                should_skip = True
        except FileNotFoundError as e:
            # If metadata is missing, we might not know simulation mode, 
            # but if we reached here, MMSE was present. 
            # We proceed unless we explicitly know it's simulation.
            logger.warning(f"WARNING: Metadata file not found ({e}). Proceeding with robustness check assuming real data.")
    
    return should_skip, skip_reasons

def main():
    """Main entry point for T027a."""
    logger.info("Starting T027a: MMSE Robustness Data Prep")

    # Verify primary files exist before checking logic
    if not PRIMARY_DATASET_PATH.exists():
        logger.error(f"Primary dataset not found: {PRIMARY_DATASET_PATH}")
        raise FileNotFoundError(f"Primary dataset not found: {PRIMARY_DATASET_PATH}")
    
    if not ROBUSTNESS_DATASET_PATH.exists():
        logger.error(f"Robustness dataset not found: {ROBUSTNESS_DATASET_PATH}")
        raise FileNotFoundError(f"Robustness dataset not found: {ROBUSTNESS_DATASET_PATH}")

    should_skip, reasons = check_skip_conditions()

    skip_log = {
        "task_id": "T027a",
        "skipped": should_skip,
        "reasons": reasons,
        "primary_dataset_path": str(PRIMARY_DATASET_PATH),
        "robustness_dataset_path": str(ROBUSTNESS_DATASET_PATH)
    }

    # Write skip log to results directory
    with open(SKIP_LOG_PATH, 'w') as f:
        json.dump(skip_log, f, indent=2)

    if should_skip:
        logger.info(f"Robustness analysis skipped. Log written to {SKIP_LOG_PATH}")
    else:
        logger.info("Preconditions met. Proceeding to T027b (Robustness Analysis).")

    return skip_log

if __name__ == "__main__":
    main()