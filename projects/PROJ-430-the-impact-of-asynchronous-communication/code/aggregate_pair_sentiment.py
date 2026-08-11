"""
Aggregate pair-level sentiment scores to generate data/derived/pair_sentiment.parquet.

This task implements T021b:
- Input: data/derived/timestamp_features.parquet (from T012) and raw event text.
- Output: data/derived/pair_sentiment.parquet with pair_id, mean_sentiment, count.
- Logic: Group comments by pair_id and calculate mean compound score.
"""
import json
import logging
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq

# Import from existing modules
from config import get_config, ensure_directories_exist
from utils.logger import get_logger

# Initialize logger
logger = get_logger(__name__)

def load_timestamp_features(config: Dict[str, Any]) -> pd.DataFrame:
    """Load timestamp features from the derived parquet file."""
    input_path = config.get("timestamp_features_path", "data/derived/timestamp_features.parquet")
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Timestamp features file not found: {path}")
    
    logger.info(f"Loading timestamp features from {path}")
    df = pd.read_parquet(path)
    logger.info(f"Loaded {len(df)} rows of timestamp features")
    return df

def load_raw_events(config: Dict[str, Any]) -> pd.DataFrame:
    """Load raw events from the JSON file."""
    input_path = config.get("raw_events_path", "data/raw/events.json")
    path = Path(input_path)
    
    if not path.exists():
        raise FileNotFoundError(f"Raw events file not found: {path}")
    
    logger.info(f"Loading raw events from {path}")
    with open(path, 'r', encoding='utf-8') as f:
        events = json.load(f)
    
    df = pd.DataFrame(events)
    logger.info(f"Loaded {len(df)} raw events")
    return df

def extract_pair_sentiment(timestamp_df: pd.DataFrame, events_df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract sentiment scores for each pair from the events and aggregate.
    
    This function:
    1. Joins timestamp features with raw events on project_id and pair_id
    2. Calculates mean sentiment (compound score) per pair
    3. Counts the number of interactions per pair
    
    Note: Assumes events_df has a 'sentiment_compound' column from prior sentiment analysis.
    If not present, we must compute it here or from a separate sentiment file.
    For T021b, we assume sentiment has been calculated and is available in the events.
    """
    # Check if sentiment column exists in events
    if 'sentiment_compound' not in events_df.columns:
        # If not, we need to load sentiment from a separate source or calculate it.
        # For this implementation, we'll assume the sentiment was computed in T019/T020
        # and stored in a separate file or added to events.
        # If missing, we raise an error to fail loudly (per constraint 9).
        raise ValueError(
            "sentiment_compound column not found in events. "
            "Ensure T019/T020 have been run and sentiment is available."
        )
    
    # Merge timestamp features with events to get sentiment per pair
    # We need to join on project_id and pair_id
    merged = pd.merge(
        timestamp_df,
        events_df[['project_id', 'pair_id', 'sentiment_compound', 'comment_id']],
        on=['project_id', 'pair_id'],
        how='inner'
    )
    
    logger.info(f"Merged data has {len(merged)} rows")
    
    # Group by pair_id (and project_id if needed) to calculate mean sentiment and count
    # The task requires: pair_id, mean_sentiment, count
    # We'll aggregate by pair_id, but keep project_id for context if needed
    aggregation = merged.groupby(['project_id', 'pair_id']).agg(
        mean_sentiment=('sentiment_compound', 'mean'),
        count=('comment_id', 'count')
    ).reset_index()
    
    # If pair_id is not unique across projects, we might need a composite key
    # For now, we'll assume pair_id is unique per project or we use project_id + pair_id
    # The output schema requested: pair_id, mean_sentiment, count
    # We'll include project_id as well for clarity, but the task specifies pair_id
    
    # Rename columns to match expected output
    result = aggregation[['project_id', 'pair_id', 'mean_sentiment', 'count']]
    
    logger.info(f"Aggregated sentiment for {len(result)} pairs")
    return result

def merge_and_fill(timestamp_df: pd.DataFrame, sentiment_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge timestamp features with sentiment data and fill missing values.
    
    This ensures all pairs have a sentiment score, filling with 0 if missing.
    """
    # Perform a left join to keep all pairs from timestamp features
    merged = pd.merge(
        timestamp_df,
        sentiment_df,
        on=['project_id', 'pair_id'],
        how='left'
    )
    
    # Fill missing sentiment scores with 0 (neutral)
    merged['mean_sentiment'] = merged['mean_sentiment'].fillna(0)
    merged['count'] = merged['count'].fillna(0).astype(int)
    
    return merged

def run_aggregate_pair_sentiment(config: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
    """
    Main pipeline for aggregating pair-level sentiment scores.
    
    Steps:
    1. Load timestamp features (from T012)
    2. Load raw events (with sentiment computed)
    3. Extract and aggregate sentiment by pair
    4. Merge and fill missing values
    5. Persist to parquet
    
    Returns:
        DataFrame with pair sentiment data
    """
    if config is None:
        config = get_config()
    
    # Ensure output directory exists
    output_path = Path(config.get("pair_sentiment_path", "data/derived/pair_sentiment.parquet"))
    ensure_directories_exist([output_path.parent])
    
    logger.info("Starting pair sentiment aggregation pipeline")
    
    # Load data
    timestamp_df = load_timestamp_features(config)
    events_df = load_raw_events(config)
    
    # Extract sentiment
    sentiment_df = extract_pair_sentiment(timestamp_df, events_df)
    
    # Merge and fill (optional, depending on use case)
    # For T021b, we just need the aggregated sentiment
    final_df = sentiment_df
    
    # Persist to parquet
    logger.info(f"Writing pair sentiment to {output_path}")
    final_df.to_parquet(output_path, index=False)
    
    logger.info(f"Successfully wrote {len(final_df)} rows to {output_path}")
    return final_df

def main():
    """Entry point for running the aggregation pipeline."""
    try:
        config = get_config()
        result = run_aggregate_pair_sentiment(config)
        logger.info("Pair sentiment aggregation completed successfully")
    except Exception as e:
        logger.error(f"Pair sentiment aggregation failed: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
