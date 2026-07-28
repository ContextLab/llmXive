import os
import json
import logging
import math
import random
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
import pandas as pd
import numpy as np
from scipy.stats import pearsonr

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_processed_data(file_path: str) -> pd.DataFrame:
    """Load processed thread data from CSV."""
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Processed data file not found: {file_path}")
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {file_path}")
    return df

def filter_threads_by_reply_count(df: pd.DataFrame, min_replies: int) -> pd.DataFrame:
    """Filter threads based on minimum reply count."""
    filtered = df[df['reply_count'] >= min_replies].copy()
    logger.info(f"Filtered to {len(filtered)} threads with reply_count >= {min_replies}")
    return filtered

def save_exclusion_counts(exclusions: Dict[str, int], log_path: str):
    """Save exclusion counts to a log file."""
    with open(log_path, 'w') as f:
        json.dump(exclusions, f, indent=2)
    logger.info(f"Saved exclusion counts to {log_path}")

def run_metrics_exclusion_pipeline(df: pd.DataFrame, output_path: str):
    """Run the exclusion pipeline for metrics calculation."""
    # Filter for threads with >= 5 replies (minimum for any analysis)
    valid_threads = filter_threads_by_reply_count(df, 5)
    
    # Classify into primary (>=20) and secondary (5-19) sets
    primary_set = valid_threads[valid_threads['reply_count'] >= 20]
    secondary_set = valid_threads[(valid_threads['reply_count'] >= 5) & (valid_threads['reply_count'] < 20)]
    
    exclusions = {
        'total_threads': len(df),
        'valid_threads': len(valid_threads),
        'primary_set': len(primary_set),
        'secondary_set': len(secondary_set),
        'excluded_insufficient_replies': len(df) - len(valid_threads)
    }
    
    # Save exclusion log
    exclusion_log_path = str(Path(output_path).parent / 'exclusion_counts.json')
    save_exclusion_counts(exclusions, exclusion_log_path)
    
    return primary_set, secondary_set

def compute_shannon_entropy(proportions: List[float]) -> float:
    """Compute Shannon entropy for a list of proportions."""
    if not proportions or sum(proportions) == 0:
        return 0.0
    entropy = 0.0
    for p in proportions:
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy

def compute_agreement_proportion(sentiment_scores: List[float]) -> float:
    """Compute agreement proportion based on sentiment scores."""
    if not sentiment_scores:
        return 0.0
    # Convert to binary: positive (>=0) vs negative (<0)
    positive_count = sum(1 for s in sentiment_scores if s >= 0)
    return positive_count / len(sentiment_scores)

def compute_time_to_decision(thread_data: Dict[str, Any]) -> float:
    """Compute time to decision in seconds."""
    # Placeholder implementation - depends on actual data structure
    if 'timestamps' in thread_data and len(thread_data['timestamps']) > 1:
        # Calculate time difference between first post and decision point
        # Assuming timestamps are in ISO format
        try:
            from datetime import datetime
            first_time = datetime.fromisoformat(thread_data['timestamps'][0])
            decision_time = datetime.fromisoformat(thread_data['timestamps'][-1])
            return (decision_time - first_time).total_seconds()
        except Exception as e:
            logger.warning(f"Could not compute time to decision: {e}")
            return 0.0
    return 0.0

def compute_decision_quality_metrics(thread_data: Dict[str, Any]) -> Dict[str, float]:
    """Compute all decision quality metrics for a thread."""
    metrics = {
        'agreement_proportion': compute_agreement_proportion(thread_data.get('sentiment_scores', [])),
        'shannon_entropy': compute_shannon_entropy(thread_data.get('sentiment_distribution', [0.5, 0.5])),
        'time_to_decision': compute_time_to_decision(thread_data)
    }
    return metrics

