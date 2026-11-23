"""
Pipeline step to join raw text data with extracted emoji features.

This module handles the merging of the raw corpus (loaded in T012)
with the extracted features (generated in T011). It includes robust
error handling for edge cases such as zero-length text, encoding errors,
and missing values.

Prerequisites:
- T012 (Data Loader) must have completed successfully (data present).
- T011 (Emoji Extraction) must be available.
"""
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np

# Import from existing project modules
from src.data.preprocessing import extract_emoji_features
from src.utils.io import set_global_seed, ensure_directory
from src.data.loaders import DataUnavailableError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set global seed for reproducibility
set_global_seed(42)

def join_raw_with_features(
    raw_df: pd.DataFrame,
    output_path: Optional[Path] = None
) -> pd.DataFrame:
    """
    Join raw text data with extracted emoji features.
    
    This function:
    1. Validates the input dataframe has required columns (message_id, text).
    2. Extracts emoji features for each text entry, handling edge cases.
    3. Joins the extracted features back to the original dataframe.
    4. Handles encoding errors and zero-length text gracefully.
    
    Args:
        raw_df (pd.DataFrame): The raw dataset loaded from T012.
        output_path (Optional[Path]): If provided, saves the joined dataframe
                                     to this path.
    
    Returns:
        pd.DataFrame: The joined dataframe with original columns plus
                     extracted emoji features.
    
    Raises:
        ValueError: If required columns are missing in raw_df.
        DataUnavailableError: If the input dataframe is empty.
    """
    logger.info(f"Starting join process on dataset with {len(raw_df)} rows.")
    
    if raw_df.empty:
        raise DataUnavailableError("Input dataframe is empty.")
    
    required_cols = ['message_id', 'text']
    missing_cols = [col for col in required_cols if col not in raw_df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")
    
    # Ensure text column is string type to handle potential NaNs or non-strings
    # Replace NaN with empty string for processing, but track original status if needed
    raw_df = raw_df.copy()
    raw_df['text'] = raw_df['text'].fillna('').astype(str)
    
    # Extract features
    extracted_features = []
    skipped_count = 0
    error_count = 0
    
    for idx, row in raw_df.iterrows():
        text = row['text']
        msg_id = row['message_id']
        
        try:
            # Handle zero-length text
            if not text or text.strip() == '':
                # Create a feature row with empty/zero values
                features = {
                    'message_id': msg_id,
                    'emoji_present': False,
                    'emoji_count': 0,
                    'emoji_types': [],
                    'text_length': 0
                }
                extracted_features.append(features)
                continue
            
            # Extract features
            features = extract_emoji_features(text)
            features['message_id'] = msg_id
            features['text_length'] = len(text)
            extracted_features.append(features)
            
        except Exception as e:
            # Log error but continue processing
            error_count += 1
            logger.warning(f"Error processing message_id {msg_id}: {str(e)}")
            
            # Fallback for failed extraction
            fallback_features = {
                'message_id': msg_id,
                'emoji_present': False,
                'emoji_count': 0,
                'emoji_types': [],
                'text_length': len(text)
            }
            extracted_features.append(fallback_features)
    
    logger.info(f"Processed {len(extracted_features)} messages. Skipped: {skipped_count}, Errors: {error_count}")
    
    # Create DataFrame from extracted features
    features_df = pd.DataFrame(extracted_features)
    
    # Merge with original dataframe on message_id
    # Use left join to ensure we keep all original rows
    joined_df = pd.merge(raw_df, features_df, on='message_id', how='left')
    
    # Fill any missing feature values with defaults (should not happen if logic is correct)
    feature_cols = ['emoji_present', 'emoji_count', 'emoji_types', 'text_length']
    for col in feature_cols:
        if col in joined_df.columns:
            if col == 'emoji_types':
                joined_df[col] = joined_df[col].apply(lambda x: x if isinstance(x, list) else [])
            else:
                joined_df[col] = joined_df[col].fillna(0)
    
    if output_path:
        ensure_directory(output_path)
        joined_df.to_csv(output_path, index=False)
        logger.info(f"Saved joined dataset to {output_path}")
    
    return joined_df

def main():
    """
    Main entry point for the pipeline join step.
    
    This function:
    1. Loads the raw data from T012 (data/raw/messages.csv).
    2. Calls join_raw_with_features to merge with extracted features.
    3. Saves the result to data/processed/features.csv.
    """
    logger.info("Running pipeline join step (T013).")
    
    # Define paths
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    raw_data_path = project_root / "data" / "raw" / "messages.csv"
    output_path = project_root / "data" / "processed" / "features.csv"
    
    if not raw_data_path.exists():
        raise FileNotFoundError(
            f"Raw data file not found at {raw_data_path}. "
            "Ensure T012 has completed successfully."
        )
    
    # Load raw data
    logger.info(f"Loading raw data from {raw_data_path}")
    try:
        raw_df = pd.read_csv(raw_data_path)
    except Exception as e:
        raise RuntimeError(f"Failed to load raw data: {str(e)}")
    
    # Perform join
    joined_df = join_raw_with_features(raw_df, output_path)
    
    logger.info(f"Pipeline join complete. Output saved to {output_path}")
    logger.info(f"Output shape: {joined_df.shape}")
    logger.info(f"Columns: {list(joined_df.columns)}")
    
    return joined_df

if __name__ == "__main__":
    main()
