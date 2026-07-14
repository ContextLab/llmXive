"""
Task T016: Save the validated synthetic cohort to data/results/synthetic_cohort.csv.

This script acts as the final step for User Story 1. It loads the synthetic cohort
constructed by `code/data/cohort.py`, ensures the output directory exists, and
writes the data to `data/results/synthetic_cohort.csv` ONLY if the validation
checks (performed by `code/analysis/validation.py`) are satisfied.

It relies on the `main` function in `code/analysis/validation.py` to perform
the validation logic. If validation fails, it logs the failure and exits
without writing the file (or writes a status file, but per task description,
it saves the cohort only after successful validation).

Note: This script assumes T014 has already produced the intermediate synthetic
cohort data (likely in memory or a temporary state) and T015 has validated it.
To make this robust and runnable, we will re-load the pre-processed data,
re-run the cohort construction (T014 logic) and validation (T015 logic) in
sequence, and then save the result. This ensures the file is generated
correctly based on the current state of the pipeline.

Alternatively, if the cohort is already saved in a temporary location by T014,
we would load that. However, the task description implies a flow where T015
validates the result of T014. Since T014 outputs to `data/results/synthetic_cohort.csv`
(see T014 description: "Output data/results/synthetic_cohort.csv"), and T015
validates it, T016 is essentially a "finalization" step.

Re-reading T014: "Output data/results/synthetic_cohort.csv".
Re-reading T015: "Validate the synthetic cohort...".
Re-reading T016: "Save the validated synthetic cohort... only after successful T015".

This implies T014 might write a *candidate* file, T015 checks it, and T016
writes the *final* file if T015 passes. Or, T014 produces an in-memory object,
T015 validates it, and T016 saves it.

Given the API surface for `code/data/cohort.py` includes `construct_synthetic_cohort`
and `main`, and `code/analysis/validation.py` includes `validate_synthetic_cohort`
and `main`, we will orchestrate the full flow here to ensure the file is
written correctly.

Steps:
1. Load preprocessed data (from T013).
2. Construct synthetic cohort (T014 logic).
3. Validate the cohort (T015 logic).
4. If valid, save to `data/results/synthetic_cohort.csv`.

We will import the necessary functions from the existing modules.
"""

import os
import logging
import sys
from pathlib import Path

# Add project root to path to allow imports
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from data.cohort import construct_synthetic_cohort, load_preprocessed_data
from analysis.validation import validate_synthetic_cohort, main as validation_main
from data.preprocessing import main as preprocessing_main

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("T016_SaveCohort")

def main():
    logger.info("Starting T016: Save validated synthetic cohort.")
    
    # Define paths
    data_dir = project_root / "data"
    results_dir = data_dir / "results"
    output_path = results_dir / "synthetic_cohort.csv"
    
    # Ensure output directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Step 1: Ensure preprocessing is done (T013)
    # We assume the preprocessing output is available or can be regenerated.
    # For robustness, we will call the preprocessing main if needed,
    # but typically this is orchestrated by main_pipeline.py.
    # Here, we assume the preprocessed data file exists or we run the logic.
    # Let's assume the preprocessed data is in `data/preprocessed_data.csv`
    # based on typical pipeline flows, or we rely on the `load_preprocessed_data`
    # function to find it.
    
    logger.info("Loading preprocessed data...")
    try:
        preprocessed_df = load_preprocessed_data()
        if preprocessed_df is None or preprocessed_df.empty:
            logger.error("Preprocessed data is empty or not found. Aborting T016.")
            return False
    except Exception as e:
        logger.error(f"Failed to load preprocessed data: {e}")
        return False
    
    # Step 2: Construct synthetic cohort (T014 logic)
    logger.info("Constructing synthetic cohort...")
    try:
        synthetic_cohort_df = construct_synthetic_cohort(preprocessed_df)
        if synthetic_cohort_df is None or synthetic_cohort_df.empty:
            logger.error("Synthetic cohort construction failed or returned empty. Aborting T016.")
            return False
    except Exception as e:
        logger.error(f"Failed to construct synthetic cohort: {e}")
        return False
    
    # Step 3: Validate the synthetic cohort (T015 logic)
    logger.info("Validating synthetic cohort...")
    validation_passed, validation_details = validate_synthetic_cohort(synthetic_cohort_df)
    
    if not validation_passed:
        logger.warning("Synthetic cohort validation failed. Details: %s", validation_details)
        logger.info("Not saving the cohort file as validation failed.")
        return False
    
    logger.info("Validation passed. Saving synthetic cohort to %s", output_path)
    
    # Step 4: Save the validated cohort
    try:
        synthetic_cohort_df.to_csv(output_path, index=False)
        logger.info("Successfully saved synthetic cohort to %s", output_path)
        return True
    except Exception as e:
        logger.error(f"Failed to save synthetic cohort: {e}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
