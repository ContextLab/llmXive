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
from pathlib import Path

# Add project root to path for imports if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_config
from errors import DataMissingCreativityError
from data.loader import validate_caq_availability
from utils.logging import log_exclusion


def main():
    """
    Execute the research pipeline.
    """
    # Setup basic logging configuration for the pipeline
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(project_root / "data" / "pipeline.log")
        ]
    )
    
    print("Starting Brain Dynamics and Creativity Pipeline...")
    logging.info("Pipeline execution started.")

    # 1. Pre-condition: Validate CAQ availability before any data loading
    config = get_config()
    manifest_path = config.DATA_PATH / "manifest.json"
    behavioral_path = config.DATA_PATH / "behavioral_scores.json"

    print(f"Validating CAQ availability in {manifest_path}...")
    logging.info(f"Validating CAQ availability in {manifest_path}...")
    
    try:
        validate_caq_availability(str(manifest_path), str(behavioral_path))
        print("CAQ validation successful.")
        logging.info("CAQ validation successful.")
    except DataMissingCreativityError as e:
        error_msg = f"CRITICAL ERROR: {e}"
        print(error_msg)
        logging.error(error_msg)
        
        # Log the specific error code as required by T036
        # Using a subject_id of 'SYSTEM' as this is a system-level validation failure
        log_exclusion(reason="DATA_MISSING_CREATIVITY", subject_id="SYSTEM")
        
        sys.exit(1)
    except FileNotFoundError as e:
        error_msg = f"CRITICAL ERROR: Required data files not found. {e}"
        print(error_msg)
        logging.error(error_msg)
        
        # Log the missing file error
        log_exclusion(reason="FILE_NOT_FOUND", subject_id="SYSTEM")
        
        sys.exit(1)

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