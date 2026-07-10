"""
Task T029: Generate data/processed/user_track_pairs.parquet with checksum and update state.yaml.

This script orchestrates the final steps of User Story 2:
1. Loads the aggregated User-Track pair data (produced by T026).
2. Verifies the match rate (ensuring T036 logic was applied).
3. Saves the final parquet file to data/processed/user_track_pairs.parquet.
4. Registers the file in state.yaml with a SHA-256 checksum.
"""
import os
import logging
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq

from config import get_project_root, get_config_dict
from state_manager import load_state, save_state, register_file
from aggregation import aggregate_to_user_track, filter_zero_variance, enforce_match_rate

logger = logging.getLogger(__name__)

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    project_root = get_project_root()
    config = get_config_dict()

    # Define paths
    # We assume the intermediate aggregated data exists from T026/T027 execution
    # Typically, T026 produces a temporary dataframe or file. 
    # For this pipeline, we assume the previous step (T027) left a processed file 
    # or we re-run the aggregation logic if inputs are available.
    # However, per the task flow, we expect the data to be ready in memory or a temp file 
    # from the previous step. 
    # To make this script runnable independently as a pipeline stage, we will:
    # 1. Check for the existence of the intermediate file from T027 (if it was saved).
    # 2. If not, we assume the user has run the ingestion/matching steps and we need to 
    #    reconstruct the state or load from a standard intermediate location.
    #
    # Standard Pipeline Assumption: 
    # T026/T027 logic is usually part of a larger run. 
    # Since T029 is the "Generate" task, it implies the data is ready to be finalized.
    # We will look for 'data/processed/aggregated_user_track_temp.parquet' or similar.
    # If that doesn't exist, we might need to re-run the aggregation from the raw matched cues.
    #
    # Let's assume the previous step (T027) saved a file named 'data/processed/aggregated_temp.parquet'
    # or we need to load the raw matched cues and re-aggregate.
    #
    # Given the constraints of a single script task:
    # We will attempt to load the 'matched_cues.parquet' (output of T023/T024) 
    # and the 'exposure_data.parquet' (output of T018) and re-run the aggregation 
    # to ensure T029 is self-contained for the final generation step.
    
    # Paths for inputs (Outputs of previous tasks)
    matched_cues_path = project_root / "data" / "processed" / "matched_cues.parquet"
    exposure_data_path = project_root / "data" / "processed" / "ingested_cohort.parquet"
    
    # Output path
    output_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    
    # Ensure directories exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not matched_cues_path.exists():
        logger.error(f"Input file not found: {matched_cues_path}")
        logger.error("Please ensure T023/T024 (Cue Matching) has been completed successfully.")
        return 1

    if not exposure_data_path.exists():
        logger.error(f"Input file not found: {exposure_data_path}")
        logger.error("Please ensure T018 (Ingestion) has been completed successfully.")
        return 1

    logger.info(f"Loading matched cues from {matched_cues_path}")
    cues_df = pd.read_parquet(matched_cues_path)

    logger.info(f"Loading exposure data from {exposure_data_path}")
    exposure_df = pd.read_parquet(exposure_data_path)

    # Step 1: Join Exposure Data (T025 logic)
    # We join the exposure data to the cues based on track_id
    # The exposure data should be at the Track level, cues at User-Track level eventually
    joined_df = join_exposure_data(cues_df, exposure_df)

    if joined_df is None or joined_df.empty:
        logger.error("Joining exposure data resulted in an empty dataframe.")
        return 1

    # Step 2: Aggregate to User-Track Pair (T026 logic)
    # This calculates mean_vividness, mean_valence per user_id + track_id
    aggregated_df = aggregate_to_user_track(joined_df)

    if aggregated_df is None or aggregated_df.empty:
        logger.error("Aggregation resulted in an empty dataframe.")
        return 1

    # Step 3: Filter Zero Variance (T027 logic)
    # Remove tracks with no memory cues or no variance in the target variables
    final_df = filter_zero_variance(aggregated_df)

    if final_df is None or final_df.empty:
        logger.warning("Filtering zero variance resulted in an empty dataframe. Proceeding with warning.")

    # Step 4: Enforce Match Rate (T036 logic)
    # This checks if the overall match rate meets the threshold (SC-004)
    # It logs a warning if < 80% but does not stop.
    match_rate_ok = enforce_match_rate(cues_df, final_df)
    
    # Step 5: Save to Parquet
    logger.info(f"Saving final user_track_pairs to {output_path}")
    final_df.to_parquet(output_path, index=False)

    # Step 6: Register in State Manager (T009/T029 logic)
    state = load_state(project_root)
    register_file(state, output_path)
    save_state(state, project_root)

    logger.info("Task T029 completed successfully.")
    logger.info(f"Output file: {output_path}")
    logger.info(f"Rows written: {len(final_df)}")
    logger.info(f"Match rate check passed/warned: {match_rate_ok}")

    return 0

if __name__ == "__main__":
    exit(main())
