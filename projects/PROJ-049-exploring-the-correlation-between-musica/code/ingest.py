"""
Data Ingestion and Preprocessing Pipeline for Music-Personality Study.

Orchestrates the download of real data (BFI-2, Last.fm) with timeout handling.
Falls back to synthetic data if real data is unavailable.
Performs merging, filtering, mapping, and preprocessing.
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
from requests.exceptions import Timeout, HTTPError, RequestException

# Import from existing project API
from utils import setup_logging, safe_http_request, download_file
from mapping import load_genre_lookup, apply_genre_mapping
from synthetic_data import generate_synthetic_data

logger = setup_logging()

# Constants
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
OUTPUT_PATH = DATA_PROCESSED_DIR / "merged_data.csv"

# Real data source URLs (Simulated for this task as per project constraints, 
# but implemented with real HTTP logic as requested)
# Note: In a real production environment, these would be the actual BFI-2/Last.fm endpoints.
# Since specific public APIs for these exact datasets are not universally standardized 
# without authentication or specific IDs, we attempt to fetch from a known research data repo 
# or fall back. For this implementation, we simulate the "Real Source" attempt logic 
# against a placeholder that represents the real source.
REAL_DATA_URLS = {
    "personality": "https://raw.githubusercontent.com/psychosocial-data/bfi2-sample/main/data.csv",
    "listening": "https://raw.githubusercontent.com/music-research/lastfm-sample/main/data.csv"
}

TIMEOUT_SECONDS = 10

def load_personality_data(url: Optional[str] = None) -> pd.DataFrame:
    """
    Load personality data (BFI-2) from a URL or local file.
    If URL is provided, attempts to fetch. If fails, raises exception.
    """
    if url:
        try:
            logger.info(f"Attempting to download personality data from {url}")
            # Use safe_http_request wrapper if available, else direct requests
            response = safe_http_request(url, timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                # Parse CSV from text
                df = pd.read_csv(pd.io.common.StringIO(response.text))
                logger.info(f"Successfully loaded personality data: {len(df)} rows")
                return df
            else:
                raise HTTPError(f"HTTP {response.status_code} for personality data")
        except (Timeout, RequestException, HTTPError) as e:
            logger.error(f"Failed to download personality data: {e}")
            raise
    else:
        # Fallback to local if URL not provided (though orchestration usually provides URL)
        local_path = DATA_RAW_DIR / "personality.csv"
        if local_path.exists():
            return pd.read_csv(local_path)
        raise FileNotFoundError("No personality data found locally or via URL.")

def load_listening_data(url: Optional[str] = None) -> pd.DataFrame:
    """
    Load listening data (Last.fm) from a URL or local file.
    """
    if url:
        try:
            logger.info(f"Attempting to download listening data from {url}")
            response = safe_http_request(url, timeout=TIMEOUT_SECONDS)
            if response.status_code == 200:
                df = pd.read_csv(pd.io.common.StringIO(response.text))
                logger.info(f"Successfully loaded listening data: {len(df)} rows")
                return df
            else:
                raise HTTPError(f"HTTP {response.status_code} for listening data")
        except (Timeout, RequestException, HTTPError) as e:
            logger.error(f"Failed to download listening data: {e}")
            raise
    else:
        local_path = DATA_RAW_DIR / "listening.csv"
        if local_path.exists():
            return pd.read_csv(local_path)
        raise FileNotFoundError("No listening data found locally or via URL.")

def merge_dataframes(personality_df: pd.DataFrame, listening_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge personality and listening data on user_id.
    """
    # Ensure column names match for merge
    # Assuming personality has 'user_id' and listening has 'user_id'
    if 'user_id' not in personality_df.columns:
        # Try to infer if needed, but standard schema implies user_id
        raise ValueError("Personality data must contain 'user_id' column.")
    if 'user_id' not in listening_df.columns:
        raise ValueError("Listening data must contain 'user_id' column.")
    
    merged = pd.merge(personality_df, listening_df, on='user_id', how='inner')
    logger.info(f"Merged data shape: {merged.shape}")
    return merged

def filter_active_users(df: pd.DataFrame, min_minutes: int = 0) -> pd.DataFrame:
    """
    Exclude users with zero (or below threshold) listening minutes.
    """
    if 'listening_minutes' not in df.columns:
        # Handle case where minutes might be named differently or missing
        logger.warning("Column 'listening_minutes' not found. Skipping filter.")
        return df
    
    initial_count = len(df)
    df = df[df['listening_minutes'] > min_minutes]
    logger.info(f"Filtered active users: {initial_count} -> {len(df)}")
    return df

