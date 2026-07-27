import os
import logging
import sys
from pathlib import Path
from typing import Optional

# Add project root to path to allow relative imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from data.cohort import construct_synthetic_cohort, load_preprocessed_data
from analysis.validation import validate_synthetic_cohort, main as validation_main
from logger import get_logger

logger = get_logger(__name__)

def save_validated_cohort(output_path: Optional[str] = None) -> bool:
    """
    Constructs the synthetic cohort, validates it, and saves it to disk
    ONLY if validation passes (SC-001 compliance).

    Returns:
        bool: True if cohort was successfully validated and saved, False otherwise.
    """
    if output_path is None:
        output_path = str(project_root / "data" / "results" / "synthetic_cohort.csv")
    
    output_path_obj = Path(output_path)
    output_dir = output_path_obj.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    try:
        # Load preprocessed data
        logger.info("Loading preprocessed data for cohort construction...")
        df_preprocessed = load_preprocessed_data()
        
        if df_preprocessed is None or df_preprocessed.empty:
            logger.error("Preprocessed data is empty or missing. Cannot construct cohort.")
            return False

        # Construct synthetic cohort (matching + weighting)
        logger.info("Constructing synthetic cohort via propensity score matching and weighting...")
        df_cohort = construct_synthetic_cohort(df_preprocessed)

        if df_cohort is None or df_cohort.empty:
            logger.error("Cohort construction resulted in an empty dataframe.")
            return False

        # Validate the cohort (SMD, Variance, VIF checks)
        logger.info("Validating synthetic cohort against balance criteria (SC-001)...")
        is_valid, validation_report = validate_synthetic_cohort(df_cohort)

        if not is_valid:
            logger.warning("Cohort validation failed. Criteria not met. Aborting save.")
            logger.warning(f"Validation report: {validation_report}")
            return False

        # Save to CSV
        logger.info(f"Cohort validation passed. Saving to {output_path}...")
        df_cohort.to_csv(output_path, index=False)
        logger.info("Synthetic cohort successfully saved.")
        return True

    except Exception as e:
        logger.exception(f"Error during cohort construction, validation, or saving: {e}")
        return False

def main():
    """Entry point for the save_cohort task."""
    logger.info("Starting T016: Save validated synthetic cohort.")
    success = save_validated_cohort()
    
    if success:
        logger.info("T016 completed successfully.")
        return 0
    else:
        logger.error("T016 failed: Cohort not saved due to validation failure or error.")
        return 1

if __name__ == "__main__":
    sys.exit(main())