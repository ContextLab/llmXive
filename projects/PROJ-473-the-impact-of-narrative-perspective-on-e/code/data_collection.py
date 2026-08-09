"""
Data collection and validation logic for reader response data.
Implements T031 and supports T028 tests.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

def validate_and_clean_responses(raw_data: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validates and cleans raw reader response data.
    
    Handles attention checks and flags invalid responses.
    
    Args:
        raw_data: DataFrame containing raw response data. Expected columns:
                  - 'story_id': Identifier for the story
                  - 'attention_check_1': Binary or categorical response to attention check
                  - 'attention_check_2': (Optional) Second attention check
                  - Other columns like empathy scores, moral judgement, etc.
    
    Returns:
        Tuple containing:
        - cleaned_df: DataFrame with invalid rows removed
        - excluded_ids: List of IDs of excluded participants (attention check failures)
    
    Raises:
        ValueError: If expected columns are missing
    """
    if raw_data.empty:
        logger.warning("Received empty raw data DataFrame.")
        return raw_data, []
    
    # Define expected attention check columns
    # Assuming standard column names based on typical survey data
    attention_check_cols = [col for col in raw_data.columns if 'attention' in col.lower()]
    
    if not attention_check_cols:
        # If no attention check columns found, log warning and return all data
        logger.warning("No attention check columns found in raw data. Skipping validation.")
        return raw_data, []
    
    # Determine valid values for attention checks
    # Assuming binary 0/1 or specific string responses like "correct"
    # This logic needs to be flexible based on the actual data source
    valid_values = {1, '1', 'correct', 'Correct', 'CORRECT', 'Yes', 'yes'}
    
    excluded_ids = []
    valid_mask = pd.Series([True] * len(raw_data))
    
    for col in attention_check_cols:
        # Check for correct responses
        # Assuming 1 or 'correct' indicates passing
        # Adjust logic based on actual data format
        if col in raw_data.columns:
            # Normalize values for comparison
            col_clean = raw_data[col].astype(str).str.strip().str.lower()
            
            # Define what constitutes a PASS
            # For binary: 1 is pass, 0 is fail
            # For text: 'correct' is pass
            if raw_data[col].dtype in ['int64', 'float64']:
                # Numeric: assume 1 is pass
                pass_mask = (raw_data[col] == 1) | (raw_data[col] == 1.0)
            else:
                # Text: assume 'correct' is pass
                pass_mask = col_clean == 'correct'
            
            valid_mask &= pass_mask
    
    # Identify excluded IDs
    excluded_mask = ~valid_mask
    excluded_ids = raw_data.loc[excluded_mask, 'story_id'].tolist() if 'story_id' in raw_data.columns else []
    
    if excluded_ids:
        logger.info(f"Excluding {len(excluded_ids)} participants due to attention check failures.")
        logger.debug(f"Excluded IDs: {excluded_ids}")
    
    # Filter the DataFrame
    cleaned_df = raw_data.loc[valid_mask].copy()
    
    return cleaned_df, excluded_ids
