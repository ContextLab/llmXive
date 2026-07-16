"""
Edge case handling utilities.
Detects empty/short texts and missing ratings, logging errors and triggering halts.
"""
import logging
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)

MIN_WORD_THRESHOLD = 5

def log_exclusions(exclusions: List[Dict[str, Any]], log_path: Optional[Path] = None):
    """Logs excluded items to a file or logger."""
    if not exclusions:
        return
    
    message = f"Excluded {len(exclusions)} items due to edge cases:\n"
    for item in exclusions:
        message += f" - ID: {item.get('id', 'N/A')}, Reason: {item.get('reason', 'Unknown')}\n"
    
    logger.warning(message)
    if log_path:
        with open(log_path, 'a') as f:
            f.write(message + "\n")

def detect_empty_or_short_texts(df: pd.DataFrame, text_col: str = 'text_content') -> List[Dict[str, Any]]:
    """
    Detects rows with empty or very short text.
    
    Args:
        df: Input DataFrame.
        text_col: Name of the text column.
        
    Returns:
        List of dicts with 'id' and 'reason'.
    """
    exclusions = []
    if text_col not in df.columns:
        return exclusions
        
    for idx, row in df.iterrows():
        text = str(row[text_col]).strip()
        if not text:
            exclusions.append({'id': row.get('conversation_id', idx), 'reason': 'Empty text'})
        else:
            word_count = len(text.split())
            if word_count < MIN_WORD_THRESHOLD:
                exclusions.append({'id': row.get('conversation_id', idx), 'reason': f'Too short ({word_count} words)'})
    
    return exclusions

def detect_missing_ratings(df: pd.DataFrame, rating_col: str = 'authenticity_score') -> List[Dict[str, Any]]:
    """
    Detects rows with missing ratings.
    
    Args:
        df: Input DataFrame.
        rating_col: Name of the rating column.
        
    Returns:
        List of dicts with 'id' and 'reason'.
    """
    exclusions = []
    if rating_col not in df.columns:
        return exclusions
        
    for idx, row in df.iterrows():
        if pd.isna(row[rating_col]):
            exclusions.append({'id': row.get('conversation_id', idx), 'reason': 'Missing rating'})
    
    return exclusions

def handle_edge_cases(text_df: pd.DataFrame, ratings_df: pd.DataFrame, 
                      log_path: Optional[Path] = None) -> Tuple[pd.DataFrame, pd.DataFrame]:
    """
    Main handler to detect and log edge cases.
    Triggers a pipeline halt (raises exception) if critical issues are found.
    
    Args:
        text_df: DataFrame of text data.
        ratings_df: DataFrame of ratings.
        log_path: Optional path to write exclusion logs.
        
    Returns:
        Tuple of (cleaned_text_df, cleaned_ratings_df)
        
    Raises:
        RuntimeError: If too many exclusions or critical schema issues are found.
    """
    text_exclusions = detect_empty_or_short_texts(text_df)
    rating_exclusions = detect_missing_ratings(ratings_df)
    
    log_exclusions(text_exclusions, log_path)
    log_exclusions(rating_exclusions, log_path)
    
    if text_exclusions:
        logger.warning(f"Detected {len(text_exclusions)} text entries with edge cases.")
        # Filter out excluded IDs from text_df
        excluded_ids = {e['id'] for e in text_exclusions}
        text_df = text_df[~text_df['conversation_id'].isin(excluded_ids)]
        
    if rating_exclusions:
        logger.warning(f"Detected {len(rating_exclusions)} entries with missing ratings.")
        # Filter out excluded IDs from ratings_df
        excluded_ids = {e['id'] for e in rating_exclusions}
        ratings_df = ratings_df[~ratings_df['conversation_id'].isin(excluded_ids)]
        
        # If ALL ratings are missing, halt
        if ratings_df.empty:
            raise RuntimeError("CRITICAL: All ratings were missing or invalid. Pipeline halted.")
            
    return text_df, ratings_df

def get_exclusion_summary(text_exclusions: List[Dict], rating_exclusions: List[Dict]) -> Dict[str, int]:
    """Returns a summary count of exclusions."""
    return {
        'text_empty_or_short': len(text_exclusions),
        'ratings_missing': len(rating_exclusions),
        'total_excluded': len(text_exclusions) + len(rating_exclusions)
    }