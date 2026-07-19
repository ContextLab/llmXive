"""
Ingest and merge MFQ, Moral Stories, and VR interaction datasets.

This module handles the routing between simulation and real data ingestion.
If DATA_MODE is 'simulation', it generates synthetic data.
If DATA_MODE is 'real', it attempts to fetch real data from OSF/HuggingFace.
"""
import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Add project root to path if not already present
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from config import get_path, validate_data_mode, DATA_MODE
from utils.logging import get_logger, get_exclusion_log_path, log_exclusion, log_pipeline_step
from data.simulation_mfq import main as generate_mfq
from data.simulation_stories import main as generate_stories
from data.ingest_real import fetch_real_mfq_data, fetch_real_stories_data, fetch_real_vr_logs, DataFetchError

# Initialize logger
logger = get_logger(__name__)

def load_mfq_data() -> pd.DataFrame:
    """
    Load MFQ data from the generated synthetic dataset or real source.

    Returns:
        DataFrame containing MFQ data.
    """
    if DATA_MODE == 'simulation':
        logger.info("Generating synthetic MFQ data...")
        generate_mfq()
        data_path = get_path("data/raw/synthetic_mfq.csv")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Synthetic MFQ data not found at {data_path}")
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} synthetic MFQ records.")
        return df
    elif DATA_MODE == 'real':
        logger.info("Fetching real MFQ data from OSF...")
        try:
            df = fetch_real_mfq_data()
            logger.info(f"Loaded {len(df)} real MFQ records.")
            return df
        except DataFetchError as e:
            logger.error(f"Failed to fetch real MFQ data: {e}")
            raise
    else:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}")

def load_stories_data() -> pd.DataFrame:
    """
    Load Moral Stories data from the generated synthetic dataset or real source.

    Returns:
        DataFrame containing Moral Stories data.
    """
    if DATA_MODE == 'simulation':
        logger.info("Generating synthetic Moral Stories data...")
        generate_stories()
        data_path = get_path("data/raw/synthetic_stories.csv")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Synthetic Moral Stories data not found at {data_path}")
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} synthetic Moral Stories records.")
        return df
    elif DATA_MODE == 'real':
        logger.info("Fetching real Moral Stories data from HuggingFace...")
        try:
            df = fetch_real_stories_data()
            logger.info(f"Loaded {len(df)} real Moral Stories records.")
            return df
        except DataFetchError as e:
            logger.error(f"Failed to fetch real Moral Stories data: {e}")
            raise
    else:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}")

def load_vr_logs_data() -> pd.DataFrame:
    """
    Load VR interaction logs from the generated synthetic dataset or real source.

    Returns:
        DataFrame containing VR interaction logs.
    """
    if DATA_MODE == 'simulation':
        # VR logs are generated as part of the stories simulation
        logger.info("VR logs already generated with synthetic stories.")
        data_path = get_path("data/raw/synthetic_vr_logs.csv")
        if not os.path.exists(data_path):
            raise FileNotFoundError(f"Synthetic VR logs not found at {data_path}")
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} synthetic VR log records.")
        return df
    elif DATA_MODE == 'real':
        logger.info("Fetching real VR interaction logs...")
        try:
            df = fetch_real_vr_logs()
            logger.info(f"Loaded {len(df)} real VR log records.")
            return df
        except DataFetchError as e:
            logger.error(f"Failed to fetch real VR logs data: {e}")
            raise
    else:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}")

def merge_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge MFQ, Moral Stories, and VR interaction logs.

    Handles ID mismatches by logging exclusions.

    Args:
        mfq_df: DataFrame with MFQ data (must have 'participant_id')
        stories_df: DataFrame with Moral Stories data (must have 'participant_id', 'story_id')
        vr_logs_df: DataFrame with VR logs (must have 'participant_id', 'story_id')

    Returns:
        Merged DataFrame with all matching records.
    """
    logger.info("Starting dataset merge...")

    # Validate required columns
    required_mfq = ['participant_id']
    required_stories = ['participant_id', 'story_id']
    required_vr = ['participant_id', 'story_id']

    for col in required_mfq:
        if col not in mfq_df.columns:
            raise ValueError(f"MFQ DataFrame missing required column: {col}")
    for col in required_stories:
        if col not in stories_df.columns:
            raise ValueError(f"Stories DataFrame missing required column: {col}")
    for col in required_vr:
        if col not in vr_logs_df.columns:
            raise ValueError(f"VR Logs DataFrame missing required column: {col}")

    # Merge MFQ with Stories on participant_id
    merged_df = pd.merge(
        mfq_df,
        stories_df,
        on='participant_id',
        how='inner',
        suffixes=('_mfq', '_stories')
    )

    # Log excluded participants (MFQ present but no stories)
    excluded_participants = set(mfq_df['participant_id']) - set(merged_df['participant_id'])
    for pid in excluded_participants:
        log_exclusion("participant_id", str(pid), "No matching stories data", logger)

    # Merge result with VR logs on participant_id and story_id
    final_df = pd.merge(
        merged_df,
        vr_logs_df,
        on=['participant_id', 'story_id'],
        how='inner',
        suffixes=('', '_vr')
    )

    # Log excluded records (stories present but no VR logs)
    story_keys = set(zip(merged_df['participant_id'], merged_df['story_id']))
    vr_keys = set(zip(final_df['participant_id'], final_df['story_id']))
    excluded_keys = story_keys - vr_keys
    for pid, sid in excluded_keys:
        log_exclusion("participant_id+story_id", f"{pid}_{sid}", "No matching VR logs", logger)

    logger.info(f"Merge complete. Final dataset size: {len(final_df)} records.")
    return final_df

def validate_and_save(merged_df: pd.DataFrame) -> str:
    """
    Validate the merged dataset and save to disk.

    Args:
        merged_df: The merged DataFrame.

    Returns:
        Path to the saved file.
    """
    output_path = get_path("data/processed/merged_data.csv")

    # Basic validation
    if merged_df.empty:
        raise ValueError("Merged dataset is empty. Cannot save.")

    # Ensure required columns exist
    required_cols = ['participant_id', 'story_id']
    for col in required_cols:
        if col not in merged_df.columns:
            raise ValueError(f"Missing required column in merged data: {col}")

    # Save to CSV
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path} ({len(merged_df)} rows).")

    return str(output_path)

def main():
    """
    Main entry point for the ingestion pipeline.
    """
    logger.info("Starting data ingestion pipeline...")

    # Validate configuration
    validate_data_mode()

    try:
        # Load datasets
        mfq_df = load_mfq_data()
        stories_df = load_stories_data()
        vr_logs_df = load_vr_logs_data()

        # Merge datasets
        merged_df = merge_datasets(mfq_df, stories_df, vr_logs_df)

        # Validate and save
        output_path = validate_and_save(merged_df)

        logger.info("Data ingestion pipeline completed successfully.")
        return output_path

    except Exception as e:
        logger.error(f"Data ingestion pipeline failed: {e}")
        raise

if __name__ == "__main__":
    main()
