"""
Generate the final User-Track Pair dataset and update state tracking.

This script loads the processed cue matching results and exposure data,
performs the final join and aggregation to User-Track Pair level,
saves the result as a Parquet file, and updates state.yaml with the checksum.
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
from state_manager import register_file, save_state, load_state
from utils import setup_logging, get_logger

logger = get_logger(__name__)


def calculate_file_checksum(file_path: Path) -> str:
    """Calculate SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_aggregated_data(config: dict) -> pd.DataFrame:
    """
    Load the aggregated User-Track Pair data from the intermediate CSV.
    
    This assumes T026 (aggregate_to_user_track) has already run and produced
    data/processed/aggregated_user_track_pairs.csv.
    """
    project_root = get_project_root()
    input_path = project_root / "data" / "processed" / "aggregated_user_track_pairs.csv"
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Intermediate file not found: {input_path}. "
            "Ensure T026 (aggregate_to_user_track) has been run successfully."
        )
    
    logger.info(f"Loading aggregated data from {input_path}")
    df = pd.read_csv(input_path)
    
    required_cols = ['user_id', 'track_id', 'mean_vividness', 'mean_valence', 
                     'residualized_exposure_score', 'overall_popularity_score', 'listen_count']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in aggregated data: {missing_cols}")
    
    return df


def save_final_dataset(df: pd.DataFrame, config: dict) -> Path:
    """Save the final User-Track Pair dataset as Parquet."""
    project_root = get_project_root()
    output_path = project_root / "data" / "processed" / "user_track_pairs.parquet"
    
    logger.info(f"Saving final dataset to {output_path}")
    
    # Ensure directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save as Parquet
    df.to_parquet(output_path, index=False, engine='pyarrow')
    
    logger.info(f"Saved {len(df)} rows to {output_path}")
    return output_path


def main():
    """Main entry point for generating user_track_pairs.parquet."""
    setup_logging()
    config = get_config_dict()
    
    logger.info("Starting User-Track Pair generation pipeline (T029)")
    
    try:
        # 1. Load the pre-aggregated data from T026
        df = load_aggregated_data(config)
        
        # 2. Sort for reproducibility
        df = df.sort_values(by=['user_id', 'track_id']).reset_index(drop=True)
        
        # 3. Save as Parquet
        output_path = save_final_dataset(df, config)
        
        # 4. Calculate checksum
        checksum = calculate_file_checksum(output_path)
        logger.info(f"Calculated checksum for {output_path.name}: {checksum}")
        
        # 5. Update state.yaml
        state = load_state()
        register_file(
            state=state,
            file_path=output_path,
            checksum=checksum,
            task_id="T029",
            description="User-Track Pair dataset with aggregated memory attributes and exposure scores"
        )
        save_state(state)
        
        logger.info("T029 completed successfully: user_track_pairs.parquet generated and state updated.")
        
    except FileNotFoundError as e:
        logger.error(f"Missing prerequisite file: {e}")
        raise
    except Exception as e:
        logger.error(f"Error during T029 execution: {e}", exc_info=True)
        raise


if __name__ == "__main__":
    main()
