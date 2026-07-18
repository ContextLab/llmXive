import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

# Import from local utils
from utils.logging_utils import get_exclusion_log_path, log_exclusion, get_logger
from utils.schema import MergedDataset
from config import ensure_directories

# Configure logger for this module
logger = get_logger(__name__)

def load_mfq_data() -> pd.DataFrame:
    """
    Load MFQ data from the generated synthetic dataset or real source.
    For this simulation task, we assume the data exists in data/processed/.
    """
    data_path = Path("data/processed/mfq_data.csv")
    if not data_path.exists():
        logger.error(f"MFQ data file not found at {data_path}. Run simulation first.")
        raise FileNotFoundError(f"MFQ data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from MFQ data.")
    return df

def load_stories_data() -> pd.DataFrame:
    """
    Load Moral Stories data from the generated synthetic dataset.
    """
    data_path = Path("data/processed/stories_data.csv")
    if not data_path.exists():
        logger.error(f"Stories data file not found at {data_path}. Run simulation first.")
        raise FileNotFoundError(f"Stories data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from Stories data.")
    return df

def load_vr_logs_data() -> pd.DataFrame:
    """
    Load VR interaction logs from the generated synthetic dataset.
    """
    data_path = Path("data/processed/vr_logs_data.csv")
    if not data_path.exists():
        logger.error(f"VR logs data file not found at {data_path}. Run simulation first.")
        raise FileNotFoundError(f"VR logs data file not found: {data_path}")
    
    df = pd.read_csv(data_path)
    logger.info(f"Loaded {len(df)} rows from VR logs data.")
    return df

def merge_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge MFQ, Stories, and VR Logs datasets on participant_id and story_id.
    Logs exclusion reasons for mismatched IDs to data/logs/exclusion.log.
    """
    ensure_directories()
    
    # Ensure we have the necessary columns
    # MFQ should have: participant_id, ...
    # Stories should have: participant_id, story_id, ...
    # VR Logs should have: participant_id, story_id, ...
    
    required_mfq_cols = ['participant_id']
    required_stories_cols = ['participant_id', 'story_id']
    required_vr_cols = ['participant_id', 'story_id']
    
    # Validate presence of required columns
    for col in required_mfq_cols:
        if col not in mfq_df.columns:
            raise ValueError(f"MFQ data missing required column: {col}")
    for col in required_stories_cols:
        if col not in stories_df.columns:
            raise ValueError(f"Stories data missing required column: {col}")
    for col in required_vr_cols:
        if col not in vr_logs_df.columns:
            raise ValueError(f"VR Logs data missing required column: {col}")

    # Step 1: Merge Stories with VR Logs on (participant_id, story_id)
    # Inner join to keep only matching records
    stories_vr_merged = pd.merge(
        stories_df, 
        vr_logs_df, 
        on=['participant_id', 'story_id'], 
        how='inner', 
        suffixes=('_stories', '_vr')
    )
    
    # Identify mismatches between Stories and VR Logs
    stories_ids = set(zip(stories_df['participant_id'], stories_df['story_id']))
    vr_ids = set(zip(vr_logs_df['participant_id'], vr_logs_df['story_id']))
    mismatched_sv = stories_ids - vr_ids
    
    if mismatched_sv:
        logger.warning(f"Found {len(mismatched_sv)} mismatched IDs between Stories and VR Logs.")
        # Log exclusion reasons
        exclusion_log_path = get_exclusion_log_path()
        for pid, sid in mismatched_sv:
            log_exclusion(
                source="stories_vr_merge",
                participant_id=str(pid),
                story_id=str(sid),
                reason="Missing matching VR log entry for this participant-story pair."
            )
    
    # Step 2: Merge the result with MFQ on participant_id
    final_merged = pd.merge(
        stories_vr_merged,
        mfq_df[['participant_id']], # Only need participant_id from MFQ for validation/merge
        on='participant_id',
        how='inner'
    )
    
    # Identify mismatches between (Stories+VR) and MFQ
    merged_ids = set(final_merged['participant_id'])
    mfq_ids = set(mfq_df['participant_id'])
    mismatched_m = merged_ids - mfq_ids
    
    if mismatched_m:
        logger.warning(f"Found {len(mismatched_m)} mismatched participant IDs between (Stories+VR) and MFQ.")
        exclusion_log_path = get_exclusion_log_path()
        for pid in mismatched_m:
            log_exclusion(
                source="final_merge",
                participant_id=str(pid),
                story_id=None,
                reason="Missing matching MFQ entry for this participant."
            )

    logger.info(f"Merge complete. Final dataset size: {len(final_merged)} rows.")
    return final_merged

def validate_and_save(merged_df: pd.DataFrame) -> str:
    """
    Validate the merged dataset against the MergedDataset schema and save to CSV.
    Returns the path to the saved file.
    """
    output_path = Path("data/processed/merged_dataset.csv")
    
    # Basic validation
    if 'participant_id' not in merged_df.columns or 'story_id' not in merged_df.columns:
        raise ValueError("Merged dataset missing required columns 'participant_id' or 'story_id'.")
    
    # Save to CSV
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged dataset to {output_path}")
    
    return str(output_path)

def main():
    """
    Main entry point for the ingestion pipeline.
    Loads data, merges it, logs exclusions, and saves the result.
    """
    try:
        # Load data
        mfq_df = load_mfq_data()
        stories_df = load_stories_data()
        vr_logs_df = load_vr_logs_data()
        
        # Merge datasets (this handles the logging of exclusions)
        merged_df = merge_datasets(mfq_df, stories_df, vr_logs_df)
        
        # Validate and save
        output_path = validate_and_save(merged_df)
        
        logger.info(f"Ingestion pipeline completed successfully. Output: {output_path}")
        return 0
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
