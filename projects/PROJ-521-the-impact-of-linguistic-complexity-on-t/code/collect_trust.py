import os
import sys
import json
import csv
import logging
import hashlib
from typing import List, Dict, Any, Optional
import pandas as pd
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
DATA_RAW_DIR = Path("data/raw")
DATA_PROCESSED_DIR = Path("data/processed")
GENERATED_TEXT_FILE = DATA_RAW_DIR / "generated_text.csv"
RAW_RESPONSES_FILE = DATA_RAW_DIR / "trust_responses.csv"
CLEANED_RESPONSES_FILE = DATA_PROCESSED_DIR / "cleaned_responses.csv"

def load_generated_text_samples() -> pd.DataFrame:
    """
    Load the generated text samples from the raw data CSV.
    Returns a DataFrame with text_id and raw_text columns.
    """
    if not GENERATED_TEXT_FILE.exists():
        logger.error(f"Generated text file not found: {GENERATED_TEXT_FILE}")
        raise FileNotFoundError(f"Generated text file not found: {GENERATED_TEXT_FILE}")
    
    logger.info(f"Loading generated text samples from {GENERATED_TEXT_FILE}")
    df = pd.read_csv(GENERATED_TEXT_FILE)
    
    required_cols = ['text_id', 'raw_text']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in generated text: {missing_cols}")
    
    return df[['text_id', 'raw_text']]

def fetch_raw_prolific_responses() -> pd.DataFrame:
    """
    Fetch raw responses from Prolific API.
    For this implementation, we assume the raw responses have already been 
    downloaded and saved to trust_responses.csv by a previous step.
    """
    if not RAW_RESPONSES_FILE.exists():
        logger.error(f"Raw responses file not found: {RAW_RESPONSES_FILE}")
        raise FileNotFoundError(f"Raw responses file not found: {RAW_RESPONSES_FILE}")
    
    logger.info(f"Loading raw responses from {RAW_RESPONSES_FILE}")
    df = pd.read_csv(RAW_RESPONSES_FILE)
    
    required_cols = ['participant_id', 'text_sample_id', 'trust_rating', 'attention_check_status']
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in raw responses: {missing_cols}")
    
    return df

def process_raw_responses(df: pd.DataFrame) -> pd.DataFrame:
    """
    Process raw responses to extract and clean data.
    - Filter out participants who failed attention checks
    - Filter out participants who straight-lined (all 1s or all 5s)
    - Ensure trust_rating is within 1-5 range
    """
    logger.info("Processing raw responses...")
    
    # Ensure trust_rating is numeric
    df['trust_rating'] = pd.to_numeric(df['trust_rating'], errors='coerce')
    df = df.dropna(subset=['trust_rating'])
    
    # Filter valid trust ratings (1-5)
    df = df[(df['trust_rating'] >= 1) & (df['trust_rating'] <= 5)]
    
    # Filter out failed attention checks
    # Assuming attention_check_status is 'pass' for valid, 'fail' for invalid
    df = df[df['attention_check_status'].str.lower() == 'pass']
    
    logger.info(f"After attention check filtering: {len(df)} responses")
    
    # Detect straight-lining: participants who gave all 1s or all 5s
    # Group by participant_id and check if all ratings are the same extreme
    participant_stats = df.groupby('participant_id')['trust_rating'].agg(['min', 'max', 'count']).reset_index()
    
    # Identify straight-liners: all 1s (min=1, max=1) or all 5s (min=5, max=5)
    straight_liners = participant_stats[
        ((participant_stats['min'] == 1) & (participant_stats['max'] == 1)) |
        ((participant_stats['min'] == 5) & (participant_stats['max'] == 5))
    ]['participant_id'].unique()
    
    logger.info(f"Detected {len(straight_liners)} straight-lining participants")
    
    # Filter out straight-liners
    df_cleaned = df[~df['participant_id'].isin(straight_liners)]
    
    logger.info(f"After straight-lining filtering: {len(df_cleaned)} responses")
    
    # Ensure required columns are present and ordered
    output_cols = ['participant_id', 'text_sample_id', 'trust_rating', 'attention_check_status']
    df_cleaned = df_cleaned[output_cols]
    
    return df_cleaned

def save_processed_responses(df: pd.DataFrame, output_path: Path) -> None:
    """
    Save cleaned responses to the processed data directory.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Saving cleaned responses to {output_path}")
    df.to_csv(output_path, index=False)
    
    # Log summary statistics
    logger.info(f"Total cleaned responses: {len(df)}")
    logger.info(f"Unique participants: {df['participant_id'].nunique()}")
    logger.info(f"Unique text samples: {df['text_sample_id'].nunique()}")
    logger.info(f"Trust rating distribution:\n{df['trust_rating'].value_counts().sort_index()}")

def main() -> int:
    """
    Main entry point for data cleaning pipeline.
    """
    try:
        # Load raw responses
        raw_df = fetch_raw_prolific_responses()
        
        # Process and clean data
        cleaned_df = process_raw_responses(raw_df)
        
        # Save cleaned data
        save_processed_responses(cleaned_df, CLEANED_RESPONSES_FILE)
        
        logger.info("Data cleaning completed successfully.")
        return 0
        
    except Exception as e:
        logger.error(f"Data cleaning failed: {str(e)}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
