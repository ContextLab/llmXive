import os
import json
import logging
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
import pandas as pd
import numpy as np
from scipy.stats import entropy as scipy_entropy
from code.config.settings import get_config

# Configure logging
logger = logging.getLogger(__name__)

def load_processed_data(filepath: str) -> pd.DataFrame:
    """Load a processed CSV/JSONL file into a DataFrame."""
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {filepath}")
    
    if path.suffix == '.csv':
        return pd.read_csv(path)
    elif path.suffix in ['.jsonl', '.json']:
        return pd.read_json(path, lines=path.suffix == '.jsonl')
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def filter_threads_by_reply_count(df: pd.DataFrame, min_replies: int = 5) -> pd.DataFrame:
    """Filter threads to keep only those with >= min_replies."""
    if 'reply_count' not in df.columns:
        logger.warning("Column 'reply_count' not found. Assuming all threads pass filter.")
        return df
    
    filtered = df[df['reply_count'] >= min_replies].copy()
    excluded_count = len(df) - len(filtered)
    logger.info(f"Filtered {excluded_count} threads with < {min_replies} replies.")
    return filtered

def save_exclusion_counts(counts: Dict[str, int], filepath: str) -> None:
    """Save exclusion counts to a JSON file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w') as f:
        json.dump(counts, f, indent=2)
    logger.info(f"Saved exclusion counts to {filepath}")

def run_metrics_exclusion_pipeline(df: pd.DataFrame, min_replies: int = 5) -> Tuple[pd.DataFrame, Dict[str, int]]:
    """
    Run the exclusion pipeline for metrics computation.
    Returns filtered dataframe and exclusion counts.
    """
    total = len(df)
    filtered = filter_threads_by_reply_count(df, min_replies)
    excluded = total - len(filtered)
    
    counts = {
        "total_threads": total,
        "excluded_insufficient_replies": excluded,
        "kept_threads": len(filtered)
    }
    
    return filtered, counts

def compute_shannon_entropy(values: List[float]) -> float:
    """
    Compute Shannon entropy for a list of probabilities or normalized values.
    Handles zero probabilities to avoid log(0).
    """
    if not values or all(v == 0 for v in values):
        return 0.0
    
    # Normalize if not already
    total = sum(values)
    if total == 0:
        return 0.0
    
    probs = [v / total for v in values]
    # Filter out zeros for log calculation
    probs = [p for p in probs if p > 0]
    
    if not probs:
        return 0.0
        
    return float(-sum(p * math.log2(p) for p in probs))

def compute_agreement_proportion(thread_df: pd.DataFrame, sentiment_col: str = 'compound_sentiment') -> float:
    """
    Compute the agreement proportion within a thread.
    Agreement is defined as the proportion of comments sharing the majority sentiment sign.
    """
    if thread_df.empty:
        return 0.0
    
    if sentiment_col not in thread_df.columns:
        logger.warning(f"Sentiment column '{sentiment_col}' not found. Returning 0.0 agreement.")
        return 0.0
    
    # Determine majority sentiment sign (positive, negative, or neutral)
    # We'll binarize: >0 positive, <0 negative, 0 neutral (treat neutral as separate or merge?)
    # Standard approach: count positive vs negative. 
    signs = thread_df[sentiment_col].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
    
    if len(signs) == 0:
        return 0.0
    
    # Count occurrences of each sign
    counts = signs.value_counts()
    
    # If there's a clear majority (e.g., all positive or all negative), agreement is high
    # Agreement = count of majority / total
    majority_count = counts.max()
    total_count = len(signs)
    
    return majority_count / total_count

def compute_time_to_decision(thread_df: pd.DataFrame, timestamp_col: str = 'timestamp') -> Optional[float]:
    """
    Compute time-to-decision in seconds.
    Assumes the last post in the thread represents the decision point.
    Returns duration from first post to last post.
    """
    if thread_df.empty or timestamp_col not in thread_df.columns:
        return None
    
    try:
        # Ensure timestamps are datetime
        times = pd.to_datetime(thread_df[timestamp_col])
        if times.empty:
            return None
        return float((times.max() - times.min()).total_seconds())
    except Exception as e:
        logger.warning(f"Could not compute time-to-decision: {e}")
        return None

def compute_decision_quality_metrics(thread_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compute all decision quality metrics for a single thread:
    (a) Agreement proportion
    (b) Shannon entropy for diversity
    (c) External validation score (if available)
    (d) Efficiency metrics (time-to-decision, thread length)
    """
    metrics = {}
    
    # (a) Agreement proportion
    metrics['agreement_proportion'] = compute_agreement_proportion(thread_df)
    
    # (b) Shannon entropy for diversity
    # We use the distribution of sentiment signs as the probability distribution
    if 'compound_sentiment' in thread_df.columns:
        signs = thread_df['compound_sentiment'].apply(lambda x: 1 if x > 0 else (-1 if x < 0 else 0))
        counts = signs.value_counts()
        # Convert to list of counts for entropy
        value_counts = list(counts.values)
        metrics['shannon_entropy'] = compute_shannon_entropy(value_counts)
    else:
        metrics['shannon_entropy'] = 0.0
    
    # (c) External validation score
    # Check if this column exists (added in T019a)
    if 'external_validation_score' in thread_df.columns:
        # Take the average or the score associated with the thread
        # Assuming the column is constant per thread or we take the mean
        metrics['external_validation_score'] = float(thread_df['external_validation_score'].mean())
    else:
        metrics['external_validation_score'] = None
    
    # (d) Efficiency metrics
    ttd = compute_time_to_decision(thread_df)
    metrics['time_to_decision_seconds'] = ttd
    metrics['thread_length'] = len(thread_df)
    
    return metrics

