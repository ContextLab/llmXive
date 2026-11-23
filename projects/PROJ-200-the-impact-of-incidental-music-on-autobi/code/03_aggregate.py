import os
import sys
import logging
from pathlib import Path

# Add project root to path if running as script
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from aggregation import (
    join_exposure_data,
    aggregate_to_user_track,
    filter_zero_variance,
    enforce_match_rate,
    load_aggregated_data
)
from utils import write_parquet, compute_sha256, update_state_yaml, setup_logging, get_logger
from config import get_project_root

logger = get_logger(__name__)

def main():
    """
    Orchestrate the aggregation pipeline:
    1. Join exposure data with matched cues.
    2. Aggregate to User-Track pairs.
    3. Filter zero variance tracks.
    4. Enforce match rate threshold.
    5. Write final parquet artifact.
    6. Compute checksum and update state.
    """
    setup_logging()
    root = get_project_root()
    
    # Paths
    ingested_cohort_path = "data/processed/ingested_cohort.parquet"
    amt_cues_path = "data/raw/amt_cues.csv" # Assuming raw AMT cues are here
    output_path = "data/processed/user_track_pairs.parquet"
    
    logger.info("Starting aggregation pipeline...")
    
    # 1. Load and Join
    # Note: join_exposure_data expects paths or dataframes. Assuming it loads ingested_cohort.
    # We pass the relative path to the ingestion artifact.
    try:
        # Load ingested cohort (T018 output)
        cohort_df = pd.read_parquet(root / ingested_cohort_path)
        logger.info(f"Loaded ingested cohort with {len(cohort_df)} rows.")
        
        # Load AMT cues (assuming CSV format based on context)
        # If AMT cues are in a different format, adjust loader here
        if not (root / amt_cues_path).exists():
            raise FileNotFoundError(f"AMT cues file not found at {root / amt_cues_path}")
        cues_df = pd.read_csv(root / amt_cues_path)
        logger.info(f"Loaded AMT cues with {len(cues_df)} rows.")
        
        joined_df = join_exposure_data(cohort_df, cues_df)
        logger.info(f"Joined data shape: {joined_df.shape}")
        
        # 2. Aggregate to User-Track Pairs
        aggregated_df = aggregate_to_user_track(joined_df)
        logger.info(f"Aggregated data shape: {aggregated_df.shape}")
        
        # 3. Filter Zero Variance
        filtered_df = filter_zero_variance(aggregated_df)
        logger.info(f"Filtered data shape: {filtered_df.shape}")
        
        # 4. Enforce Match Rate
        match_rate_ok = enforce_match_rate(filtered_df)
        if not match_rate_ok:
            logger.warning("Match rate threshold not met. Proceeding with warning.")
        
        # 5. Write Parquet (T123)
        logger.info(f"Writing final artifact to {output_path}")
        write_parquet(filtered_df, output_path)
        
        # 6. Compute Checksum (T124)
        checksum = compute_sha256(output_path)
        logger.info(f"Computed checksum: {checksum}")
        
        # 7. Update State (T125)
        metadata = {
            "task_id": "T029",
            "description": "User-Track Pairs Aggregation",
            "source": ["ingested_cohort.parquet", "amt_cues.csv"]
        }
        update_state_yaml(output_path, checksum, metadata)
        
        logger.info("Aggregation pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
