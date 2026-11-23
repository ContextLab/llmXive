import os
import sys
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
from scipy import stats
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data/processed/metrics_pipeline.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Constants
PROJECT_ROOT = Path(__file__).parent.parent.parent
PROCESSED_DIR = PROJECT_ROOT / 'data' / 'processed'
RAW_DIR = PROJECT_ROOT / 'data' / 'raw'

def load_processed_data() -> pd.DataFrame:
    """
    Load the filtered dataset containing threads with ≥3 seed posts.
    
    CRITICAL FIX FOR T059:
    This function now explicitly loads 'threads_with_seeds.csv' (output of T009)
    instead of 'reddit_threads.jsonl'. This ensures that threads excluded by
    T010 (those with <3 top-level posts) are NOT included in the metrics calculation.
    
    Returns:
        pd.DataFrame: Filtered dataset with seed posts extracted.
        
    Raises:
        FileNotFoundError: If the filtered dataset does not exist.
    """
    input_path = PROCESSED_DIR / 'threads_with_seeds.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Filtered dataset not found at {input_path}. "
            "Ensure T009 (extract_seed_posts) has been executed successfully."
        )
    
    logger.info(f"Loading filtered dataset from {input_path}")
    df = pd.read_csv(input_path)
    
    logger.info(f"Loaded {len(df)} threads from filtered dataset. "
               f"Columns: {list(df.columns)}")
    
    return df

def filter_threads_by_reply_count(df: pd.DataFrame, min_replies: int = 20) -> pd.DataFrame:
    """
    Filter threads based on reply count for contagion index calculation.
    
    Args:
        df: Input DataFrame with thread data.
        min_replies: Minimum number of replies required (default: 20).
        
    Returns:
        pd.DataFrame: Filtered DataFrame with threads having >= min_replies.
    """
    logger.info(f"Filtering threads with reply_count >= {min_replies}")
    
    if 'reply_count' not in df.columns:
        logger.warning("Column 'reply_count' not found in DataFrame. "
                     "Attempting to calculate from available data.")
        # Fallback: calculate reply_count if not present
        # This assumes we have comment data or can infer from thread structure
        if 'comments' in df.columns:
            df['reply_count'] = df['comments'].apply(lambda x: len(eval(x)) if isinstance(x, str) else 0)
        else:
            logger.error("Cannot calculate reply_count without 'comments' column.")
            raise KeyError("Missing 'reply_count' or 'comments' column")
    
    filtered_df = df[df['reply_count'] >= min_replies].copy()
    excluded_count = len(df) - len(filtered_df)
    
    logger.info(f"Filtered {excluded_count} threads with reply_count < {min_replies}. "
               f"Remaining threads: {len(filtered_df)}")
    
    # Log exclusions
    if excluded_count > 0:
        exclusions_path = PROCESSED_DIR / 'exclusions_reply_count.log'
        with open(exclusions_path, 'w') as f:
            excluded_threads = df[df['reply_count'] < min_replies]
            for _, row in excluded_threads.iterrows():
                f.write(json.dumps({
                    'thread_id': row.get('thread_id', 'unknown'),
                    'reason_code': 'REPLY_COUNT_INSUFFICIENT',
                    'reply_count': row['reply_count'],
                    'min_required': min_replies
                }) + '\n')
        logger.info(f"Exclusion log written to {exclusions_path}")
    
    return filtered_df

def save_exclusion_counts(excluded_count: int, reason_code: str, output_path: Path):
    """Save exclusion counts to a log file."""
    with open(output_path, 'a') as f:
        f.write(json.dumps({
            'timestamp': pd.Timestamp.now().isoformat(),
            'reason_code': reason_code,
            'excluded_count': excluded_count
        }) + '\n')

def run_metrics_exclusion_pipeline():
    """
    Run the metrics exclusion pipeline.
    
    This pipeline:
    1. Loads the filtered dataset (threads with ≥3 seed posts) from T009.
    2. Filters threads by reply count (≥20) for contagion analysis.
    3. Logs exclusions and writes metrics.
    """
    logger.info("Starting metrics exclusion pipeline")
    
    # Step 1: Load filtered dataset (T059 FIX: uses threads_with_seeds.csv)
    df = load_processed_data()
    
    # Step 2: Filter by reply count
    filtered_df = filter_threads_by_reply_count(df, min_replies=20)
    
    # Step 3: Save exclusion counts
    exclusion_log_path = PROCESSED_DIR / 'exclusion_counts.log'
    save_exclusion_counts(
        excluded_count=len(df) - len(filtered_df),
        reason_code='REPLY_COUNT_INSUFFICIENT',
        output_path=exclusion_log_path
    )
    
    logger.info(f"Metrics exclusion pipeline complete. "
               f"Threads remaining: {len(filtered_df)}")
    
    return filtered_df

def compute_shannon_entropy(values: List[float]) -> float:
    """
    Compute Shannon entropy for a list of values.
    
    Args:
        values: List of values (e.g., sentiment scores).
        
    Returns:
        float: Shannon entropy value.
    """
    if not values or len(values) == 0:
        return 0.0
    
    # Normalize to probabilities
    total = sum(values)
    if total == 0:
        return 0.0
    
    probs = [v / total for v in values]
    entropy = -sum(p * math.log(p) if p > 0 else 0 for p in probs)
    
    return entropy

