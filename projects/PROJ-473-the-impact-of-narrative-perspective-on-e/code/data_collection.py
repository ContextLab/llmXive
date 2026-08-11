import pandas as pd
import numpy as np
from typing import List, Dict, Any, Tuple, Optional
import logging
import json
import os

logger = logging.getLogger(__name__)

def validate_and_clean_responses(raw_data: pd.DataFrame) -> pd.DataFrame:
    """
    Validate and clean reader response data.
    - Check for attention checks
    - Flag invalid responses
    - Remove rows with missing critical fields
    """
    required_cols = ['story_id', 'empathy_score', 'moral_judgement_score', 'participant_id']
    missing_cols = [c for c in required_cols if c not in raw_data.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns: {missing_cols}")

    # Drop rows with missing critical scores
    initial_count = len(raw_data)
    cleaned = raw_data.dropna(subset=['empathy_score', 'moral_judgement_score'])
    dropped = initial_count - len(cleaned)
    if dropped > 0:
        logger.warning(f"Dropped {dropped} rows with missing scores.")

    # Simple attention check: if empathy_score is exactly 0 or 100 (assuming 0-100 scale)
    # and moral_judgement_score is identical, flag as suspicious (optional logic)
    # For now, we just ensure types are numeric
    cleaned['empathy_score'] = pd.to_numeric(cleaned['empathy_score'], errors='coerce')
    cleaned['moral_judgement_score'] = pd.to_numeric(cleaned['moral_judgement_score'], errors='coerce')
    
    cleaned = cleaned.dropna(subset=['empathy_score', 'moral_judgement_score'])

    return cleaned.reset_index(drop=True)

def aggregate_reader_scores(stories: List[Dict], responses: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate reader scores per story.
    Input: 
      - stories: List of dicts from perspective_features.json containing story_id and perspective_score
      - responses: DataFrame with story_id, empathy_score, moral_judgement_score
    Output:
      - DataFrame with story_id, perspective_score, empathy_score (mean), moral_judgement_score (mean)
    """
    if not stories:
        logger.warning("No stories provided for aggregation.")
        return pd.DataFrame()

    # Create DataFrame from stories
    stories_df = pd.DataFrame(stories)
    required_story_cols = ['story_id', 'narrator_distance_score']
    if not all(c in stories_df.columns for c in required_story_cols):
        raise ValueError(f"Stories data missing required columns: {required_story_cols}")
    
    # Rename narrator_distance_score to perspective_score to match spec
    stories_df = stories_df.rename(columns={'narrator_distance_score': 'perspective_score'})
    stories_df = stories_df[['story_id', 'perspective_score']]

    # Validate responses
    cleaned_responses = validate_and_clean_responses(responses)

    # Group responses by story_id and calculate means
    aggregated_responses = cleaned_responses.groupby('story_id').agg({
        'empathy_score': 'mean',
        'moral_judgement_score': 'mean'
    }).reset_index()

    # Merge with stories
    # Use outer join to see if we have all stories, but spec implies we align on existing
    aligned = pd.merge(stories_df, aggregated_responses, on='story_id', how='inner')

    if aligned.empty:
        logger.warning("No matching story_ids found between stories and responses.")
    else:
        logger.info(f"Aligned {len(aligned)} stories with reader responses.")

    return aligned

def run_aggregation_pipeline(features_path: str, responses_path: str, output_path: str):
    """
    Run the full aggregation pipeline:
    1. Load perspective features
    2. Load reader responses
    3. Aggregate scores
    4. Write aligned_dataset.csv
    """
    logger.info(f"Loading perspective features from {features_path}")
    if not os.path.exists(features_path):
        raise FileNotFoundError(f"Features file not found: {features_path}")
    
    with open(features_path, 'r') as f:
        stories = json.load(f)

    logger.info(f"Loading reader responses from {responses_path}")
    if not os.path.exists(responses_path):
        raise FileNotFoundError(f"Responses file not found: {responses_path}")
    
    responses = pd.read_csv(responses_path)

    logger.info("Aggregating scores...")
    aligned_df = aggregate_reader_scores(stories, responses)

    # Ensure columns are in the exact order required by T033
    # Schema: story_id, perspective_score, empathy_score, moral_judgement_score
    target_cols = ['story_id', 'perspective_score', 'empathy_score', 'moral_judgement_score']
    if all(c in aligned_df.columns for c in target_cols):
        aligned_df = aligned_df[target_cols]
    else:
        logger.warning(f"Aligned dataset missing columns. Found: {aligned_df.columns.tolist()}")

    # Write output
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    aligned_df.to_csv(output_path, index=False)
    logger.info(f"Aligned dataset written to {output_path}")
    
    # Log column verification
    actual_cols = list(aligned_df.columns)
    if actual_cols == target_cols:
        logger.info("Verification: Output CSV contains required columns in correct order.")
    else:
        logger.warning(f"Verification: Column mismatch. Expected {target_cols}, got {actual_cols}")

    return aligned_df
