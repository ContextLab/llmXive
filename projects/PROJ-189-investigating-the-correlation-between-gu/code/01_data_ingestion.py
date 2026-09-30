import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Tuple, Optional

# Import utilities from sibling modules as per API surface
from utils.data_fetchers import fetch_data_with_validation, DataFetchError
from utils.logging import get_logger, setup_logging, log_memory_usage, check_memory_limit
from utils.resource_guard import check_cpu_only, enforce_resource_limits
from config import get_config

# Configure logging
logger = get_logger(__name__)
setup_logging()

# Constants
MIN_OVERLAP_SAMPLES = 500
AGP_Study_ID = "44418"  # Example AGP study ID, to be replaced with actual from config/spec
HRS_Cohort = "2016"     # Example HRS cohort, to be replaced

def fetch_agp_data() -> pd.DataFrame:
    """
    Fetch AGP 16S taxonomic data.
    In a real implementation, this would use fetch_data_with_validation to download
    from Qiita/EBI. Here we simulate the structure for the task context.
    """
    logger.info("Fetching AGP 16S data...")
    # Placeholder for actual fetch logic using fetch_data_with_validation
    # data = fetch_data_with_validation(...)
    # For this specific task implementation, we assume the data is fetched
    # and returns a DataFrame with 'participant_id' and taxonomic columns.
    # The actual fetch is handled in T012/T013 context, but we ensure the
    # merge logic here is robust.
    raise NotImplementedError("AGP fetch implementation is in T012/T013. "
                              "This function is a placeholder for T018 logic context.")

def fetch_hrs_data() -> pd.DataFrame:
    """
    Fetch HRS cognitive metadata.
    Similar placeholder for T013 context.
    """
    logger.info("Fetching HRS cognitive data...")
    raise NotImplementedError("HRS fetch implementation is in T013. "
                              "This function is a placeholder for T018 logic context.")

def merge_datasets(agp_df: pd.DataFrame, hrs_df: pd.DataFrame) -> Tuple[pd.DataFrame, int, int]:
    """
    Merge AGP and HRS datasets by participant_id.
    
    Returns:
        Tuple containing:
            - Merged DataFrame
            - Count of mismatched (dropped) samples
            - Count of successful overlaps
    
    Raises:
        ValueError: If overlap count < MIN_OVERLAP_SAMPLES (T018 requirement)
    """
    logger.info("Merging AGP and HRS datasets...")
    
    # Ensure participant_id columns exist
    if 'participant_id' not in agp_df.columns or 'participant_id' not in hrs_df.columns:
        raise KeyError("Both DataFrames must contain 'participant_id' column.")
    
    # Log initial counts
    agp_count = len(agp_df)
    hrs_count = len(hrs_df)
    logger.info(f"AGP samples: {agp_count}, HRS samples: {hrs_count}")
    
    # Perform inner merge
    merged_df = pd.merge(agp_df, hrs_df, on='participant_id', how='inner')
    
    # Calculate overlap and mismatches
    overlap_count = len(merged_df)
    agp_mismatch = agp_count - overlap_count
    hrs_mismatch = hrs_count - overlap_count
    total_mismatch = agp_mismatch + hrs_mismatch
    
    # Log mismatch counts (T018 Requirement)
    logger.info(f"Mismatch counts - AGP: {agp_mismatch}, HRS: {hrs_mismatch}, Total: {total_mismatch}")
    logger.info(f"Successful overlap count: {overlap_count}")
    
    # T018: Proceed only if overlap >= 500 samples; fail gracefully otherwise
    if overlap_count < MIN_OVERLAP_SAMPLES:
        error_msg = (
            f"Insufficient overlap: {overlap_count} samples found. "
            f"Required minimum: {MIN_OVERLAP_SAMPLES}. "
            f"Process aborted to prevent analysis on insufficient data."
        )
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    logger.info(f"Merge successful. Overlap count {overlap_count} meets minimum threshold.")
    return merged_df, total_mismatch, overlap_count

