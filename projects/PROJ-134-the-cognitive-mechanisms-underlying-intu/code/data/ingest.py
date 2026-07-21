import os
import sys
import logging
import pandas as pd
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from code.config import get_path, DATA_MODE, validate_data_mode, ensure_directories
from code.utils.logging import get_logger, get_exclusion_log_path, log_exclusion, log_pipeline_step
from code.utils.schema import MergedDataset

# Initialize logger
logger = get_logger(__name__)

def load_mfq_data() -> pd.DataFrame:
    """
    Load MFQ data based on DATA_MODE.
    
    If DATA_MODE is 'simulation', load from the generated synthetic dataset.
    If DATA_MODE is 'real', route to ingest_real.py to fetch real data.
    
    Returns:
        DataFrame containing MFQ data.
    
    Raises:
        FileNotFoundError: If simulated data file is missing in simulation mode.
        NotImplementedError: If real mode is requested but Phase 6 is incomplete.
        DataFetchError: If real data fetch fails (in ingest_real).
    """
    if DATA_MODE == 'simulation':
        data_path = get_path("data/raw/synthetic_mfq.csv")
        if not data_path.exists():
            # Fallback: generate synthetic data if file missing (only in simulation mode)
            logger.warning(f"Synthetic MFQ data not found at {data_path}. Generating on-the-fly for simulation mode.")
            # Import here to avoid circular dependency if simulation_mfq.py is not yet run
            from code.data.simulation_mfq import main as generate_mfq
            generate_mfq()
        
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} MFQ records from {data_path}")
        return df
    
    elif DATA_MODE == 'real':
        # Route to real data ingestion
        logger.info("Routing to real data ingestion (ingest_real.py)...")
        try:
            from code.data.ingest_real import fetch_real_mfq_data
            df = fetch_real_mfq_data()
            logger.info(f"Loaded {len(df)} real MFQ records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch real MFQ data: {e}")
            raise
    
    else:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}")

def load_stories_data() -> pd.DataFrame:
    """
    Load Moral Stories data based on DATA_MODE.
    
    If DATA_MODE is 'simulation', load from the generated synthetic dataset.
    If DATA_MODE is 'real', route to ingest_real.py to fetch real data.
    
    Returns:
        DataFrame containing Moral Stories data.
    """
    if DATA_MODE == 'simulation':
        data_path = get_path("data/raw/synthetic_stories.csv")
        if not data_path.exists():
            logger.warning(f"Synthetic Stories data not found at {data_path}. Generating on-the-fly.")
            from code.data.simulation_stories import main as generate_stories
            generate_stories()
        
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} story records from {data_path}")
        return df
    
    elif DATA_MODE == 'real':
        logger.info("Routing to real data ingestion for stories...")
        try:
            from code.data.ingest_real import fetch_real_stories_data
            df = fetch_real_stories_data()
            logger.info(f"Loaded {len(df)} real story records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch real stories data: {e}")
            raise
    
    else:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}")

def load_vr_logs_data() -> pd.DataFrame:
    """
    Load VR Interaction Logs data based on DATA_MODE.
    
    If DATA_MODE is 'simulation', load from the generated synthetic dataset.
    If DATA_MODE is 'real', route to ingest_real.py to fetch real data.
    
    Returns:
        DataFrame containing VR Logs data.
    """
    if DATA_MODE == 'simulation':
        data_path = get_path("data/raw/synthetic_vr_logs.csv")
        if not data_path.exists():
            logger.warning(f"Synthetic VR Logs data not found at {data_path}. Generating on-the-fly.")
            from code.data.simulation_stories import main as generate_stories
            # The generate_stories function handles all three datasets including VR logs
            generate_stories()
        
        df = pd.read_csv(data_path)
        logger.info(f"Loaded {len(df)} VR log records from {data_path}")
        return df
    
    elif DATA_MODE == 'real':
        logger.info("Routing to real data ingestion for VR logs...")
        try:
            from code.data.ingest_real import fetch_real_vr_logs
            df = fetch_real_vr_logs()
            logger.info(f"Loaded {len(df)} real VR log records")
            return df
        except Exception as e:
            logger.error(f"Failed to fetch real VR logs data: {e}")
            raise
    
    else:
        raise ValueError(f"Invalid DATA_MODE: {DATA_MODE}")

