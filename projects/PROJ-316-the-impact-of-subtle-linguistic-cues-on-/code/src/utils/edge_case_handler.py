"""
Edge case handler for detecting and logging exclusions based on FR-006 and FR-007.

FR-006: Exclude conversations with fewer than 5 words.
FR-007: Exclude records with missing authenticity ratings.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# Ensure log directory exists
LOG_DIR = Path("data/derived")
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOG_FILE = LOG_DIR / "exclusion_log.csv"

def log_exclusions(exclusions: List[Dict[str, Any]]) -> None:
    """
    Log excluded records to a CSV file and print summary to logger.
    
    Args:
        exclusions: List of dictionaries containing exclusion details
            (conversation_id, reason, original_data)
    """
    if not exclusions:
        logger.info("No records excluded.")
        return

    # Convert to DataFrame
    df_exclusions = pd.DataFrame(exclusions)
    
    # Append to existing log if it exists
    if LOG_FILE.exists():
        existing_df = pd.read_csv(LOG_FILE)
        combined_df = pd.concat([existing_df, df_exclusions], ignore_index=True)
    else:
        combined_df = df_exclusions
    
    # Save to CSV
    combined_df.to_csv(LOG_FILE, index=False)
    
    # Log summary
    exclusion_counts = df_exclusions['reason'].value_counts()
    logger.info(f"Excluded {len(exclusions)} records:")
    for reason, count in exclusion_counts.items():
        logger.info(f"  - {reason}: {count}")

def detect_empty_or_short_texts(df: pd.DataFrame, text_column: str = 'text', min_words: int = 5) -> List[Dict[str, Any]]:
    """
    Detect conversations with empty or short texts (<5 words).
    
    Args:
        df: DataFrame containing conversation data
        text_column: Name of the column containing text data
        min_words: Minimum number of words required (default: 5)
    
    Returns:
        List of dictionaries with exclusion details
    """
    exclusions = []
    
    if text_column not in df.columns:
        logger.warning(f"Column '{text_column}' not found in DataFrame. Skipping text length check.")
        return exclusions
    
    for idx, row in df.iterrows():
        text = row.get(text_column, "")
        
        if pd.isna(text) or str(text).strip() == "":
            exclusions.append({
                'conversation_id': row.get('conversation_id', f'row_{idx}'),
                'reason': 'empty_text',
                'original_data': str(text)[:100]  # Truncate for log
            })
        else:
            word_count = len(str(text).split())
            if word_count < min_words:
                exclusions.append({
                    'conversation_id': row.get('conversation_id', f'row_{idx}'),
                    'reason': f'short_text_{word_count}_words',
                    'original_data': str(text)[:100]
                })
    
    return exclusions

def detect_missing_ratings(df: pd.DataFrame, rating_column: str = 'authenticity_score') -> List[Dict[str, Any]]:
    """
    Detect records with missing authenticity ratings.
    
    Args:
        df: DataFrame containing conversation and rating data
        rating_column: Name of the column containing ratings
    
    Returns:
        List of dictionaries with exclusion details
    """
    exclusions = []
    
    if rating_column not in df.columns:
        logger.warning(f"Column '{rating_column}' not found in DataFrame. Skipping rating check.")
        return exclusions
    
    for idx, row in df.iterrows():
        rating = row.get(rating_column)
        
        if pd.isna(rating):
            exclusions.append({
                'conversation_id': row.get('conversation_id', f'row_{idx}'),
                'reason': 'missing_rating',
                'original_data': None
            })
    
    return exclusions

def handle_edge_cases(
    df: pd.DataFrame, 
    text_column: str = 'text', 
    rating_column: str = 'authenticity_score',
    min_words: int = 5,
    log_to_file: bool = True
) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
    """
    Main function to handle all edge cases: empty/short texts and missing ratings.
    
    Args:
        df: Input DataFrame
        text_column: Column name for text data
        rating_column: Column name for rating data
        min_words: Minimum word count threshold
        log_to_file: Whether to write exclusions to CSV log file
    
    Returns:
        Tuple of (filtered DataFrame, list of all exclusions)
    """
    all_exclusions = []
    
    # Check for empty/short texts
    text_exclusions = detect_empty_or_short_texts(df, text_column, min_words)
    all_exclusions.extend(text_exclusions)
    
    # Check for missing ratings
    rating_exclusions = detect_missing_ratings(df, rating_column)
    all_exclusions.extend(rating_exclusions)
    
    # Create mask for valid records
    valid_mask = pd.Series(True, index=df.index)
    
    # Filter by text length
    if text_column in df.columns:
        text_lengths = df[text_column].apply(lambda x: len(str(x).split()) if pd.notna(x) and str(x).strip() != "" else 0)
        valid_mask &= (text_lengths >= min_words)
    
    # Filter by rating presence
    if rating_column in df.columns:
        valid_mask &= df[rating_column].notna()
    
    filtered_df = df[valid_mask].reset_index(drop=True)
    
    # Log exclusions
    if log_to_file and all_exclusions:
        log_exclusions(all_exclusions)
    
    return filtered_df, all_exclusions

def get_exclusion_summary() -> Optional[pd.DataFrame]:
    """
    Load and return the exclusion log if it exists.
    
    Returns:
        DataFrame with exclusion details or None if log doesn't exist
    """
    if LOG_FILE.exists():
        return pd.read_csv(LOG_FILE)
    return None