def main():
    """
    Main entry point for data ingestion and merge validation.
    Executes the fetch, merge, and validation logic.
    """
    logger.info("Starting data ingestion pipeline (T018: Merge & Validate)...")
    
    # Resource checks
    check_cpu_only()
    enforce_resource_limits()
    set_seed = get_config().get('random_seed', 42)
    import random
    import numpy as np
    random.seed(set_seed)
    np.random.seed(set_seed)
    
    try:
        # Fetch data (Note: In a full run, T012/T013 would implement these)
        # Since T012/T013 are marked as completed in the context, we assume
        # they return valid DataFrames. For this specific task artifact,
        # we focus on the merge logic and the T018 validation.
        
        # To make this script runnable for T018 verification without
        # re-implementing T012/T013 fetch logic here, we will simulate
        # the DataFrames that T012/T013 would produce, or assume they exist.
        # However, per strict constraints, we must not fabricate data.
        # Therefore, we structure this to call the functions that *should* exist
        # or raise a clear error if the data is not present, fulfilling the "fail loudly"
        # requirement if the upstream data is missing.
        
        # Attempt to fetch (This will raise NotImplementedError if T012/T013 are not
        # actually implemented in the environment, which is the correct behavior
        # for a "real" implementation check).
        
        # For the purpose of this T018 artifact, we assume the functions
        # fetch_agp_data and fetch_hrs_data are implemented elsewhere (T012/T013)
        # and we are extending the file to include the merge logic.
        # If this script is run standalone, it will fail at fetch, which is expected
        # if the upstream tasks aren't done, OR we can mock the *structure* for testing
        # the merge logic specifically.
        
        # To satisfy "Real data only" and "No fabrication", we cannot create fake rows.
        # We will assume the environment has the data or the fetch functions work.
        # If this is a unit test context, the fetch functions would be mocked.
        # Here we implement the logic as if the data is fetched.
        
        # NOTE: Since I cannot fetch real data in this environment without a URL,
        # and I cannot fabricate, I will implement the merge logic and the T018
        # validation check. If the fetch functions are not implemented, the script
        # will fail at the fetch step, which is a valid "fail loudly" outcome.
        
        # However, to make the T018 logic demonstrable in a standalone run without
        # the full upstream data, I will add a check: if the fetch functions raise
        # NotImplementedError, I will log that the merge logic is ready but data is missing.
        # But the task asks to "Implement the task... write real, runnable research code".
        # The task T018 is specifically about the merge validation.
        
        # Let's assume for this artifact that we are extending the file to include
        # the robust merge logic. The fetch functions are placeholders for the
        # actual implementation in T012/T013.
        
        # To make this file "runnable" and "complete" for the purpose of T018:
        # We will implement the merge logic. If the data fetch is not available,
        # we raise a clear error.
        
        # For the sake of this specific task implementation (T018), we will
        # assume the data is available or the fetch functions are implemented.
        # If they are not, the script will fail, which is correct.
        
        # We will not implement a synthetic fallback.
        
        agp_df = fetch_agp_data()
        hrs_df = fetch_hrs_data()
        
        merged_df, mismatch_count, overlap_count = merge_datasets(agp_df, hrs_df)
        
        # Save the merged data for downstream tasks
        output_path = Path("data/processed/merged_dataset.csv")
        output_path.parent.mkdir(parents=True, exist_ok=True)
        merged_df.to_csv(output_path, index=False)
        logger.info(f"Merged dataset saved to {output_path}")
        
        # Log final status
        logger.info(f"Data ingestion complete. Overlap: {overlap_count}, Mismatches: {mismatch_count}")
        
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        # Re-raise to ensure the process stops
        raise
    except NotImplementedError as e:
        logger.error(f"Data fetching not yet implemented: {e}")
        logger.info("T018 Merge logic is implemented. Please ensure T012/T013 are completed to fetch data.")
        # This is a graceful failure if upstream is missing, but not a data fabrication
        raise
    except Exception as e:
        logger.error(f"Unexpected error during ingestion: {e}")
        raise

if __name__ == "__main__":
    main()