def compute_agreement_proportion(scores: List[float], threshold: float = 0.5) -> float:
    """
    Compute agreement proportion based on sentiment scores.
    
    Args:
        scores: List of sentiment scores.
        threshold: Threshold for agreement (default: 0.5).
        
    Returns:
        float: Agreement proportion.
    """
    if not scores:
        return 0.0
    
    # Count scores above threshold
    agreements = sum(1 for s in scores if s > threshold)
    return agreements / len(scores)

def compute_time_to_decision(thread_data: Dict[str, Any]) -> float:
    """
    Compute time-to-decision for a thread.
    
    Args:
        thread_data: Dictionary containing thread data with timestamps.
        
    Returns:
        float: Time-to-decision in seconds.
    """
    if 'start_time' not in thread_data or 'decision_time' not in thread_data:
        return 0.0
    
    start = pd.to_datetime(thread_data['start_time'])
    decision = pd.to_datetime(thread_data['decision_time'])
    
    return (decision - start).total_seconds()

def compute_decision_quality_metrics(thread_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute decision quality metrics for each thread.
    
    Args:
        thread_df: DataFrame with thread data.
        
    Returns:
        pd.DataFrame: DataFrame with added decision quality metrics.
    """
    logger.info("Computing decision quality metrics")
    
    metrics = []
    
    for _, row in thread_df.iterrows():
        thread_id = row.get('thread_id', 'unknown')
        
        # Extract sentiment scores (assuming they are in a list or string representation)
        if 'sentiment_scores' in row:
            scores_str = row['sentiment_scores']
            if isinstance(scores_str, str):
                try:
                    scores = eval(scores_str)
                except:
                    scores = []
            else:
                scores = scores_str
        else:
            scores = []
        
        # Compute metrics
        entropy = compute_shannon_entropy([abs(s) for s in scores]) if scores else 0.0
        agreement = compute_agreement_proportion(scores, threshold=0.5) if scores else 0.0
        
        # Time to decision (if timestamps available)
        time_to_decision = 0.0
        if 'start_time' in row and 'decision_time' in row:
            time_to_decision = compute_time_to_decision(row)
        
        metrics.append({
            'thread_id': thread_id,
            'entropy': entropy,
            'agreement_proportion': agreement,
            'time_to_decision': time_to_decision,
            'reply_count': row.get('reply_count', 0)
        })
    
    metrics_df = pd.DataFrame(metrics)
    logger.info(f"Computed decision quality metrics for {len(metrics_df)} threads")
    
    return metrics_df

def compute_bootstrap_ci(data: List[float], stat_func, n_bootstrap: int = 1000, 
                        confidence: float = 0.95, random_seed: int = 42) -> Tuple[float, float]:
    """
    Compute bootstrap confidence intervals for a statistic.
    
    Args:
        data: Input data.
        stat_func: Function to compute the statistic.
        n_bootstrap: Number of bootstrap samples.
        confidence: Confidence level (default: 0.95).
        random_seed: Random seed for reproducibility.
        
    Returns:
        Tuple[float, float]: Lower and upper bounds of confidence interval.
    """
    random.seed(random_seed)
    np.random.seed(random_seed)
    
    bootstrap_stats = []
    n = len(data)
    
    for _ in range(n_bootstrap):
        sample = np.random.choice(data, size=n, replace=True)
        stat = stat_func(sample)
        if not math.isnan(stat) and not math.isinf(stat):
            bootstrap_stats.append(stat)
    
    if not bootstrap_stats:
        return (0.0, 0.0)
    
    lower_percentile = (1 - confidence) / 2 * 100
    upper_percentile = (1 + confidence) / 2 * 100
    
    lower = np.percentile(bootstrap_stats, lower_percentile)
    upper = np.percentile(bootstrap_stats, upper_percentile)
    
    return (lower, upper)

def save_thread_metrics(metrics_df: pd.DataFrame, output_path: Path):
    """Save thread metrics to CSV."""
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Thread metrics saved to {output_path}")

def run_decision_quality_pipeline():
    """
    Run the full decision quality metrics pipeline.
    
    This pipeline:
    1. Loads filtered dataset (T059 FIX: uses threads_with_seeds.csv).
    2. Filters by reply count.
    3. Computes decision quality metrics.
    4. Saves results to thread_metrics.csv.
    """
    logger.info("Starting decision quality metrics pipeline")
    
    # Load and filter data
    df = load_processed_data()
    filtered_df = filter_threads_by_reply_count(df, min_replies=20)
    
    # Compute metrics
    metrics_df = compute_decision_quality_metrics(filtered_df)
    
    # Save results
    output_path = PROCESSED_DIR / 'thread_metrics.csv'
    save_thread_metrics(metrics_df, output_path)
    
    logger.info(f"Decision quality pipeline complete. "
               f"Metrics saved to {output_path}")
    
    return metrics_df

def main():
    """Main entry point for the metrics pipeline."""
    logger.info("Metrics pipeline started")
    
    try:
        # Run the pipeline
        metrics_df = run_decision_quality_pipeline()
        
        # Log summary
        logger.info(f"Pipeline summary:")
        logger.info(f"  - Threads processed: {len(metrics_df)}")
        logger.info(f"  - Output file: {PROCESSED_DIR / 'thread_metrics.csv'}")
        
    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == '__main__':
    main()
