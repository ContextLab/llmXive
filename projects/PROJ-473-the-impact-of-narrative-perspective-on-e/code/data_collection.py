"""
Data collection and validation logic for reader response data.
Implements T031 and supports T028 tests.
"""
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import json
import os

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

def aggregate_reader_scores(stories: List[Dict[str, Any]], responses: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregates perspective features and reader response scores into a single aligned dataset.
    
    This function implements T032. It consumes:
    - perspective_features.json (parsed into `stories` list of dicts)
    - reader_response.csv (loaded into `responses` DataFrame)
    
    It produces:
    - data/processed/aligned_dataset.csv with columns:
      story_id, perspective_score, empathy_score, moral_judgement_score
    
    Args:
        stories: List of dictionaries loaded from perspective_features.json.
                 Each dict must contain at least 'story_id' and 'perspective_score'.
        responses: DataFrame loaded from reader_response.csv.
                   Must contain 'story_id', 'empathy_score', and 'moral_judgement_score'.
    
    Returns:
        DataFrame containing the aligned dataset.
    
    Raises:
        FileNotFoundError: If required input files are missing (checked by caller).
        ValueError: If required columns are missing from inputs.
    """
    if not stories:
        raise ValueError("The 'stories' list is empty. Cannot aggregate without perspective features.")
    
    if responses.empty:
        raise ValueError("The 'responses' DataFrame is empty. Cannot aggregate without reader responses.")
    
    # Convert stories list to DataFrame
    perspectives_df = pd.DataFrame(stories)
    
    # Validate required columns in perspectives
    required_perspective_cols = ['story_id', 'perspective_score']
    missing_perspective_cols = [col for col in required_perspective_cols if col not in perspectives_df.columns]
    if missing_perspective_cols:
        raise ValueError(f"Missing columns in perspective features: {missing_perspective_cols}")
    
    # Validate required columns in responses
    required_response_cols = ['story_id', 'empathy_score', 'moral_judgement_score']
    missing_response_cols = [col for col in required_response_cols if col not in responses.columns]
    if missing_response_cols:
        raise ValueError(f"Missing columns in reader responses: {missing_response_cols}")
    
    # Select only required columns from responses to avoid duplication
    responses_clean = responses[required_response_cols].copy()
    
    # Merge on story_id
    # Using inner join to ensure we only keep stories that have both perspective and response data
    aligned_df = pd.merge(
        perspectives_df[['story_id', 'perspective_score']],
        responses_clean,
        on='story_id',
        how='inner'
    )
    
    if aligned_df.empty:
        logger.warning("Merge resulted in an empty DataFrame. No matching story_ids found between inputs.")
        return aligned_df
    
    # Ensure numeric types for aggregation
    aligned_df['perspective_score'] = pd.to_numeric(aligned_df['perspective_score'], errors='coerce')
    aligned_df['empathy_score'] = pd.to_numeric(aligned_df['empathy_score'], errors='coerce')
    aligned_df['moral_judgement_score'] = pd.to_numeric(aligned_df['moral_judgement_score'], errors='coerce')
    
    # Drop rows with NaN in critical columns
    aligned_df = aligned_df.dropna(subset=['perspective_score', 'empathy_score', 'moral_judgement_score'])
    
    # Log aggregation stats
    logger.info(f"Aggregation complete: {len(aligned_df)} stories aligned.")
    logger.debug(f"Alignment stats - Mean Perspective: {aligned_df['perspective_score'].mean():.3f}, "
                 f"Mean Empathy: {aligned_df['empathy_score'].mean():.3f}")
    
    # Ensure output directory exists
    output_path = "data/processed/aligned_dataset.csv"
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Write to CSV
    aligned_df.to_csv(output_path, index=False)
    logger.info(f"Aligned dataset written to {output_path}")
    
    return aligned_df
