"""
Data Ingestion and Preprocessing Module.

Handles loading personality and listening data, merging, cleaning, and standardizing
genre tags. Supports real data download with fallback to synthetic generation.
"""

import os
import logging
import time
import hashlib
from pathlib import Path
from typing import Tuple, Optional, List, Dict, Any

import pandas as pd
import numpy as np
import requests

from utils import setup_logging, safe_http_request, load_config
from mapping import apply_genre_mapping
from synthetic_data import generate_synthetic_data

logger = setup_logging(__name__)

# Configuration
CONFIG = load_config()
RANDOM_SEED = int(CONFIG.get("RANDOM_SEED", 42))
DATA_PATH = Path(CONFIG.get("DATA_PATH", "data"))
RAW_DATA_DIR = DATA_PATH / "raw"
PROCESSED_DATA_DIR = DATA_PATH / "processed"

# Real data sources (as per spec)
# Using OpenML for BFI-2 like data and Last.fm API or dataset
# For this implementation, we assume specific dataset IDs or URLs are configured
# If real sources fail, we fall back to synthetic as per T012 requirements
BFI_SOURCE_URL = "https://api.openml.org/data/v1/json/dataset/205" # Placeholder for BFI-2 equivalent
LASTFM_SOURCE_URL = "https://api.openml.org/data/v1/json/dataset/206" # Placeholder for Last.fm equivalent

def load_personality_data(source_url: Optional[str] = None) -> pd.DataFrame:
    """
    Load personality data (BFI-2 or equivalent).
    
    Args:
        source_url: URL to the personality dataset.
        
    Returns:
        DataFrame with personality scores.
    """
    logger.info(f"Attempting to load personality data from {source_url or 'default source'}...")
    try:
        # Attempt to fetch real data
        if source_url:
            response = safe_http_request(source_url)
            if response.status_code == 200:
                # Parse JSON response assuming OpenML format or similar
                data = response.json()
                # Convert to DataFrame (simplified for this example)
                # In a real scenario, this would parse the specific format
                df = pd.DataFrame(data.get('data', []))
                logger.info(f"Successfully loaded {len(df)} rows of personality data.")
                return df
        else:
            logger.warning("No source URL provided for personality data.")
    except Exception as e:
        logger.warning(f"Failed to load real personality data: {e}. Falling back to synthetic.")
    
    # Fallback to synthetic
    logger.info("Generating synthetic personality data...")
    df = generate_synthetic_data(n_rows=500, seed=RANDOM_SEED, data_type="personality")
    return df

def load_listening_data(source_url: Optional[str] = None) -> pd.DataFrame:
    """
    Load listening data (Last.fm or equivalent).
    
    Args:
        source_url: URL to the listening dataset.
        
    Returns:
        DataFrame with listening history.
    """
    logger.info(f"Attempting to load listening data from {source_url or 'default source'}...")
    try:
        if source_url:
            response = safe_http_request(source_url)
            if response.status_code == 200:
                data = response.json()
                df = pd.DataFrame(data.get('data', []))
                logger.info(f"Successfully loaded {len(df)} rows of listening data.")
                return df
        else:
            logger.warning("No source URL provided for listening data.")
    except Exception as e:
        logger.warning(f"Failed to load real listening data: {e}. Falling back to synthetic.")
    
    # Fallback to synthetic
    logger.info("Generating synthetic listening data...")
    df = generate_synthetic_data(n_rows=500, seed=RANDOM_SEED, data_type="listening")
    return df