def apply_genre_standardization(df: pd.DataFrame) -> pd.DataFrame:
    """
    Map raw genre tags to standard categories using contracts/genre_lookup.yaml.
    """
    if 'raw_genres' not in df.columns:
        logger.warning("Column 'raw_genres' not found. Skipping genre mapping.")
        return df
    
    return apply_genre_mapping(df)

def preprocess_merged_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Handle missing demographic data:
    - Numeric: impute with median
    - Categorical: impute with mode
    - Exclude rows if critical columns missing (optional, here we impute)
    """
    # Identify numeric and categorical columns (excluding user_id)
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    
    # Impute numeric with median
    for col in numeric_cols:
        if df[col].isnull().any():
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)
            logger.info(f"Imputed {col} (numeric) with median: {median_val}")
    
    # Impute categorical with mode
    for col in categorical_cols:
        if df[col].isnull().any():
            mode_val = df[col].mode()[0] if not df[col].mode().empty else 'Unknown'
            df[col] = df[col].fillna(mode_val)
            logger.info(f"Imputed {col} (categorical) with mode: {mode_val}")
    
    return df

def save_processed_data(df: pd.DataFrame, output_path: str) -> str:
    """
    Save the processed dataframe to CSV and return the checksum.
    """
    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)
    
    df.to_csv(output_path, index=False)
    
    # Calculate checksum
    with open(output_path, "rb") as f:
        content = f.read()
        checksum = hashlib.md5(content).hexdigest()
    
    logger.info(f"Saved processed data to {output_path}")
    logger.info(f"Checksum (MD5): {checksum}")
    return checksum

def run_orchestration() -> pd.DataFrame:
    """
    Main orchestration function:
    1. Attempt to download real data (BFI-2, Last.fm) with timeout.
    2. If HTTP 404/Timeout, log FALLBACK: SYNTHETIC and generate synthetic data.
    3. Apply mapping, merge, filter, preprocess.
    4. Save to data/processed/merged_data.csv with checksum.
    """
    logger.info("Starting Data Ingestion Orchestration (T012)")
    
    df_personality = None
    df_listening = None
    use_real_data = False

    # Step 1: Attempt Real Data Download
    try:
        logger.info("Attempting to fetch REAL data sources...")
        df_personality = load_personality_data(REAL_DATA_URLS["personality"])
        df_listening = load_listening_data(REAL_DATA_URLS["listening"])
        use_real_data = True
        logger.info("Real data fetched successfully.")
    except Exception as e:
        logger.error(f"Real data fetch failed: {e}")
        logger.warning("FALLBACK: SYNTHETIC")
        
        # Step 2: Generate Synthetic Data
        logger.info("Generating synthetic data via code/synthetic_data.py...")
        # Generate and save synthetic data first
        synthetic_df = generate_synthetic_data()
        
        # Split synthetic data back into components for processing pipeline consistency
        # Synthetic data is generated as a single wide dataframe.
        # We need to split it to mimic the pipeline flow or adjust the pipeline.
        # Given the synthetic data structure: demographics + personality + listening
        # We can reconstruct the splits.
        cols_personality = ['extraversion', 'agreeableness', 'conscientiousness', 'emotional_stability', 'open_mindedness']
        cols_demographics = ['age', 'gender', 'country']
        cols_listening = ['user_id', 'raw_genres', 'listening_minutes']
        
        # Reconstruct for the merge step (assuming 1:1 match in synthetic)
        df_personality = synthetic_df[cols_demographics + cols_personality]
        df_listening = synthetic_df[cols_listening]

    # Step 3: Merge
    df_merged = merge_dataframes(df_personality, df_listening)

    # Step 4: Filter Active Users
    df_filtered = filter_active_users(df_merged, min_minutes=0)

    # Step 5: Apply Genre Mapping
    df_mapped = apply_genre_standardization(df_filtered)

    # Step 6: Preprocess (Impute Missing)
    df_final = preprocess_merged_data(df_mapped)

    # Step 7: Save
    checksum = save_processed_data(df_final, str(OUTPUT_PATH))

    logger.info("Orchestration complete.")
    return df_final

if __name__ == "__main__":
    run_orchestration()