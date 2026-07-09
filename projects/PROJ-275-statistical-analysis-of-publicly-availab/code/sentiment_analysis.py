"""
Sentiment Analysis Module for Movie Review Data.

Implements VADER sentiment scoring for weekly review text and merges
scores into the time-series structure aligned with release dates.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
import nltk
from nltk.sentiment.vader import SentimentIntensityAnalyzer

# Ensure necessary NLTK resources are available
try:
    vader_lexicon_path = nltk.data.find('sentiment/vader_lexicon.zip')
except LookupError:
    nltk.download('vader_lexicon', quiet=True)

from config import get_config, get_dataset_urls, ensure_directories
from entities import TimeSeriesMovie, SentimentScore
from data_ingestion import setup_logger

# Initialize logger
logger = setup_logger('sentiment_analysis')

def compute_vader_sentiment(text: str) -> Dict[str, float]:
    """
    Compute VADER sentiment scores for a given text.

    Args:
        text: The review text to analyze.

    Returns:
        Dictionary containing 'neg', 'neu', 'pos', 'compound' scores.
    """
    if not isinstance(text, str) or not text.strip():
        return {
            'neg': 0.0,
            'neu': 1.0,
            'pos': 0.0,
            'compound': 0.0
        }

    analyzer = SentimentIntensityAnalyzer()
    scores = analyzer.polarity_scores(text)
    return scores

def process_reviews_for_timeseries(
    df: pd.DataFrame,
    text_column: str = 'review_text',
    score_column: str = 'sentiment_score'
) -> pd.DataFrame:
    """
    Process a DataFrame of reviews to compute VADER sentiment scores.

    Args:
        df: DataFrame containing review data, expected to have a text column.
        text_column: Name of the column containing review text.
        score_column: Name of the column to store the compound sentiment score.

    Returns:
        DataFrame with added sentiment scores.
    """
    if df.empty:
        logger.warning("Input DataFrame is empty. Returning empty DataFrame.")
        return df

    logger.info(f"Computing VADER sentiment for {len(df)} reviews...")

    # Apply VADER scoring
    df[score_column] = df[text_column].apply(
        lambda x: compute_vader_sentiment(x).get('compound', 0.0)
    )

    logger.info(f"Sentiment scoring complete. Range: [{df[score_column].min():.4f}, {df[score_column].max():.4f}]")
    return df

def merge_sentiment_to_timeseries(
    timeseries_df: pd.DataFrame,
    review_df: pd.DataFrame,
    time_column: str = 'review_week',
    sentiment_column: str = 'sentiment_score'
) -> pd.DataFrame:
    """
    Merge computed sentiment scores into the time-series structure.

    Assumes review_df has been processed by process_reviews_for_timeseries
    and contains a 'review_week' column (or similar time alignment key)
    and a 'sentiment_score' column.

    Args:
        timeseries_df: The base time-series DataFrame (e.g., from align_timestamps).
                       Expected to have columns like 'movie_id', 'week_number', 'release_date', etc.
        review_df: The DataFrame with reviews and computed sentiment scores.
                   Expected to have 'movie_id', 'week_number' (or 'review_week'), and 'sentiment_score'.
        time_column: The column name in review_df representing the week (default 'review_week').
        sentiment_column: The column name in review_df for the sentiment score.

    Returns:
        A new DataFrame with sentiment scores merged into the time-series structure.
    """
    if timeseries_df.empty:
        logger.warning("Time-series DataFrame is empty. Returning empty DataFrame.")
        return timeseries_df

    if review_df.empty:
        logger.warning("Review DataFrame is empty. Cannot merge sentiment.")
        return timeseries_df

    # Ensure consistent column naming for merge
    # We assume the time-series has 'movie_id' and 'week_number'
    # And review_df has 'movie_id' and 'review_week' (or similar)

    # Normalize time column names for merging
    ts_key = 'week_number' if 'week_number' in timeseries_df.columns else None
    review_key = time_column if time_column in review_df.columns else None

    if not ts_key or not review_key:
        # Fallback: try to infer keys if standard names are missing
        # This is a simple fallback; robust implementation might need more config
        available_ts_cols = [c for c in timeseries_df.columns if 'week' in c.lower()]
        available_review_cols = [c for c in review_df.columns if 'week' in c.lower()]

        if available_ts_cols:
            ts_key = available_ts_cols[0]
        if available_review_cols:
            review_key = available_review_cols[0]

    if not ts_key or not review_key:
        logger.error("Could not identify time keys for merging sentiment to time-series.")
        return timeseries_df

    # Perform the merge
    # We assume review_df might have multiple reviews per week per movie,
    # so we aggregate (mean) the sentiment score per movie-week.
    if review_key in review_df.columns and sentiment_column in review_df.columns:
        review_agg = review_df.groupby(['movie_id', review_key])[sentiment_column].mean().reset_index()
        review_agg.rename(columns={review_key: ts_key, sentiment_column: 'weekly_sentiment_avg'}, inplace=True)
    else:
        logger.error(f"Required columns for aggregation not found in review_df: {review_key}, {sentiment_column}")
        return timeseries_df

    # Merge the aggregated sentiment into the time-series
    merged_df = pd.merge(
        timeseries_df,
        review_agg,
        on=['movie_id', ts_key],
        how='left'
    )

    # Fill NaN sentiment scores (weeks with no reviews) with 0.0 or a neutral value
    # The spec implies a continuous time-series, so filling with 0 (neutral) is reasonable
    merged_df['weekly_sentiment_avg'] = merged_df['weekly_sentiment_avg'].fillna(0.0)

    logger.info(f"Successfully merged sentiment scores. Shape: {merged_df.shape}")
    return merged_df

def main():
    """
    Main entry point for the sentiment analysis pipeline.
    This function loads the pre-processed data (from T012), computes sentiment,
    and saves the result.
    """
    config = get_config()
    ensure_directories()

    # Define paths based on project structure
    processed_dir = Path(config.get('paths', {}).get('processed', 'data/processed'))
    output_file = processed_dir / 'sentiment_scored_timeseries.parquet'
    log_file = Path('data/logs/sentiment_log.txt')

    # Setup file logger for this module
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)

    logger.info("Starting sentiment analysis pipeline (T015)...")

    # Load the time-series data generated by T012
    # T012 output is expected to be 'data/processed/merged_clean.parquet' or similar
    # We need to locate the output of align_timestamps
    input_file = processed_dir / 'merged_clean.parquet'

    if not input_file.exists():
        # Fallback to checking data/processed directly if paths config is different
        input_file = Path('data/processed/merged_clean.parquet')

    if not input_file.exists():
        logger.error(f"Input file not found: {input_file}. Has T012 been completed?")
        sys.exit(1)

    try:
        logger.info(f"Loading data from {input_file}...")
        ts_df = pd.read_parquet(input_file)

        # T012 output structure:
        # It should have 'movie_id', 'week_number', 'release_date', 'opening_weekend_revenue' (static),
        # and potentially review text if it was carried through, OR we need to join with raw reviews.
        # However, T012 description says "align timestamps... create weekly sentiment time-series".
        # If T012 didn't include the text, we must join with the raw reviews.
        # Let's assume T012 output includes the necessary text or we have a separate reviews file.
        # Given the flow: T009 (download) -> T010 (merge) -> T011 (filter) -> T012 (align).
        # T012 likely produces the time-series structure.
        # If the text is not in ts_df, we need to load the raw reviews again.
        # For robustness, let's check if 'review_text' is present.
        
        if 'review_text' not in ts_df.columns:
            # We need to load the raw reviews to compute sentiment if they aren't in the time-series yet.
            # This implies we might need to re-load the merged clean data or a specific reviews file.
            # Let's assume the 'merged_clean.parquet' from T013 (which is the output of T012 logic)
            # contains the necessary data or we need to join with the original review data.
            # To keep T015 independent of T013's specific implementation details regarding text,
            # we will assume the input to T015 is the output of T012 which should have the reviews
            # or we need to fetch the review data again.
            # However, the most efficient way is if T012 output includes the text.
            # If not, we might need to load the raw reviews from the original source or the merged dataset.
            # Let's try to load the raw reviews from the original merged dataset if text is missing.
            
            # Fallback: Load the raw reviews from the initial merged dataset (T010 output)
            # This is a bit of a hack if T012 didn't preserve it, but necessary for T015.
            # Assuming T010 output is 'data/processed/merged_raw.parquet' or similar.
            # Actually, T013 saves 'merged_clean.parquet'. T012 is the logic inside T013.
            # If 'review_text' is missing, we assume we need to join with the raw review data.
            # Let's assume the 'merged_clean.parquet' has 'movie_id' and 'week_number' and 'review_text' (if available).
            # If not, we might need to re-join with the original review data.
            # For now, let's assume the input file has 'review_text'. If not, we raise an error.
            logger.error("Input file does not contain 'review_text' column. T012 must include review text for T015.")
            sys.exit(1)

        # Compute sentiment
        ts_df = process_reviews_for_timeseries(ts_df, text_column='review_text', score_column='sentiment_score')

        # If the time-series structure requires aggregation (e.g., multiple reviews per week),
        # we should aggregate here. T012 might have already done this, but let's ensure.
        # If 'sentiment_score' is already per-week (aggregated), we are good.
        # If it's per-review, we need to group by movie_id and week_number.
        if ts_df.groupby(['movie_id', 'week_number']).size().max() > 1:
            logger.info("Aggregating sentiment scores per movie-week...")
            ts_df = ts_df.groupby(['movie_id', 'week_number', 'release_date', 'opening_weekend_revenue', 'genre'], as_index=False)['sentiment_score'].mean()
            ts_df.rename(columns={'sentiment_score': 'weekly_sentiment_avg'}, inplace=True)
        else:
            ts_df.rename(columns={'sentiment_score': 'weekly_sentiment_avg'}, inplace=True)

        # Save the result
        output_dir = output_file.parent
        output_dir.mkdir(parents=True, exist_ok=True)
        ts_df.to_parquet(output_file, index=False)

        logger.info(f"Sentiment analysis complete. Output saved to {output_file}")
        logger.info(f"Final shape: {ts_df.shape}, Columns: {list(ts_df.columns)}")

    except Exception as e:
        logger.error(f"Error during sentiment analysis: {e}", exc_info=True)
        sys.exit(1)
    finally:
        logger.removeHandler(file_handler)

if __name__ == '__main__':
    main()
