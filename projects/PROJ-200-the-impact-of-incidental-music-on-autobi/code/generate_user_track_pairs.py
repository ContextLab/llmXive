"""
Generate the final user_track_pairs.parquet dataset.

This script orchestrates the loading of aggregated data from the cue matching
and exposure calculation stages, saves it as a Parquet file with a checksum,
and updates the state.yaml file for artifact tracking.

It depends on T026 (aggregate_to_user_track) having produced the aggregated
dataset in memory or temporary storage, and T025 (join_exposure_data) having
joined the exposure data.
"""
import os
import logging
from pathlib import Path
import pandas as pd
import pyarrow.parquet as pq
import hashlib
import yaml
from datetime import datetime

from config import get_project_root, get_config_dict
from aggregation import aggregate_to_user_track, join_exposure_data, filter_zero_variance
from cue_matching import match_cues, normalize_cues
from state_manager import register_file, save_state
from utils import setup_logging

# Configure logging
logger = setup_logging(__name__)


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_aggregated_data() -> pd.DataFrame:
    """
    Load and join exposure data with matched cues to create the User-Track pairs.

    This function orchestrates the final assembly of the user_track_pairs dataset
    by:
    1. Loading the ingested cohort (from T018)
    2. Loading matched cues (from T024/T047)
    3. Joining exposure data (T025)
    4. Aggregating to user-track level (T026)
    5. Filtering zero variance tracks (T027)
    """
    project_root = get_project_root()
    
    # Load ingested cohort (T018 output)
    ingested_path = project_root / "data" / "processed" / "ingested_cohort.parquet"
    if not ingested_path.exists():
        raise FileNotFoundError(f"Ingested cohort not found at {ingested_path}. Run T018 first.")
    
    cohort_df = pd.read_parquet(ingested_path)
    logger.info(f"Loaded ingested cohort with {len(cohort_df)} rows")

    # Load matched cues from the aggregation step
    # The aggregation module should have already performed the join and aggregation
    # We assume the aggregated data is available via the aggregation module's state
    # or we re-run the aggregation logic here to ensure consistency.
    
    # Re-run aggregation to ensure we have the latest data
    # This is necessary because the aggregation step (T026) might have been
    # run in a previous session and we need to ensure the data is fresh.
    
    # Load cues (assuming they are in data/processed or loaded by aggregation)
    # The aggregation module handles the loading of AMT data internally.
    # We rely on aggregate_to_user_track to return the final DataFrame.
    
    # Check if we need to re-run matching or if we can load pre-computed matches
    # For simplicity and correctness, we re-run the aggregation pipeline
    # from the ingested cohort.
    
    # Note: In a real pipeline, we would load the pre-computed matches.
    # Here, we assume the aggregation module has the logic to do this.
    
    # Call the aggregation function to get the user-track pairs
    # This function should handle loading the necessary data and performing the join
    user_track_df = aggregate_to_user_track(cohort_df)
    
    if user_track_df is None or len(user_track_df) == 0:
        logger.warning("Aggregation returned empty DataFrame. Check input data.")
        return pd.DataFrame()

    logger.info(f"Aggregated to {len(user_track_df)} user-track pairs")

    # Filter zero variance tracks (T027)
    filtered_df = filter_zero_variance(user_track_df)
    logger.info(f"After filtering zero variance: {len(filtered_df)} rows")

    return filtered_df


def save_final_dataset(df: pd.DataFrame, output_path: Path) -> None:
    """Save the DataFrame to Parquet format."""
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Parquet
    table = pa.Table.from_pandas(df)
    pq.write_table(table, output_path)
    
    logger.info(f"Saved user-track pairs to {output_path} ({len(df)} rows)")


def save_state_entry(file_path: Path, checksum: str, description: str) -> None:
    """Update state.yaml with the new artifact."""
    state_path = get_project_root() / "state.yaml"
    
    state = {}
    if state_path.exists():
        with open(state_path, 'r') as f:
            state = yaml.safe_load(f) or {}
    
    state['artifacts'] = state.get('artifacts', {})
    state['artifacts']['user_track_pairs'] = {
        'path': str(file_path.relative_to(get_project_root())),
        'checksum': checksum,
        'description': description,
        'timestamp': datetime.now().isoformat()
    }
    
    with open(state_path, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)
    
    logger.info(f"Updated state.yaml with {file_path.name}")


def main():
    """Main entry point for generating user_track_pairs.parquet."""
    logger.info("Starting user_track_pairs generation (T029)")
    
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    
    try:
        # Load and aggregate data
        df = load_aggregated_data()
        
        if df.empty:
            logger.error("No data to save. Aborting.")
            return 1
        
        # Save to Parquet
        save_final_dataset(df, output_path)
        
        # Calculate checksum
        checksum = calculate_file_checksum(output_path)
        
        # Update state.yaml
        save_state_entry(
            output_path, 
            checksum, 
            "Aggregated User-Track pairs with exposure ratios and memory attributes"
        )
        
        logger.info(f"T029 completed successfully. Output: {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Error generating user_track_pairs: {e}", exc_info=True)
        return 1


if __name__ == "__main__":
    import pyarrow as pa
    exit_code = main()
    exit(exit_code)
