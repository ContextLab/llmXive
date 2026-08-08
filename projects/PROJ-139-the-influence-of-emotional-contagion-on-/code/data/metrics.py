"""
Emotional Contagion Metrics and Decision Quality Calculations.

This module implements the calculation of the emotional contagion index,
decision quality metrics, and related statistical analyses.

CRITICAL DATA FLOW NOTE (T059 FIX):
This module now explicitly reads from the *filtered* dataset
(data/processed/threads_with_seeds.csv) which contains only threads
that passed the seed post filter (>=3 top-level posts) as defined in T010.
It NO LONGER reads from data/raw/reddit_threads.jsonl directly for metrics
calculation to prevent inclusion of excluded threads.
"""

import os
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy import stats

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants
MIN_REPLIES_FOR_CONTAGION = 20
SENTIMENT_WINDOW_SIZE = 20
BOOTSTRAP_RESAMPLES = 1000
RANDOM_SEED = 42

np.random.seed(RANDOM_SEED)
random.seed(RANDOM_SEED)


def load_processed_data(input_path: str) -> pd.DataFrame:
    """
    Load the processed dataset containing threads with extracted seed posts.

    T059 FIX: This function now loads from the filtered dataset
    (threads_with_seeds.csv) which has already excluded threads with <3 seed posts.

    Args:
        input_path: Path to the input CSV file.

    Returns:
        DataFrame with thread data.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    logger.info(f"Loading processed data from {input_path}")
    df = pd.read_csv(input_path)

    # Verify required columns exist
    required_cols = ['thread_id', 'seed_sentiment', 'replies', 'reply_count']
    missing = [col for col in required_cols if col not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    logger.info(f"Loaded {len(df)} threads from filtered dataset")
    return df


def filter_threads_by_reply_count(df: pd.DataFrame, min_replies: int = MIN_REPLIES_FOR_CONTAGION) -> Tuple[pd.DataFrame, int]:
    """
    Filter threads based on minimum reply count for contagion analysis.

    Args:
        df: Input DataFrame.
        min_replies: Minimum number of replies required.

    Returns:
        Tuple of (filtered DataFrame, count of excluded threads).
    """
    total_count = len(df)
    filtered_df = df[df['reply_count'] >= min_replies].copy()
    excluded_count = total_count - len(filtered_df)

    logger.info(f"Filtered threads: {len(filtered_df)} included, {excluded_count} excluded (reply_count < {min_replies})")

    return filtered_df, excluded_count


def save_exclusion_counts(exclusion_log_path: str, reason_code: str, count: int, details: Optional[List[Dict]] = None):
    """
    Save exclusion counts to a log file.

    Args:
        exclusion_log_path: Path to the exclusion log file.
        reason_code: Code indicating the reason for exclusion.
        count: Number of excluded items.
        details: Optional list of detailed exclusion records.
    """
    log_entry = {
        "reason_code": reason_code,
        "count": count,
        "timestamp": pd.Timestamp.now().isoformat()
    }
    if details:
        log_entry["details"] = details

    log_path = Path(exclusion_log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with open(log_path, 'a') as f:
        f.write(json.dumps(log_entry) + '\n')

    logger.info(f"Saved exclusion log: {reason_code} - {count} items")


def run_metrics_exclusion_pipeline(exclusion_log_path: str, output_path: str):
    """
    Run the exclusion pipeline for metrics calculation.

    Args:
        exclusion_log_path: Path to write exclusion logs.
        output_path: Path to write the filtered dataset.
    """
    # This is a placeholder for the exclusion logic
    # The actual filtering is done in filter_threads_by_reply_count
    logger.info(f"Metrics exclusion pipeline initialized")


def compute_shannon_entropy(proportions: List[float]) -> float:
    """
    Compute Shannon entropy for a list of proportions.

    Args:
        proportions: List of proportions that sum to 1.

    Returns:
        Shannon entropy value.
    """
    entropy = 0.0
    for p in proportions:
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def compute_agreement_proportion(sentiment_scores: List[float], threshold: float = 0.0) -> float:
    """
    Compute the proportion of posts agreeing with the seed sentiment.

    Args:
        sentiment_scores: List of sentiment scores.
        threshold: Threshold for determining agreement.

    Returns:
        Agreement proportion.
    """
    if not sentiment_scores:
        return 0.0

    # Determine seed sentiment direction (positive if > 0, negative if < 0, neutral if 0)
    # For simplicity, we'll use the first score as the seed sentiment
    seed_sentiment = sentiment_scores[0] if sentiment_scores else 0.0

    agreeing_count = 0
    for score in sentiment_scores[1:]:  # Skip seed post
        if (seed_sentiment > 0 and score > 0) or \
           (seed_sentiment < 0 and score < 0) or \
           (abs(seed_sentiment) < threshold and abs(score) < threshold):
            agreeing_count += 1

    return agreeing_count / len(sentiment_scores[1:]) if len(sentiment_scores) > 1 else 0.0


def compute_time_to_decision(timestamps: List[str]) -> Optional[float]:
    """
    Compute time to decision in seconds.

    Args:
        timestamps: List of ISO format timestamps.

    Returns:
        Time to decision in seconds, or None if insufficient data.
    """
    if len(timestamps) < 2:
        return None

    try:
        first_ts = pd.to_datetime(timestamps[0])
        last_ts = pd.to_datetime(timestamps[-1])
        return (last_ts - first_ts).total_seconds()
    except Exception as e:
        logger.warning(f"Could not compute time to decision: {e}")
        return None


def compute_decision_quality_metrics(thread_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Compute decision quality metrics for a single thread.

    Args:
        thread_data: Dictionary containing thread data.

    Returns:
        Dictionary with computed metrics.
    """
    metrics = {}

    # Extract sentiment scores from replies
    replies = thread_data.get('replies', [])
    if replies:
        sentiment_scores = [r.get('sentiment_compound', 0.0) for r in replies]
        metrics['agreement_proportion'] = compute_agreement_proportion(sentiment_scores)
        metrics['entropy'] = compute_shannon_entropy([1.0])  # Placeholder for diversity calculation
        metrics['time_to_decision'] = compute_time_to_decision([r.get('timestamp') for r in replies])
        metrics['thread_length'] = len(replies)
    else:
        metrics['agreement_proportion'] = 0.0
        metrics['entropy'] = 0.0
        metrics['time_to_decision'] = None
        metrics['thread_length'] = 0

    return metrics