def merge_dataframes(personality_df: pd.DataFrame, listening_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge personality and listening data on user_id.
    
    Args:
        personality_df: DataFrame with personality scores.
        listening_df: DataFrame with listening history.
        
    Returns:
        Merged DataFrame.
    """
    logger.info("Merging personality and listening data...")
    # Ensure common key exists
    if 'user_id' not in personality_df.columns or 'user_id' not in listening_df.columns:
        raise ValueError("Both dataframes must contain 'user_id' column.")
    
    merged = pd.merge(personality_df, listening_df, on='user_id', how='inner')
    logger.info(f"Merged dataset contains {len(merged)} users.")
    return merged

def filter_active_users(df: pd.DataFrame, min_minutes: int = 0) -> pd.DataFrame:
    """
    Exclude users with zero or less listening minutes.
    
    Args:
        df: Merged DataFrame.
        min_minutes: Minimum listening minutes threshold.
        
    Returns:
        Filtered DataFrame.
    """
    logger.info(f"Filtering users with < {min_minutes} listening minutes...")
    if 'listening_minutes' in df.columns:
        df = df[df['listening_minutes'] > min_minutes]
    logger.info(f"Remaining active users: {len(df)}")
    return df

def apply_genre_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw genre tags to standard categories.
    
    Args:
        df: DataFrame with raw genre tags.
        
    Returns:
        DataFrame with standardized genres.
    """
    logger.info("Applying genre standardization...")
    # Assuming a column 'raw_genres' or similar exists
    # If not, we might need to aggregate or handle differently
    if 'genre' in df.columns:
        df['standard_genre'] = apply_genre_mapping(df['genre'])
    elif 'genres' in df.columns:
        # Handle list of genres if present
        df['standard_genre'] = df['genres'].apply(lambda x: apply_genre_mapping(x) if isinstance(x, str) else 'Other')
    else:
        logger.warning("No genre column found. Creating 'Other' placeholder.")
        df['standard_genre'] = 'Other'
    
    return df

def preprocess_merged_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing demographic data.
    
    Args:
        df: DataFrame with potential missing values.
        
    Returns:
        Cleaned DataFrame.
    """
    logger.info("Handling missing demographic data...")
    demographics = ['age', 'gender', 'country']
    
    for col in df.columns:
        if col in demographics:
            if pd.api.types.is_numeric_dtype(df[col]):
                median_val = df[col].median()
                df[col] = df[col].fillna(median_val)
                logger.info(f"Imputed numeric '{col}' with median: {median_val}")
            else:
                mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
                df[col] = df[col].fillna(mode_val)
                logger.info(f"Imputed categorical '{col}' with mode: {mode_val}")
        else:
            # Drop rows with missing values in other critical columns if necessary
            # For now, we drop rows with any missing values to be safe
            if df[col].isnull().any():
                logger.warning(f"Column '{col}' has missing values. Dropping rows.")
                df = df.dropna(subset=[col])
    
    return df

def calculate_checksum(df: pd.DataFrame, filepath: Path) -> str:
    """
    Calculate MD5 checksum of the saved file.
    
    Args:
        df: DataFrame to save.
        filepath: Path to save the file.
        
    Returns:
        MD5 checksum string.
    """
    df.to_csv(filepath, index=False)
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()

def save_processed_data(df: pd.DataFrame, filename: str) -> Path:
    """
    Save processed data to disk.
    
    Args:
        df: DataFrame to save.
        filename: Name of the output file.
        
    Returns:
        Path to the saved file.
    """
    PROCESSED_DATA_DIR.mkdir(parents=True, exist_ok=True)
    filepath = PROCESSED_DATA_DIR / filename
    checksum = calculate_checksum(df, filepath)
    logger.info(f"Saved processed data to {filepath} (Checksum: {checksum})")
    return filepath

def run_orchestration() -> Optional[Path]:
    """
    Main orchestration function for data ingestion.
    
    Returns:
        Path to the merged dataset, or None if failed.
    """
    start_time = time.time()
    logger.info("Starting data ingestion orchestration...")
    
    try:
        # 1. Load Data
        personality_df = load_personality_data(BFI_SOURCE_URL)
        listening_df = load_listening_data(LASTFM_SOURCE_URL)
        
        # 2. Merge
        merged_df = merge_dataframes(personality_df, listening_df)
        
        # 3. Filter
        merged_df = filter_active_users(merged_df)
        
        # 4. Standardize Genres
        merged_df = apply_genre_standardization(merged_df)
        
        # 5. Preprocess (Impute Missing)
        merged_df = preprocess_merged_data(merged_df)
        
        # 6. Save
        output_path = save_processed_data(merged_df, "merged_data.csv")
        
        elapsed = time.time() - start_time
        logger.info(f"Orchestration completed in {elapsed:.2f}s")
        return output_path
        
    except Exception as e:
        logger.error(f"Orchestration failed: {e}")
        return None

def main():
    """Entry point for script execution."""
    result = run_orchestration()
    if result:
        print(f"Success: {result}")
    else:
        print("Failed to complete data ingestion.")
        exit(1)

if __name__ == "__main__":
    main()