def save_thread_metrics(metrics_list: List[Dict[str, Any]], filepath: str) -> None:
    """Save a list of metric dictionaries to a CSV file."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    if not metrics_list:
        logger.warning("No metrics to save.")
        # Create empty file with headers if possible, or just touch
        pd.DataFrame().to_csv(path, index=False)
        return

    df = pd.DataFrame(metrics_list)
    df.to_csv(path, index=False)
    logger.info(f"Saved {len(metrics_list)} thread metrics to {filepath}")

def run_decision_quality_pipeline(
    input_path: str, 
    output_path: str,
    min_replies: int = 5
) -> Dict[str, Any]:
    """
    Main pipeline to compute decision quality metrics for all valid threads.
    
    1. Load processed data (from T019/T013).
    2. Filter by reply count.
    3. Group by thread_id.
    4. Compute metrics for each thread.
    5. Save results.
    
    Returns a summary dictionary.
    """
    logger.info(f"Starting decision quality metrics pipeline. Input: {input_path}")
    
    # Load data
    df = load_processed_data(input_path)
    
    # Ensure we have thread_id
    if 'thread_id' not in df.columns:
        raise ValueError("Input data must contain 'thread_id' column.")
    
    # Filter by reply count (if column exists)
    if 'reply_count' in df.columns:
        filtered_df, exclusion_counts = run_metrics_exclusion_pipeline(df, min_replies)
    else:
        filtered_df = df
        exclusion_counts = {"total": len(df), "excluded": 0}
    
    if filtered_df.empty:
        logger.warning("No threads passed the filter. Saving empty metrics.")
        save_thread_metrics([], output_path)
        return {
            "status": "empty",
            "input_count": len(df),
            "output_count": 0,
            "exclusions": exclusion_counts
        }
    
    # Group by thread_id
    thread_groups = filtered_df.groupby('thread_id')
    
    metrics_list = []
    for thread_id, group in thread_groups:
        metrics = compute_decision_quality_metrics(group)
        metrics['thread_id'] = thread_id
        metrics_list.append(metrics)
    
    # Save
    save_thread_metrics(metrics_list, output_path)
    
    return {
        "status": "success",
        "input_count": len(df),
        "filtered_count": len(filtered_df),
        "output_count": len(metrics_list),
        "exclusions": exclusion_counts,
        "output_file": str(output_path)
    }

def main():
    """Entry point for the decision quality metrics pipeline."""
    config = get_config()
    
    # Define paths based on config or defaults
    # Assuming valid dataset is at data/processed/valid_threads.csv (from T019)
    # Or we might need to load the sentiment-processed data from T013
    # The task says "use the *filtered* dataset (valid threads, seed posts extracted, reply count >= 5)"
    # T013 produces sentiment scores. T019 produces valid threads.
    # We assume the sentiment scores are merged into the valid threads data or we load from a specific processed file.
    # Let's assume the input is the sentiment-processed valid threads.
    
    # Default paths
    input_file = "data/processed/valid_threads_sentiment.csv" 
    # If that doesn't exist, try to load from the base valid threads and assume sentiment is there?
    # The spec says T013 applies VADER to the valid dataset.
    # Let's check if a merged file exists or construct the path.
    # For robustness, we'll try the most likely path derived from previous tasks.
    
    # Attempt to find the file
    possible_inputs = [
        "data/processed/valid_threads_sentiment.csv",
        "data/processed/valid_threads.csv",
        "data/processed/threads_with_seeds.csv"
    ]
    
    actual_input = None
    for p in possible_inputs:
        if Path(p).exists():
            actual_input = p
            break
    
    if not actual_input:
        # Fallback: try to load the raw valid threads and hope sentiment is there, or fail
        logger.error("Could not find valid threads with sentiment data.")
        raise FileNotFoundError("No valid input file found for decision quality metrics.")
    
    output_file = "data/processed/decision_quality_metrics.csv"
    
    logger.info(f"Processing input: {actual_input}")
    logger.info(f"Output will be written to: {output_file}")
    
    try:
        result = run_decision_quality_pipeline(actual_input, output_file)
        logger.info(f"Pipeline completed successfully. Result: {result}")
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
