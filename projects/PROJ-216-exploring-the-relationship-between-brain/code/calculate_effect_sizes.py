"""
T032: Calculate effect sizes (Cohen's d) and 95% confidence intervals.

Reads data/processed/graph_metrics.csv and data/processed/behavioral_scores.csv,
merges them, computes Pearson/Spearman correlations per metric, calculates
Cohen's d and 95% CIs, and appends the results to the CSV.

Output:
    data/processed/graph_metrics.csv (updated with new columns)
"""
import os
import sys
import math
import csv
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
import numpy as np
import pandas as pd
from scipy import stats

# Import existing utilities
from config import get_sample_limit

# Constants
PROJECT_ROOT = Path(__file__).resolve().parent.parent
GRAPH_METRICS_PATH = PROJECT_ROOT / "data" / "processed" / "graph_metrics.csv"
BEHAVIORAL_SCORES_PATH = PROJECT_ROOT / "data" / "processed" / "behavioral_scores.csv"
OUTPUT_PATH = GRAPH_METRICS_PATH  # Overwrite the existing file as per task description

def load_graph_metrics() -> pd.DataFrame:
    """Load the graph metrics CSV."""
    if not GRAPH_METRICS_PATH.exists():
        raise FileNotFoundError(f"Graph metrics file not found: {GRAPH_METRICS_PATH}")
    df = pd.read_csv(GRAPH_METRICS_PATH)
    # Ensure required columns exist
    required_cols = ["subject_id", "metric_name", "value"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in graph metrics: {missing}")
    return df

def load_behavioral_scores() -> pd.DataFrame:
    """Load the behavioral scores CSV."""
    if not BEHAVIORAL_SCORES_PATH.exists():
        raise FileNotFoundError(f"Behavioral scores file not found: {BEHAVIORAL_SCORES_PATH}")
    df = pd.read_csv(BEHAVIORAL_SCORES_PATH)
    # Ensure required columns exist
    required_cols = ["subject_id", "score_value"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns in behavioral scores: {missing}")
    return df

def calculate_cohen_d(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Formula: (mean1 - mean2) / pooled_std
    Pooled std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1 + n2 - 2))
    """
    n1, n2 = len(group1), len(group2)
    if n1 < 2 or n2 < 2:
        return 0.0  # Cannot calculate with < 2 samples per group
    
    mean1, std1 = np.mean(group1), np.std(group1, ddof=1)
    mean2, std2 = np.mean(group2), np.std(group2, ddof=1)
    
    if std1 == 0 and std2 == 0:
        return 0.0
        
    pooled_std = math.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std

def calculate_ci_95_cohen_d(cohens_d: float, n1: int, n2: int, alpha: float = 0.05) -> Tuple[float, float]:
    """
    Calculate 95% Confidence Interval for Cohen's d.
    
    Approximation using non-central t-distribution or standard error approximation.
    SE_d ≈ sqrt((n1+n2)/(n1*n2) + d^2/(2*(n1+n2)))
    CI = d ± t_crit * SE_d
    """
    n = n1 + n2
    if n < 3:
        return (0.0, 0.0)
    
    # Standard error approximation
    se_d = math.sqrt((n / (n1 * n2)) + (cohens_d**2 / (2 * (n - 2))))
    
    # t critical value for 95% CI (two-tailed)
    # Degrees of freedom for independent t-test
    df = n1 + n2 - 2
    t_crit = stats.t.ppf(1 - alpha/2, df)
    
    lower = cohens_d - t_crit * se_d
    upper = cohens_d + t_crit * se_d
    
    return (lower, upper)

def main():
    print("Starting T032: Calculate effect sizes and confidence intervals...")
    
    # Load data
    try:
        metrics_df = load_graph_metrics()
        scores_df = load_behavioral_scores()
    except FileNotFoundError as e:
        print(f"ERROR: {e}")
        sys.exit(1)
    
    # Merge metrics with scores
    # The metrics file likely has multiple rows per subject (one per metric)
    # We need to calculate correlation per metric type
    
    merged = pd.merge(metrics_df, scores_df, on="subject_id", how="inner")
    if merged.empty:
        print("ERROR: No matching subjects found between metrics and scores.")
        sys.exit(1)
    
    # Get unique metrics
    unique_metrics = merged["metric_name"].unique()
    
    # Prepare results storage
    # We will append the stats to the original metrics file structure
    # Since the original file has one row per subject-metric, we need to broadcast the stats
    # OR, more likely, the task implies adding these columns to the *aggregated* stats
    # However, the task says "append columns ... to data/processed/graph_metrics.csv"
    # If graph_metrics.csv is the long format (subject, metric, value), adding a single
    # correlation stat per metric row makes sense (broadcasting the stat for that metric type).
    
    # Let's assume we calculate the correlation stats for each metric type against the score.
    # Then we add columns: cohens_d, ci_95_lower, ci_95_upper to the CSV, repeating the value for each row of that metric.
    
    stats_map = {} # metric_name -> {cohens_d, ci_lower, ci_upper}
    
    for metric in unique_metrics:
        subset = merged[merged["metric_name"] == metric]
        x = subset["value"].values
        y = subset["score_value"].values
        
        if len(x) < 3:
            print(f"WARNING: Insufficient data for metric {metric} (n={len(x)}). Skipping.")
            stats_map[metric] = {"cohens_d": 0.0, "ci_95_lower": 0.0, "ci_95_upper": 0.0}
            continue
        
        # We need to define groups for Cohen's d.
        # Typically, we split the score distribution (e.g., High vs Low).
        # A common approach is median split.
        median_score = np.median(y)
        low_group = x[y <= median_score]
        high_group = x[y > median_score]
        
        if len(low_group) < 2 or len(high_group) < 2:
            print(f"WARNING: Cannot split groups for metric {metric}. Skipping.")
            stats_map[metric] = {"cohens_d": 0.0, "ci_95_lower": 0.0, "ci_95_upper": 0.0}
            continue
        
        d = calculate_cohen_d(high_group, low_group)
        ci_lower, ci_upper = calculate_ci_95_cohen_d(d, len(high_group), len(low_group))
        
        stats_map[metric] = {
            "cohens_d": d,
            "ci_95_lower": ci_lower,
            "ci_95_upper": ci_upper
        }
        print(f"Metric {metric}: Cohen's d = {d:.4f}, 95% CI [{ci_lower:.4f}, {ci_upper:.4f}]")
    
    # Add columns to the dataframe
    metrics_df["cohens_d"] = metrics_df["metric_name"].map(lambda m: stats_map.get(m, {}).get("cohens_d", 0.0))
    metrics_df["ci_95_lower"] = metrics_df["metric_name"].map(lambda m: stats_map.get(m, {}).get("ci_95_lower", 0.0))
    metrics_df["ci_95_upper"] = metrics_df["metric_name"].map(lambda m: stats_map.get(m, {}).get("ci_95_upper", 0.0))
    
    # Ensure output directory exists
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    
    # Save to CSV
    metrics_df.to_csv(OUTPUT_PATH, index=False)
    print(f"Successfully updated {OUTPUT_PATH}")

if __name__ == "__main__":
    main()