def compute_bootstrap_ci(x: List[float], y: List[float], n_bootstraps: int = 1000, 
                         confidence_level: float = 0.95, random_seed: Optional[int] = None) -> Tuple[float, float]:
    """
    Compute 95% confidence interval for Pearson correlation using bootstrapping.
    
    Args:
        x: First variable (e.g., seed sentiment)
        y: Second variable (e.g., delta sentiment)
        n_bootstraps: Number of bootstrap resamples
        confidence_level: Confidence level for the interval (default 0.95)
        random_seed: Random seed for reproducibility
    
    Returns:
        Tuple of (lower_bound, upper_bound) for the confidence interval
    """
    if random_seed is not None:
        np.random.seed(random_seed)
    
    if len(x) != len(y) or len(x) < 2:
        logger.warning("Insufficient data for bootstrap CI calculation")
        return (None, None)
    
    n = len(x)
    bootstrap_correlations = []
    
    for _ in range(n_bootstraps):
        # Resample with replacement
        indices = np.random.choice(n, size=n, replace=True)
        x_resampled = [x[i] for i in indices]
        y_resampled = [y[i] for i in indices]
        
        # Compute correlation for this bootstrap sample
        try:
            corr, _ = pearsonr(x_resampled, y_resampled)
            if not math.isnan(corr):
                bootstrap_correlations.append(corr)
        except Exception as e:
            # Skip if correlation cannot be computed (e.g., constant values)
            continue
    
    if len(bootstrap_correlations) < 10:
        logger.warning("Insufficient bootstrap samples for reliable CI")
        return (None, None)
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_idx = int((alpha / 2) * len(bootstrap_correlations))
    upper_idx = int((1 - alpha / 2) * len(bootstrap_correlations))
    
    sorted_correlations = sorted(bootstrap_correlations)
    lower_bound = sorted_correlations[lower_idx]
    upper_bound = sorted_correlations[upper_idx]
    
    return (lower_bound, upper_bound)

def save_thread_metrics(metrics_df: pd.DataFrame, output_path: str):
    """Save thread metrics to CSV."""
    metrics_df.to_csv(output_path, index=False)
    logger.info(f"Saved thread metrics to {output_path} with {len(metrics_df)} rows")