def compute_bootstrap_ci(data: List[float], stat_func, n_resamples: int = BOOTSTRAP_RESAMPLES, confidence: float = 0.95) -> Tuple[float, float, float]:
    """
    Compute bootstrap confidence intervals for a statistic.

    Args:
        data: Input data.
        stat_func: Function to compute the statistic.
        n_resamples: Number of bootstrap resamples.
        confidence: Confidence level.

    Returns:
        Tuple of (statistic, lower_ci, upper_ci).
    """
    data = np.array(data)
    n = len(data)
    bootstrap_stats = []

    for _ in range(n_resamples):
        resample = np.random.choice(data, size=n, replace=True)
        bootstrap_stats.append(stat_func(resample))

    bootstrap_stats = np.array(bootstrap_stats)
    stat_value = stat_func(data)
    alpha = 1 - confidence
    lower_ci = np.percentile(bootstrap_stats, 100 * alpha / 2)
    upper_ci = np.percentile(bootstrap_stats, 100 * (1 - alpha / 2))

    return stat_value, lower_ci, upper_ci


def save_thread_metrics(metrics_df: pd.DataFrame, output_path: str):
    """
    Save thread metrics to a CSV file.

    Args:
        metrics_df: DataFrame with metrics.
        output_path: Path to the output file.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Saved thread metrics to {output_path}")


def run_decision_quality_pipeline(
    input_path: str,
    output_path: str,
    exclusion_log_path: Optional[str] = None
):
    """
    Run the full decision quality metrics pipeline.

    T059 FIX: This pipeline now reads from the filtered dataset
    (threads_with_seeds.csv) to ensure only threads with >=3 seed posts
    are processed.

    Args:
        input_path: Path to the filtered input CSV.
        output_path: Path to write the metrics CSV.
        exclusion_log_path: Optional path to write exclusion logs.
    """
    logger.info("Starting decision quality metrics pipeline")

    # Load processed data (T059: filtered dataset)
    df = load_processed_data(input_path)

    # Filter by reply count for contagion analysis
    filtered_df, excluded_count = filter_threads_by_reply_count(df)

    # Log exclusions if path provided
    if exclusion_log_path and excluded_count > 0:
        save_exclusion_counts(
            exclusion_log_path,
            "REPLY_COUNT_INSUFFICIENT",
            excluded_count
        )

    # Initialize metrics list
    metrics_list = []

    for _, row in filtered_df.iterrows():
        thread_id = row['thread_id']
        seed_sentiment = row['seed_sentiment']
        replies = row.get('replies', [])

        # Parse replies if stored as string
        if isinstance(replies, str):
            try:
                replies = json.loads(replies)
            except:
                replies = []

        if not isinstance(replies, list):
            replies = []

        # Extract sentiment scores
        sentiment_scores = [r.get('sentiment_compound', 0.0) for r in replies] if replies else []

        # Compute contagion index (delta of sentiment over first 20 replies)
        if len(sentiment_scores) >= MIN_REPLIES_FOR_CONTAGION:
            window_scores = sentiment_scores[:SENTIMENT_WINDOW_SIZE]
            positions = list(range(1, SENTIMENT_WINDOW_SIZE + 1))

            # Linear regression for slope (delta)
            slope, intercept, r_value, p_value, std_err = stats.linregress(positions, window_scores)
            contagion_index = slope

            # Compute Pearson correlation between seed sentiment and delta
            # For simplicity, we'll use the slope as the contagion index
            # and compute correlation with seed sentiment across threads later

            # Bootstrap confidence intervals for the slope
            stat_val, ci_low, ci_high = compute_bootstrap_ci(
                window_scores,
                lambda x: stats.linregress(range(1, len(x)+1), x)[0],
                n_resamples=BOOTSTRAP_RESAMPLES
            )

            metrics_list.append({
                'thread_id': thread_id,
                'contagion_index': contagion_index,
                'reply_count_used': min(len(sentiment_scores), SENTIMENT_WINDOW_SIZE),
                'window_type': 'fixed_20',
                'confidence_interval_low': ci_low,
                'confidence_interval_high': ci_high,
                'seed_sentiment': seed_sentiment,
                'reply_count': row['reply_count']
            })
        else:
            # Insufficient replies for contagion calculation
            metrics_list.append({
                'thread_id': thread_id,
                'contagion_index': None,
                'reply_count_used': len(sentiment_scores),
                'window_type': 'insufficient',
                'confidence_interval_low': None,
                'confidence_interval_high': None,
                'seed_sentiment': seed_sentiment,
                'reply_count': row['reply_count']
            })

    # Create DataFrame
    metrics_df = pd.DataFrame(metrics_list)

    # Save metrics
    save_thread_metrics(metrics_df, output_path)

    logger.info(f"Decision quality pipeline complete. Processed {len(metrics_df)} threads.")
    return metrics_df


def main():
    """
    Main entry point for the metrics pipeline.
    """
    # Define paths
    base_dir = Path(__file__).parent.parent
    input_path = base_dir / "data" / "processed" / "threads_with_seeds.csv"
    output_path = base_dir / "data" / "processed" / "thread_metrics.csv"
    exclusion_log_path = base_dir / "data" / "processed" / "metrics_exclusions.log"

    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        logger.error("Please ensure T009 (extract.py) has run and produced threads_with_seeds.csv")
        return

    # Run pipeline
    run_decision_quality_pipeline(
        input_path=str(input_path),
        output_path=str(output_path),
        exclusion_log_path=str(exclusion_log_path)
    )


if __name__ == "__main__":
    main()