def merge_datasets(mfq_df: pd.DataFrame, stories_df: pd.DataFrame, vr_logs_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge MFQ, Stories, and VR Logs datasets on participant_id and story_id.
    
    Handles ID mismatches by logging exclusions.
    
    Args:
        mfq_df: MFQ DataFrame
        stories_df: Stories DataFrame
        vr_logs_df: VR Logs DataFrame
    
    Returns:
        Merged DataFrame.
    """
    # Ensure consistent column names for merging
    # Assuming 'participant_id' is the key in all, and 'story_id' in stories/vr_logs
    
    # Step 1: Merge Stories and VR Logs on story_id
    if 'story_id' in stories_df.columns and 'story_id' in vr_logs_df.columns:
        stories_vr = pd.merge(stories_df, vr_logs_df, on='story_id', how='inner')
        logger.info(f"Merged Stories and VR Logs: {len(stories_vr)} records")
    else:
        logger.warning("Missing story_id in one of the datasets. Skipping Stories-VR merge.")
        stories_vr = stories_df.copy()
    
    # Step 2: Merge MFQ with the result on participant_id
    if 'participant_id' in mfq_df.columns and 'participant_id' in stories_vr.columns:
        merged = pd.merge(mfq_df, stories_vr, on='participant_id', how='inner')
        logger.info(f"Merged MFQ with Stories/VR: {len(merged)} records")
    else:
        logger.warning("Missing participant_id in one of the datasets. Skipping MFQ merge.")
        merged = stories_vr.copy()
    
    # Log exclusions for participants present in one but not the other (if full outer join was desired, but we do inner)
    # For now, we log the counts to indicate what was dropped
    logger.info(f"Excluded participants due to ID mismatch (inner join): "
                f"MFQ={len(mfq_df)}, Stories/VR={len(stories_vr)}, Final={len(merged)}")
    
    return merged

def validate_and_save(merged_df: pd.DataFrame) -> pd.DataFrame:
    """
    Validate the merged dataset and save to disk.
    
    Checks:
    - No null values in critical columns: gaze_x, gaze_y, response_time
    
    Args:
        merged_df: Merged DataFrame
    
    Returns:
        Validated DataFrame.
    
    Raises:
        ValueError: If validation fails.
    """
    critical_columns = ['gaze_x', 'gaze_y', 'response_time']
    
    for col in critical_columns:
        if col in merged_df.columns:
            null_count = merged_df[col].isnull().sum()
            if null_count > 0:
                error_msg = f"Found {null_count} null values in critical column '{col}'"
                logger.error(error_msg)
                raise ValueError(error_msg)
        else:
            logger.warning(f"Critical column '{col}' not found in merged dataset.")
    
    # Save to disk
    output_path = get_path("data/processed/merged_data.csv")
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Saved merged data to {output_path}")
    
    return merged_df

def main():
    """
    Main entry point for the ingestion pipeline.
    
    1. Validate DATA_MODE.
    2. Load MFQ, Stories, VR Logs.
    3. Merge datasets.
    4. Validate and save.
    """
    ensure_directories()
    validate_data_mode()
    
    log_pipeline_step("start_ingestion", DATA_MODE)
    
    try:
        mfq_df = load_mfq_data()
        stories_df = load_stories_data()
        vr_logs_df = load_vr_logs_data()
        
        merged_df = merge_datasets(mfq_df, stories_df, vr_logs_df)
        validated_df = validate_and_save(merged_df)
        
        log_pipeline_step("end_ingestion", {"records": len(validated_df)})
        logger.info("Ingestion pipeline completed successfully.")
        
    except Exception as e:
        logger.error(f"Ingestion pipeline failed: {e}")
        log_pipeline_step("end_ingestion_failed", {"error": str(e)})
        raise

if __name__ == "__main__":
    main()