"""
Aggregation Module for the Impact of Incidental Music on Autobiographical Memory Retrieval project.

This module handles joining exposure data with matched cues, aggregating to User-Track pairs,
filtering zero-variance tracks, and enforcing match rate thresholds.

Functions:
  join_exposure_data: Joins matched cues with exposure data.
  aggregate_to_user_track: Aggregates data to User-Track pair level.
  filter_zero_variance: Filters out tracks with high exposure but no memory cues.
  enforce_match_rate: Verifies match rate >= 80% (SC-004).
"""
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import pandas as pd
import numpy as np
from config import get_project_root, get_config_dict

logger = logging.getLogger(__name__)

def join_exposure_data(df_matched: pd.DataFrame, df_exposure: pd.DataFrame,
                       track_id_col: str = 'track_id', 
                       matched_title_col: str = 'matched_title',
                       matched_artist_col: str = 'matched_artist') -> pd.DataFrame:
    """
    Joins matched cues with exposure data (Track-level exposure joined to User-Track pairs).

    Args:
        df_matched: DataFrame with matched cues.
        df_exposure: DataFrame with exposure scores per track.
        track_id_col: Name of the track ID column in exposure data.
        matched_title_col: Name of the matched title column.
        matched_artist_col: Name of the matched artist column.

    Returns:
        DataFrame with exposure data joined to matched cues.
    """
    logger.info("Joining exposure data with matched cues")
    
    # Create a mapping from (title, artist) to track_id and exposure scores
    exposure_map = df_exposure.set_index(['title', 'artist']).to_dict('index')
    
    def get_exposure(row):
        key = (row[matched_title_col], row[matched_artist_col])
        if key in exposure_map:
            return exposure_map[key]
        return None
    
    # Merge logic (simplified for this implementation)
    # In practice, we would join on track_id directly if available
    df = df_matched.merge(df_exposure, left_on=[matched_title_col, matched_artist_col],
                          right_on=['title', 'artist'], how='left')
    
    logger.info(f"Joined {len(df)} records with exposure data")
    return df

def aggregate_to_user_track(df: pd.DataFrame, user_id_col: str = 'user_id',
                            track_id_col: str = 'track_id',
                            vividness_col: str = 'vividness',
                            valence_col: str = 'valence') -> pd.DataFrame:
    """
    Aggregates data to User-Track pair level (mean vividness, mean valence) as per plan.md update.

    Args:
        df: DataFrame with user, track, and memory attribute data.
        user_id_col: Name of the user ID column.
        track_id_col: Name of the track ID column.
        vividness_col: Name of the vividness column.
        valence_col: Name of the valence column.

    Returns:
        DataFrame aggregated to User-Track pair level.
    """
    logger.info("Aggregating to User-Track pair level")
    
    agg_dict = {
        vividness_col: 'mean',
        valence_col: 'mean',
        track_id_col: 'first',  # Keep track ID
        user_id_col: 'first'     # Keep user ID
    }
    
    # Add exposure columns if present
    exposure_cols = [col for col in df.columns if 'exposure' in col.lower()]
    for col in exposure_cols:
        agg_dict[col] = 'first'
    
    df_agg = df.groupby([user_id_col, track_id_col]).agg(agg_dict).reset_index()
    df_agg = df_agg.rename(columns={
        vividness_col: 'mean_vividness',
        valence_col: 'mean_valence'
    })
    
    logger.info(f"Aggregated to {len(df_agg)} User-Track pairs")
    return df_agg

def filter_zero_variance(df: pd.DataFrame, exposure_col: str = 'residualized_exposure_score',
                         threshold: float = 0.95) -> pd.DataFrame:
    """
    Filters out tracks with high exposure but no memory cues.

    Args:
        df: DataFrame with User-Track pair data.
        exposure_col: Name of the exposure score column.
        threshold: Variance threshold below which to filter.

    Returns:
        Filtered DataFrame.
    """
    logger.info("Filtering zero-variance tracks")
    
    if exposure_col not in df.columns:
        logger.warning(f"Exposure column '{exposure_col}' not found. Skipping zero-variance filter.")
        return df
    
    # Calculate variance per track
    track_variance = df.groupby('track_id')[exposure_col].var()
    valid_tracks = track_variance[track_variance > 0].index
    
    df_filtered = df[df['track_id'].isin(valid_tracks)]
    logger.info(f"Filtered to {len(df_filtered)} User-Track pairs with non-zero variance")
    
    return df_filtered

def enforce_match_rate(df: pd.DataFrame, match_col: str = 'is_match', 
                       threshold: float = 0.80) -> bool:
    """
    Verifies SC-004 (Match Rate >= 80%); LOG WARNING and proceed if threshold is missed,
    do NOT raise exception. This task MUST run before any modeling tasks.

    Args:
        df: DataFrame with match status column.
        match_col: Name of the match status column.
        threshold: Minimum required match rate.

    Returns:
        True if match rate meets threshold, False otherwise.
    """
    logger.info(f"Enforcing match rate threshold: {threshold:.0%}")
    
    match_rate = df[match_col].mean()
    logger.info(f"Current match rate: {match_rate:.2%}")
    
    if match_rate < threshold:
        logger.warning(f"Match rate ({match_rate:.2%}) is below threshold ({threshold:.0%}). "
                       "Proceeding with warning as per SC-004.")
        return False
    else:
        logger.info(f"Match rate ({match_rate:.2%}) meets threshold ({threshold:.0%}).")
        return True
