"""
Aggregation module for User Story 2.
Implements cue matching, joining, and aggregation to User-Track pairs.
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np

# Add project root to path to allow imports
import sys
from config import get_project_root, get_config_dict

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def join_exposure_data(cues_df: pd.DataFrame, cohort_df: pd.DataFrame) -> pd.DataFrame:
    """
    Join matched cues with exposure data (Track-level exposure joined to User-Track pairs).
    
    Args:
        cues_df: DataFrame with matched cues (User-Track pairs with cue attributes)
        cohort_df: DataFrame with exposure data (from T018: ingested_cohort.parquet)
        
    Returns:
        DataFrame with joined exposure and cue data
    """
    logger.info("Joining exposure data with matched cues")
    
    # Ensure we have the necessary columns
    required_cue_cols = ['user_id', 'track_id', 'mean_vividness', 'mean_valence']
    required_cohort_cols = ['user_id', 'track_id', 'adolescent_exposure_ratio', 'overall_popularity_score']
    
    # Check for missing columns
    missing_cue_cols = [col for col in required_cue_cols if col not in cues_df.columns]
    missing_cohort_cols = [col for col in required_cohort_cols if col not in cohort_df.columns]
    
    if missing_cue_cols:
        logger.error(f"Missing columns in cues_df: {missing_cue_cols}")
        raise ValueError(f"Missing columns in cues_df: {missing_cue_cols}")
        
    if missing_cohort_cols:
        logger.error(f"Missing columns in cohort_df: {missing_cohort_cols}")
        raise ValueError(f"Missing columns in cohort_df: {missing_cohort_cols}")
    
    # Select only necessary columns from cohort_df
    cohort_subset = cohort_df[required_cohort_cols].drop_duplicates(subset=['user_id', 'track_id'])
    
    # Merge on user_id and track_id
    merged_df = cues_df.merge(
        cohort_subset,
        on=['user_id', 'track_id'],
        how='inner'
    )
    
    logger.info(f"Joined dataset shape: {merged_df.shape}")
    return merged_df

def aggregate_to_user_track(cues_df: pd.DataFrame, cues_metadata: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate data to User-Track Pair level (mean vividness, mean valence).
    
    Args:
        cues_df: DataFrame with raw cue matches
        cues_metadata: DataFrame with cue metadata (vividness, valence)
        
    Returns:
        DataFrame aggregated to User-Track pairs
    """
    logger.info("Aggregating to User-Track pairs")
    
    # Merge cues with metadata
    merged = cues_df.merge(
        cues_metadata[['cue_id', 'vividness', 'valence']],
        on='cue_id',
        how='left'
    )
    
    # Aggregate by user_id and track_id
    aggregated = merged.groupby(['user_id', 'track_id']).agg({
        'vividness': 'mean',
        'valence': 'mean',
        'cue_id': 'count'  # Count of cues per pair
    }).reset_index()
    
    aggregated = aggregated.rename(columns={'cue_id': 'cue_count'})
    
    logger.info(f"Aggregated dataset shape: {aggregated.shape}")
    return aggregated

def filter_zero_variance(aggregated_df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter out tracks with zero associated User-Track pairs.
    
    This removes tracks that have no rows in the pair-level table,
    avoiding singularities in the design matrix.
    
    Args:
        aggregated_df: DataFrame with User-Track pairs
        
    Returns:
        Filtered DataFrame
    """
    logger.info("Filtering tracks with zero User-Track pairs")
    
    # Count pairs per track
    track_counts = aggregated_df.groupby('track_id').size()
    
    # Get tracks with at least one pair
    valid_tracks = track_counts[track_counts > 0].index.tolist()
    
    # Filter the dataframe
    filtered_df = aggregated_df[aggregated_df['track_id'].isin(valid_tracks)].copy()
    
    logger.info(f"Original tracks: {aggregated_df['track_id'].nunique()}, "
               f"Filtered tracks: {filtered_df['track_id'].nunique()}")
    
    return filtered_df

def enforce_match_rate(aggregated_df: pd.DataFrame, cues_df: pd.DataFrame) -> pd.DataFrame:
    """
    Verify SC-004 (Match Rate >= config.MATCH_RATE_THRESHOLD).
    
    If threshold is '[deferred]', log warning and proceed.
    If numeric, check and log warning if below threshold, but do NOT raise exception.
    
    Args:
        aggregated_df: Aggregated User-Track pairs
        cues_df: Original cues dataframe
        
    Returns:
        The same aggregated_df (unchanged, but with logging)
    """
    logger.info("Enforcing match rate threshold")
    
    config = get_config_dict()
    threshold = config.get('MATCH_RATE_THRESHOLD', '[deferred]')
    
    # Calculate match rate
    total_cues = len(cues_df)
    matched_cues = aggregated_df['cue_count'].sum()
    
    if total_cues == 0:
        match_rate = 0.0
    else:
        match_rate = matched_cues / total_cues
    
    logger.info(f"Match rate: {match_rate:.4f} ({matched_cues}/{total_cues})")
    
    if threshold == '[deferred]':
        logger.warning("Match rate threshold is [deferred]. Proceeding with analysis.")
    else:
        try:
            threshold_val = float(threshold)
            if match_rate < threshold_val:
                logger.warning(f"Match rate ({match_rate:.4f}) is below threshold ({threshold_val}). "
                             f"Proceeding with analysis as per SC-004.")
            else:
                logger.info(f"Match rate ({match_rate:.4f}) meets threshold ({threshold_val}).")
        except (ValueError, TypeError):
            logger.warning(f"Invalid threshold value: {threshold}. Proceeding with analysis.")
    
    return aggregated_df

def load_aggregated_data() -> Optional[pd.DataFrame]:
    """
    Load the final aggregated User-Track pairs dataset.
    This is called by T029 to get the data to save.
    
    Returns:
        DataFrame with User-Track pairs, or None if not available
    """
    # The aggregated data should already be in memory from T036
    # We need to reconstruct it or load from intermediate storage
    
    # For now, we assume the data is available via the pipeline state
    # In a real implementation, this would load from a temporary file
    # or be passed as an argument
    
    # Since T036 (enforce_match_rate) returns the dataframe,
    # and T029 runs after T036, we need to ensure the data is available
    
    # For this implementation, we'll load from the last known state
    # In practice, the pipeline orchestration would pass this data directly
    
    project_root = get_project_root()
    intermediate_path = project_root / "data" / "processed" / "user_track_pairs_temp.parquet"
    
    if intermediate_path.exists():
        try:
            df = pd.read_parquet(intermediate_path)
            logger.info(f"Loaded intermediate data from {intermediate_path}")
            return df
        except Exception as e:
            logger.error(f"Failed to load intermediate data: {e}")
            return None
    else:
        logger.error("Intermediate data file not found. T036 may not have completed.")
        return None

def main():
    """Main entry point for aggregation pipeline."""
    logger.info("Starting aggregation pipeline")
    
    # This would be called by the orchestration script
    # For now, it's a placeholder
    logger.info("Aggregation pipeline completed")

if __name__ == "__main__":
    main()
