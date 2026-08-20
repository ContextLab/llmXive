"""
Physics Pipeline Runner for T025.

Reads the filtered dataset from User Story 1, applies physics models
(T021-T023), applies unphysical filters (T024a-T024b), and writes
the clean result to data/processed/derived_physics.csv.
"""
import logging
import sys
from pathlib import Path

import pandas as pd
import numpy as np

from physics import (
    calculate_quiescent_xuv,
    calculate_cumulative_flux,
    calculate_retention_fraction,
    calculate_unphysical_flag,
    apply_unphysical_filter,
    validate_derived_columns,
    run_physics_pipeline
)
from utils import log_api_provenance, calculate_checksum
import config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Execute the physics pipeline:
    1. Load merged_filtered.csv
    2. Apply physics calculations (Quiescent XUV, Cumulative Flux, Retention)
    3. Flag and filter unphysical records
    4. Validate derived columns
    5. Save to derived_physics.csv
    """
    input_path = Path("data/processed/merged_filtered.csv")
    output_path = Path("data/processed/derived_physics.csv")
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T017 (save_processed_data) has been run successfully.")
        sys.exit(1)

    logger.info(f"Loading data from {input_path}")
    try:
        df = pd.read_csv(input_path)
    except Exception as e:
        logger.error(f"Failed to load CSV: {e}")
        sys.exit(1)

    logger.info(f"Loaded {len(df)} records. Starting physics calculations...")

    # Apply the full physics pipeline which includes T021-T024b logic
    # The run_physics_pipeline function is expected to orchestrate the calls
    # to calculate_quiescent_xuv, calculate_cumulative_flux, calculate_retention_fraction,
    # calculate_unphysical_flag, and apply_unphysical_filter.
    try:
        df_processed = run_physics_pipeline(df)
    except Exception as e:
        logger.error(f"Physics pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # Validate derived columns to ensure no NaNs where expected (T026 dependency)
    # This function is defined in physics.py but we call it here to be explicit about the step
    is_valid, errors = validate_derived_columns(df_processed)
    if not is_valid:
        logger.warning(f"Validation warnings: {errors}")
        # We proceed but log the warnings as per T026 requirements (validation logic exists)

    # Save the result
    logger.info(f"Saving {len(df_processed)} records to {output_path}")
    df_processed.to_csv(output_path, index=False)
    
    # Generate checksum for provenance
    checksum = calculate_checksum(output_path)
    log_api_provenance(
        operation="physics_pipeline_run",
        input_file=str(input_path),
        output_file=str(output_path),
        checksum=checksum,
        record_count=len(df_processed)
    )
    
    logger.info(f"Pipeline complete. Checksum: {checksum}")

if __name__ == "__main__":
    main()
