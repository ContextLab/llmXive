import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
import logging
import json
import os

def validate_and_clean_responses(responses_path: str) -> pd.DataFrame:
    """
    Validate and clean reader response data.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Validating responses from {responses_path}")
    
    if not os.path.exists(responses_path):
        raise FileNotFoundError(f"Response file not found: {responses_path}")
    
    df = pd.read_csv(responses_path)
    
    # Ensure required columns exist
    required_cols = ['story_id', 'empathy_score', 'moral_judgement_score']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")
    
    # Drop rows with NaN in relevant columns
    df = df.dropna(subset=required_cols)
    
    logger.info(f"Validated {len(df)} responses")
    return df

def aggregate_reader_scores(
    stories_path: str,
    responses_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Aggregate reader response data with story features.
    Joins on story_id to merge perspective_score with empathy_score and moral_judgement_score.
    
    Input:
      stories_path: Path to perspective_features.json (from T016)
      responses_path: Path to aligned_reader_response.csv (from T009.6b)
      output_path: Path to save aligned_dataset.csv
    
    Output:
      DataFrame with columns: story_id, perspective_score, empathy_score, moral_judgement_score
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Aggregating data: {stories_path} + {responses_path} -> {output_path}")
    
    # Load perspective features
    if not os.path.exists(stories_path):
        raise FileNotFoundError(f"Stories file not found: {stories_path}")
        
    with open(stories_path, 'r') as f:
        stories_data = json.load(f)
    
    # Convert to DataFrame
    stories_df = pd.DataFrame(stories_data)
    
    # Ensure story_id column exists
    if 'story_id' not in stories_df.columns:
        raise ValueError("Missing story_id in perspective features")
    
    # Extract perspective_score (narrator_distance_score)
    # The T016 output uses 'narrator_distance_score' as the primary perspective metric
    if 'narrator_distance_score' in stories_df.columns:
        stories_df['perspective_score'] = stories_df['narrator_distance_score']
    elif 'perspective_score' in stories_df.columns:
        pass  # Already exists
    else:
        raise ValueError("Missing perspective score in stories data. Expected 'narrator_distance_score' or 'perspective_score'.")
    
    # Load and validate reader responses
    responses_df = validate_and_clean_responses(responses_path)
    
    # Join on story_id
    merged_df = pd.merge(
        stories_df[['story_id', 'perspective_score']],
        responses_df[['story_id', 'empathy_score', 'moral_judgement_score']],
        on='story_id',
        how='inner'
    )
    
    if len(merged_df) == 0:
        logger.warning("No matching records found between stories and responses. Check story_id alignment.")
    
    logger.info(f"Aggregated {len(merged_df)} records")
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Save to CSV
    merged_df.to_csv(output_path, index=False)
    logger.info(f"Aggregated data saved to {output_path}")
    
    return merged_df

def run_aggregation_pipeline(
    features_path: str,
    responses_path: str,
    output_path: str
) -> pd.DataFrame:
    """
    Run the full aggregation pipeline.
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Running aggregation pipeline: {features_path} + {responses_path} -> {output_path}")
    
    return aggregate_reader_scores(features_path, responses_path, output_path)
