"""
Proxy Extractor Service

Extracts metadata-based proxies representing "perceived control" from social media posts.
STRICT CONSTRAINT: This module MUST NOT access or process text content (Constitution Principle VI).
All calculations rely solely on metadata fields: post_id, user_id, timestamp, filter_applied, etc.
"""

import json
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import pandas as pd
import numpy as np

from code.config import CONFIG

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def calculate_filter_applied_contribution(row: pd.Series) -> float:
    """
    Calculate the contribution of filter_applied flag to control_proxy.
    
    Args:
        row: A DataFrame row containing metadata (specifically 'filter_applied')
    
    Returns:
        float: +1.0 if filter_applied is True/1, else 0.0
    """
    # Explicitly check for the flag in metadata only
    filter_val = row.get('filter_applied', False)
    
    # Handle various boolean representations
    if filter_val is True or filter_val == 1 or filter_val == 'true':
        return 1.0
    return 0.0


def calculate_timestamp_regularity(user_timestamps: List[str]) -> float:
    """
    Calculate timestamp regularity metric for a user.
    
    Measures how regular a user's posting schedule is.
    Returns a value between 0.0 (irregular) and 1.0 (highly regular).
    
    Args:
        user_timestamps: List of timestamp strings for a single user
    
    Returns:
        float: Regularity score (0.0 to 1.0)
    """
    if len(user_timestamps) < 2:
        return 0.0
    
    try:
        # Parse timestamps
        timestamps = pd.to_datetime(user_timestamps)
        timestamps = timestamps.sort_values()
        
        # Calculate time differences between consecutive posts
        diffs = timestamps.diff().dropna()
        
        if len(diffs) < 1:
            return 0.0
        
        # Convert to hours
        diffs_hours = diffs.dt.total_seconds() / 3600
        
        # Calculate coefficient of variation (std/mean)
        mean_diff = diffs_hours.mean()
        std_diff = diffs_hours.std()
        
        if mean_diff == 0:
            return 1.0  # Perfectly regular (all posts at same time)
        
        cv = std_diff / mean_diff
        
        # Convert CV to a 0-1 scale (lower CV = higher regularity)
        # Using exponential decay: regularity = exp(-cv)
        regularity = np.exp(-cv)
        
        return float(np.clip(regularity, 0.0, 1.0))
        
    except Exception as e:
        logger.warning(f"Error calculating timestamp regularity: {e}")
        return 0.0


def calculate_control_proxy(row: pd.Series, user_regularity: float) -> float:
    """
    Calculate the final control_proxy score.
    
    Combines filter_applied contribution and timestamp regularity.
    Formula: control_proxy = (filter_contribution * 0.5) + (regularity * 0.5)
    
    Args:
        row: DataFrame row with metadata
        user_regularity: Pre-calculated timestamp regularity for the user
    
    Returns:
        float: Control proxy score between 0.0 and 1.0
    """
    filter_contribution = calculate_filter_applied_contribution(row)
    
    # Weighted average: 50% filter, 50% regularity
    control_proxy = (filter_contribution * 0.5) + (user_regularity * 0.5)
    
    return float(np.clip(control_proxy, 0.0, 1.0))


def run_proxy_extraction_pipeline(input_path: Path, output_path: Path) -> Dict[str, Any]:
    """
    Main pipeline for proxy extraction.
    
    Reads raw social media data, extracts control proxies from metadata only,
    and saves results to CSV.
    
    Args:
        input_path: Path to input CSV (data/raw/social_media.csv)
        output_path: Path to output CSV (data/processed/proxy_results.csv)
    
    Returns:
        Dict with pipeline statistics
    """
    logger.info(f"Starting proxy extraction pipeline from {input_path}")
    
    # Validate input exists
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    # Load data
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    
    # CRITICAL: Verify we are NOT accessing text columns
    text_cols = ['text', 'tweet', 'content', 'message', 'post_content']
    for col in text_cols:
        if col in df.columns:
            logger.warning(f"WARNING: Text column '{col}' detected but NOT used in proxy calculation")
    
    # Calculate timestamp regularity per user
    logger.info("Calculating timestamp regularity per user...")
    user_regularity = {}
    
    # Group by user_id and calculate regularity
    if 'user_id' in df.columns and 'timestamp' in df.columns:
        for user_id, group in df.groupby('user_id'):
            timestamps = group['timestamp'].dropna().tolist()
            if len(timestamps) > 0:
                user_regularity[user_id] = calculate_timestamp_regularity(timestamps)
        logger.info(f"Calculated regularity for {len(user_regularity)} unique users")
    else:
        logger.warning("Missing 'user_id' or 'timestamp' columns, defaulting regularity to 0.0")
        user_regularity = {}
    
    # Calculate control_proxy for each row
    logger.info("Calculating control_proxy for each post...")
    df['control_proxy'] = df.apply(
        lambda row: calculate_control_proxy(
            row, 
            user_regularity.get(row.get('user_id'), 0.0)
        ),
        axis=1
    )
    
    # Prepare output dataframe
    output_cols = ['post_id', 'user_id', 'control_proxy', 'timestamp_regularity']
    
    # Add timestamp_regularity column (user-level value)
    df['timestamp_regularity'] = df['user_id'].map(
        lambda uid: user_regularity.get(uid, 0.0)
    )
    
    # Ensure required columns exist
    for col in output_cols:
        if col not in df.columns:
            if col == 'post_id':
                df['post_id'] = range(len(df))
            elif col == 'user_id':
                df['user_id'] = ['unknown'] * len(df)
            else:
                df[col] = 0.0
    
    # Select and save output
    result_df = df[output_cols].copy()
    
    # Ensure output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    result_df.to_csv(output_path, index=False)
    logger.info(f"Saved proxy results to {output_path}")
    
    # Return statistics
    stats = {
        'total_rows': len(df),
        'unique_users': len(user_regularity),
        'output_rows': len(result_df),
        'avg_control_proxy': float(result_df['control_proxy'].mean()),
        'min_control_proxy': float(result_df['control_proxy'].min()),
        'max_control_proxy': float(result_df['control_proxy'].max()),
        'output_path': str(output_path)
    }
    
    logger.info(f"Pipeline completed. Stats: {stats}")
    return stats


def run_full_proxy_pipeline() -> Dict[str, Any]:
    """
    Full pipeline entry point using configured paths.
    
    Returns:
        Dict with pipeline statistics
    """
    input_path = Path(CONFIG.DATA_RAW_DIR) / 'social_media.csv'
    output_path = Path(CONFIG.DATA_PROCESSED_DIR) / 'proxy_results.csv'
    
    return run_proxy_extraction_pipeline(input_path, output_path)
