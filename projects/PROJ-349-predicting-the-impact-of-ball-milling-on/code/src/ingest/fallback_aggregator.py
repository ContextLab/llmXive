"""
Fallback aggregation logic for loading verified static subsets.
"""
import logging
import os
import pandas as pd
from pathlib import Path
from typing import Optional

from src.exceptions import DataIngestionError, InsufficientDataError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

FALLBACK_FILE_PATH = "data/fallback/uci_verified_subset.csv"

def load_fallback_data() -> Optional[pd.DataFrame]:
    """
    Load the verified static subset from T043 (UCI fallback).
    
    Returns:
        DataFrame if file exists and is valid, None otherwise.
    """
    fallback_path = Path(FALLBACK_FILE_PATH)
    
    if not fallback_path.exists():
        logger.warning(f"Fallback file not found at {fallback_path}.")
        return None
    
    try:
        df = pd.read_csv(fallback_path)
        if df.empty:
            logger.warning("Fallback file exists but contains no rows.")
            return None
        
        # Validate basic schema presence (optional but good practice)
        required_cols = ['experiment_id', 'source', 'material_type', 'milling_speed', 
                       'milling_time', 'ball_to_powder_ratio', 'youngs_modulus', 
                       'density', 'd10', 'd50', 'd90', 'process_duration']
        
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            logger.warning(f"Fallback data missing required columns: {missing_cols}")
            # Return anyway as it might be partially useful, but log warning
        
        logger.info(f"Successfully loaded fallback data with {len(df)} rows.")
        return df
    except Exception as e:
        logger.error(f"Error reading fallback file: {e}")
        return None

def append_fallback_if_needed(
    primary_df: pd.DataFrame,
    threshold: int = 150
) -> pd.DataFrame:
    """
    Append fallback data if primary dataset is below threshold.
    
    Args:
        primary_df: The primary merged dataset.
        threshold: Minimum required rows.
        
    Returns:
        Combined DataFrame if fallback was used, otherwise primary_df.
    """
    if len(primary_df) >= threshold:
        logger.info(f"Primary dataset ({len(primary_df)} rows) meets threshold ({threshold}). Skipping fallback.")
        return primary_df
    
    logger.warning(f"Primary dataset ({len(primary_df)} rows) below threshold ({threshold}). Appending fallback.")
    fallback_df = load_fallback_data()
    
    if fallback_df is None or fallback_df.empty:
        logger.error("Fallback data unavailable. Cannot append.")
        return primary_df
    
    # Combine dataframes
    combined = pd.concat([primary_df, fallback_df], ignore_index=True)
    logger.info(f"Combined dataset size: {len(combined)} rows.")
    return combined

def run_fallback_aggregation(
    primary_df: pd.DataFrame,
    output_path: str = "data/processed/merged_with_fallback.csv",
    threshold: int = 150
) -> pd.DataFrame:
    """
    Run the full fallback aggregation pipeline.
    
    Args:
        primary_df: Primary merged dataset.
        output_path: Path to save the final output.
        threshold: Minimum row threshold.
        
    Returns:
        Final aggregated DataFrame.
    """
    final_df = append_fallback_if_needed(primary_df, threshold)
    
    # Save output
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    final_df.to_csv(output_path, index=False)
    logger.info(f"Final aggregated dataset saved to {output_path}")
    
    return final_df