def run_decision_quality_pipeline(df: pd.DataFrame, output_path: str):
    """
    Run the full decision quality metrics pipeline including contagion index
    calculation with bootstrapped confidence intervals.
    
    This implements T053: Add confidence_interval column to thread_metrics.csv
    """
    logger.info("Starting decision quality metrics pipeline")
    
    # Filter threads
    primary_set, secondary_set = run_metrics_exclusion_pipeline(df, output_path)
    
    all_metrics = []
    
    # Process primary set (fixed window: 20 comments)
    for _, thread in primary_set.iterrows():
        thread_id = thread['thread_id']
        seed_sentiment = thread.get('seed_sentiment', 0.0)
        reply_sentiments = thread.get('reply_sentiments', [])
        reply_count = thread.get('reply_count', 0)
        
        # Use first 20 replies for fixed window
        window_sentiments = reply_sentiments[:20] if len(reply_sentiments) >= 20 else reply_sentiments
        
        if len(window_sentiments) < 2:
            logger.warning(f"Thread {thread_id}: Insufficient replies for delta calculation")
            continue
        
        # Calculate delta as slope of linear regression of sentiment vs position
        positions = list(range(1, len(window_sentiments) + 1))
        try:
            # Simple linear regression: y = mx + c, where m is the slope (delta)
            n = len(positions)
            sum_x = sum(positions)
            sum_y = sum(window_sentiments)
            sum_xy = sum(x * y for x, y in zip(positions, window_sentiments))
            sum_x2 = sum(x * x for x in positions)
            
            delta = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            # Calculate Pearson correlation between seed sentiment and delta
            # Since we have only one seed sentiment value, we compute correlation
            # across multiple threads, but for this thread we record the delta
            # and later correlate across the dataset
            # For now, we'll store the delta and seed sentiment for later correlation
            metrics_row = {
                'thread_id': thread_id,
                'contagion_index': delta,  # Delta as the contagion index
                'reply_count_used': len(window_sentiments),
                'window_type': 'fixed_20',
                'seed_sentiment': seed_sentiment,
                'delta': delta
            }
            
            # Compute bootstrap CI for the correlation if we had multiple samples
            # For a single thread, we can't compute correlation, so we'll set CI to null
            # The correlation will be computed across threads in a separate step
            metrics_row['confidence_interval'] = None
            
            all_metrics.append(metrics_row)
            
        except Exception as e:
            logger.warning(f"Thread {thread_id}: Error calculating delta - {e}")
            continue
    
    # Process secondary set (variable window)
    for _, thread in secondary_set.iterrows():
        thread_id = thread['thread_id']
        seed_sentiment = thread.get('seed_sentiment', 0.0)
        reply_sentiments = thread.get('reply_sentiments', [])
        reply_count = thread.get('reply_count', 0)
        
        if len(reply_sentiments) < 2:
            logger.warning(f"Thread {thread_id}: Insufficient replies for delta calculation")
            continue
        
        # Use all available replies
        window_sentiments = reply_sentiments
        
        try:
            positions = list(range(1, len(window_sentiments) + 1))
            n = len(positions)
            sum_x = sum(positions)
            sum_y = sum(window_sentiments)
            sum_xy = sum(x * y for x, y in zip(positions, window_sentiments))
            sum_x2 = sum(x * x for x in positions)
            
            delta = (n * sum_xy - sum_x * sum_y) / (n * sum_x2 - sum_x * sum_x)
            
            metrics_row = {
                'thread_id': thread_id,
                'contagion_index': delta,
                'reply_count_used': len(window_sentiments),
                'window_type': 'variable',
                'seed_sentiment': seed_sentiment,
                'delta': delta,
                'confidence_interval': None
            }
            
            all_metrics.append(metrics_row)
            
        except Exception as e:
            logger.warning(f"Thread {thread_id}: Error calculating delta - {e}")
            continue
    
    # Create DataFrame
    metrics_df = pd.DataFrame(all_metrics)
    
    # Calculate correlation across all threads and compute bootstrap CI
    if len(metrics_df) >= 2:
        seed_sentiments = metrics_df['seed_sentiment'].tolist()
        deltas = metrics_df['contagion_index'].tolist()
        
        try:
            overall_corr, _ = pearsonr(seed_sentiments, deltas)
            
            # Compute bootstrap CI for the overall correlation
            ci_lower, ci_upper = compute_bootstrap_ci(
                seed_sentiments, deltas, 
                n_bootstraps=1000, 
                confidence_level=0.95,
                random_seed=42
            )
            
            # Add CI to all rows (since it's a dataset-level statistic)
            if ci_lower is not None and ci_upper is not None:
                metrics_df['confidence_interval'] = f"[{ci_lower:.4f}, {ci_upper:.4f}]"
                logger.info(f"Overall correlation: {overall_corr:.4f}, 95% CI: [{ci_lower:.4f}, {ci_upper:.4f}]")
            else:
                metrics_df['confidence_interval'] = None
                logger.warning("Could not compute confidence interval")
                
        except Exception as e:
            logger.warning(f"Error computing correlation and CI: {e}")
            metrics_df['confidence_interval'] = None
    else:
        logger.warning("Insufficient threads for correlation analysis")
        metrics_df['confidence_interval'] = None
    
    # Save results
    save_thread_metrics(metrics_df, output_path)
    
    return metrics_df

def main():
    """Main entry point for the metrics pipeline."""
    # Define paths
    base_path = Path(__file__).parent.parent
    input_path = base_path / "data" / "processed" / "all_threads_classified.csv"
    output_path = base_path / "data" / "processed" / "thread_metrics.csv"
    
    if not input_path.exists():
        logger.error(f"Input file not found: {input_path}")
        return
    
    # Load data
    df = load_processed_data(str(input_path))
    
    # Run pipeline
    metrics_df = run_decision_quality_pipeline(df, str(output_path))
    
    logger.info("Decision quality metrics pipeline completed successfully")

if __name__ == "__main__":
    main()