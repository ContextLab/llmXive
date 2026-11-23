"""
T019: Implement filtering logic to exclude dialogues missing `quality_rating` or chatbot utterances.

This script loads the merged dataset from T018, filters out dialogues that:
1. Are missing the `quality_rating` field.
2. Have no chatbot utterances (empty bot response list or missing bot text).

It logs the counts of excluded dialogues to `data/raw/exclusions.log` and saves
the filtered dataset to `data/processed/filtered_dialogues.parquet`.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import pandas as pd
import pyarrow.parquet as pq

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/raw/exclusions.log', mode='w')
    ]
)
logger = logging.getLogger(__name__)

# Ensure output directories exist
def ensure_directories():
    Path('data/raw').mkdir(parents=True, exist_ok=True)
    Path('data/processed').mkdir(parents=True, exist_ok=True)

def load_merged_dialogues() -> pd.DataFrame:
    """Load the merged dialogues from T018."""
    input_path = Path('data/processed/merged_dialogues.parquet')
    if not input_path.exists():
        raise FileNotFoundError(
            f"Input file not found: {input_path}. "
            "Please ensure T018 (merge_datasets) has been completed successfully."
        )
    
    logger.info(f"Loading merged dialogues from {input_path}")
    df = pd.read_parquet(input_path)
    logger.info(f"Loaded {len(df)} dialogues")
    return df

def filter_dialogues(df: pd.DataFrame) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Filter dialogues based on:
    1. Presence of 'quality_rating'.
    2. Presence of at least one chatbot utterance.
    
    Returns:
        Tuple of (filtered_df, exclusion_counts)
    """
    initial_count = len(df)
    exclusion_counts = {
        'missing_quality_rating': 0,
        'missing_bot_utterances': 0,
        'total_excluded': 0
    }

    # 1. Filter missing quality_rating
    if 'quality_rating' not in df.columns:
        logger.warning("Column 'quality_rating' not found in dataset. Skipping quality rating filter.")
    else:
        missing_quality = df['quality_rating'].isna()
        count_missing_quality = missing_quality.sum()
        exclusion_counts['missing_quality_rating'] = count_missing_quality
        logger.info(f"Excluding {count_missing_quality} dialogues with missing quality_rating")
        df = df[~missing_quality]

    # 2. Filter missing chatbot utterances
    # Assuming 'bot_utterances' is a list column or 'bot_text' contains the text
    # Based on typical schema, we check for 'bot_utterances' list or 'bot_text'
    
    if 'bot_utterances' in df.columns:
        # Check for empty lists or NaN
        is_empty_bot = df['bot_utterances'].apply(
            lambda x: not isinstance(x, list) or len(x) == 0 or pd.isna(x)
        )
    elif 'bot_text' in df.columns:
        # Check for empty strings or NaN
        is_empty_bot = df['bot_text'].apply(
            lambda x: pd.isna(x) or (isinstance(x, str) and len(x.strip()) == 0)
        )
    else:
        # If neither column exists, we cannot filter by bot utterances
        logger.warning("Neither 'bot_utterances' nor 'bot_text' column found. Skipping bot utterance filter.")
        is_empty_bot = pd.Series([False] * len(df), index=df.index)

    count_missing_bot = is_empty_bot.sum()
    exclusion_counts['missing_bot_utterances'] = count_missing_bot
    logger.info(f"Excluding {count_missing_bot} dialogues with missing/empty bot utterances")
    df = df[~is_empty_bot]

    exclusion_counts['total_excluded'] = initial_count - len(df)
    
    logger.info(f"Final dataset size: {len(df)} (Excluded: {exclusion_counts['total_excluded']})")
    return df, exclusion_counts

def save_results(df: pd.DataFrame, exclusion_counts: Dict[str, int]):
    """Save filtered data and update exclusion log."""
    output_path = Path('data/processed/filtered_dialogues.parquet')
    
    # Save DataFrame
    df.to_parquet(output_path, index=False)
    logger.info(f"Saved filtered dialogues to {output_path}")

    # Update exclusion log with summary
    log_path = Path('data/raw/exclusions.log')
    with open(log_path, 'a') as f:
        f.write("\n--- T019 Filter Summary ---\n")
        for key, value in exclusion_counts.items():
            f.write(f"{key}: {value}\n")
        f.write(f"Total remaining: {len(df)}\n")

def main():
    ensure_directories()
    
    try:
        df = load_merged_dialogues()
        filtered_df, counts = filter_dialogues(df)
        save_results(filtered_df, counts)
        logger.info("T019 completed successfully.")
    except Exception as e:
        logger.error(f"T019 failed: {e}")
        raise

if __name__ == '__main__':
    main()
