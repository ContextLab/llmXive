"""
Data ingestion module for merging MFQ and Moral Stories datasets.
Routes to simulation or real data based on configuration.
"""
import os
import sys
import logging
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

import pandas as pd

from code.config import get_path, load_yaml_config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(get_path("data/logs/ingest.log"))
    ]
)
logger = logging.getLogger(__name__)

# Paths
MFQ_PATH = "data/raw/synthetic_mfq.csv"
STORIES_PATH = "data/raw/synthetic_stories.csv"
VR_LOGS_PATH = "data/raw/synthetic_vr_logs.csv"
MERGED_OUTPUT_PATH = "data/processed/merged_data.csv"


def load_mfq_data() -> pd.DataFrame:
    """Load MFQ data from the generated synthetic dataset."""
    full_path = get_path(MFQ_PATH)
    if not full_path.exists():
        raise FileNotFoundError(f"MFQ data not found at {full_path}. Run simulation first.")
    
    logger.info(f"Loading MFQ data from {full_path}")
    df = pd.read_csv(full_path)
    logger.info(f"Loaded {len(df)} MFQ records")
    return df


def load_stories_data() -> pd.DataFrame:
    """Load Moral Stories data from the generated synthetic dataset."""
    full_path = get_path(STORIES_PATH)
    if not full_path.exists():
        raise FileNotFoundError(f"Stories data not found at {full_path}. Run simulation first.")
    
    logger.info(f"Loading stories data from {full_path}")
    df = pd.read_csv(full_path)
    logger.info(f"Loaded {len(df)} story records")
    return df


def load_vr_logs_data() -> pd.DataFrame:
    """Load VR interaction logs from the generated synthetic dataset."""
    full_path = get_path(VR_LOGS_PATH)
    if not full_path.exists():
        raise FileNotFoundError(f"VR logs not found at {full_path}. Run simulation first.")
    
    logger.info(f"Loading VR logs from {full_path}")
    df = pd.read_csv(full_path)
    logger.info(f"Loaded {len(df)} VR log records")
    return df


def merge_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge MFQ, Stories, and VR logs into a single dataset.
    
    Args:
        mfq_df: MFQ dataset
        stories_df: Moral stories dataset
        vr_logs_df: VR interaction logs dataset
        
    Returns:
        Merged DataFrame
    """
    # Merge stories and VR logs first
    merged = pd.merge(
        stories_df,
        vr_logs_df,
        on=['participant_id', 'story_id'],
        how='inner'
    )
    logger.info(f"Merged stories and VR logs: {len(merged)} records")
    
    # Merge with MFQ data
    final_df = pd.merge(
        merged,
        mfq_df,
        on='participant_id',
        how='inner'
    )
    logger.info(f"Final merged dataset: {len(final_df)} records")
    
    return final_df


def validate_and_save(df: pd.DataFrame, output_path: str) -> None:
    """Validate and save the merged dataset."""
    # Basic validation
    required_cols = ['participant_id', 'story_id', 'salience_level', 'response_time', 'gaze_metrics', 'judgment_rating']
    missing_cols = [c for c in required_cols if c not in df.columns]
    
    if missing_cols:
        raise ValueError(f"Merged data missing required columns: {missing_cols}")
    
    # Save to disk
    full_path = get_path(output_path)
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving merged data to {full_path}")
    df.to_csv(full_path, index=False)
    logger.info(f"Saved {len(df)} records to {full_path}")


def main() -> None:
    """Main entry point for the ingestion script."""
    try:
        logger.info("Starting data ingestion pipeline")
        
        # Load datasets
        mfq_df = load_mfq_data()
        stories_df = load_stories_data()
        vr_logs_df = load_vr_logs_data()
        
        # Merge
        merged_df = merge_datasets(mfq_df, stories_df, vr_logs_df)
        
        # Validate and save
        validate_and_save(merged_df, MERGED_OUTPUT_PATH)
        
        logger.info("Ingestion pipeline completed successfully")
        
    except Exception as e:
        logger.error(f"Ingestion failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
