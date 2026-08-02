"""
Statistical analysis module for correlating graph metrics with behavioral scores.
Implements Bonferroni correction for multiple comparisons as per Constitution Principle VII.
"""
import os
import sys
import csv
import json
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional

import numpy as np
import pandas as pd
from scipy import stats as scipy_stats


def load_graph_metrics(csv_path: str) -> pd.DataFrame:
    """
    Load graph metrics from a CSV file.
    Expected columns: subject_id, metric_name, value
    """
    if not os.path.exists(csv_path):
        raise FileNotFoundError(f"Graph metrics file not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    required_cols = {'subject_id', 'metric_name', 'value'}
    if not required_cols.issubset(df.columns):
        raise ValueError(f"CSV missing required columns. Found: {df.columns}, Expected: {required_cols}")
    return df


def load_behavioral_scores(json_path: str) -> Dict[str, float]:
    """
    Load behavioral scores (Fluid Intelligence) from a JSON file.
    Expected format: {"subject_id": score_value, ...}
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Behavioral scores file not found: {json_path}")
    
    with open(json_path, 'r') as f:
        data = json.load(f)
    
    # Ensure we have a dict mapping subject_id to score
    if not isinstance(data, dict):
        raise ValueError("Behavioral scores JSON must be a dictionary mapping subject_id to score.")
    
    return data


def merge_metrics_with_scores(metrics_df: pd.DataFrame, scores_dict: Dict[str, float]) -> pd.DataFrame:
    """
    Merge graph metrics with behavioral scores.
    Returns a DataFrame with columns: subject_id, metric_name, value, score
    """
    # Create a DataFrame from the scores dict
    scores_df = pd.DataFrame(list(scores_dict.items()), columns=['subject_id', 'score'])
    
    # Merge with metrics
    merged = pd.merge(metrics_df, scores_df, on='subject_id', how='inner')
    
    if merged.empty:
        raise ValueError("No matching subjects found between graph metrics and behavioral scores.")
    
    return merged


def compute_correlation(
    df: pd.DataFrame, 
    metric_name: str, 
    method: str = 'pearson'
) -> Tuple[float, float]:
    """
    Compute correlation between a specific metric and scores.
    Returns (correlation_coefficient, p_value).
    """
    subset = df[df['metric_name'] == metric_name]
    if subset.empty:
        raise ValueError(f"No data found for metric: {metric_name}")
    
    x = subset['value'].values
    y = subset['score'].values
    
    if len(x) < 3:
        raise ValueError(f"Insufficient data points for correlation on {metric_name}: {len(x)}")
    
    if method == 'pearson':
        corr, p_val = scipy_stats.pearsonr(x, y)
    elif method == 'spearman':
        corr, p_val = scipy_stats.spearmanr(x, y)
    else:
        raise ValueError(f"Unsupported correlation method: {method}")
    
    return float(corr), float(p_val)


def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Dict[str, Any]:
    """
    Apply Bonferroni correction for multiple comparisons.
    
    Args:
        p_values: List of raw p-values from hypothesis tests.
        alpha: Significance level (default 0.05).
    
    Returns:
        Dictionary containing:
            - 'adjusted_alpha': The corrected alpha threshold (alpha / n_tests).
            - 'significant_indices': List of indices where p < adjusted_alpha.
            - 'adjusted_p_values': List of p-values multiplied by n_tests (capped at 1.0).
            - 'summary': A string summary of the results.
    """
    if not p_values:
        return {
            'adjusted_alpha': alpha,
            'significant_indices': [],
            'adjusted_p_values': [],
            'summary': "No p-values provided."
        }
    
    n_tests = len(p_values)
    adjusted_alpha = alpha / n_tests
    
    adjusted_p_values = [min(p * n_tests, 1.0) for p in p_values]
    significant_indices = [i for i, p in enumerate(adjusted_p_values) if p < alpha]
    
    summary = (
        f"Bonferroni Correction Results:\n"
        f"  Number of tests: {n_tests}\n"
        f"  Original alpha: {alpha}\n"
        f"  Adjusted alpha threshold: {adjusted_alpha:.6f}\n"
        f"  Significant results: {len(significant_indices)}\n"
        f"  Significant indices: {significant_indices}"
    )
    
    return {
        'adjusted_alpha': adjusted_alpha,
        'significant_indices': significant_indices,
        'adjusted_p_values': adjusted_p_values,
        'summary': summary
    }


def analyze_correlations(
    metrics_df: pd.DataFrame,
    scores_dict: Dict[str, float],
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform correlation analysis between all metrics and behavioral scores,
    applying Bonferroni correction for multiple comparisons.
    
    Args:
        metrics_df: DataFrame of graph metrics.
        scores_dict: Dictionary of behavioral scores.
        alpha: Significance level.
    
    Returns:
        Dictionary containing analysis results and corrected p-values.
    """
    merged_df = merge_metrics_with_scores(metrics_df, scores_dict)
    unique_metrics = merged_df['metric_name'].unique()
    
    results = []
    p_values = []
    metric_names = []
    
    for metric in unique_metrics:
        try:
            corr, p_val = compute_correlation(merged_df, metric)
            results.append({
                'metric': metric,
                'correlation': corr,
                'p_value': p_val
            })
            p_values.append(p_val)
            metric_names.append(metric)
        except ValueError as e:
            print(f"Warning: Skipping {metric} due to error: {e}", file=sys.stderr)
    
    if not p_values:
        return {
            'results': [],
            'correction': bonferroni_correction([], alpha),
            'summary': "No valid correlations computed."
        }
    
    correction = bonferroni_correction(p_values, alpha)
    
    # Attach adjusted p-values to results
    for i, res in enumerate(results):
        res['adjusted_p_value'] = correction['adjusted_p_values'][i]
        res['is_significant'] = i in correction['significant_indices']
    
    return {
        'results': results,
        'correction': correction,
        'summary': correction['summary']
    }


def main():
    """
    Main entry point for statistical analysis.
    Loads data, computes correlations, applies Bonferroni correction,
    and prints the summary.
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent
    metrics_path = project_root / "data" / "processed" / "graph_metrics.csv"
    scores_path = project_root / "data" / "processed" / "behavioral_scores.json"
    
    print(f"Loading graph metrics from: {metrics_path}")
    try:
        metrics_df = load_graph_metrics(str(metrics_path))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print(f"Loading behavioral scores from: {scores_path}")
    try:
        scores_dict = load_behavioral_scores(str(scores_path))
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)
    
    print("Performing correlation analysis with Bonferroni correction...")
    try:
        analysis_results = analyze_correlations(metrics_df, scores_dict)
    except ValueError as e:
        print(f"Error during analysis: {e}", file=sys.stderr)
        sys.exit(1)
    
    # Print summary
    print("\n" + "="*50)
    print(analysis_results['summary'])
    print("="*50 + "\n")
    
    # Print detailed results
    print("Detailed Results:")
    print(f"{'Metric':<30} {'Correlation':<12} {'Raw P':<12} {'Adj P':<12} {'Significant'}")
    print("-" * 80)
    
    for res in analysis_results['results']:
        sig_str = "YES" if res['is_significant'] else "NO"
        print(f"{res['metric']:<30} {res['correlation']:<12.4f} {res['p_value']:<12.4e} {res['adjusted_p_value']:<12.4e} {sig_str}")
    
    print("\nAnalysis complete.")


if __name__ == "__main__":
    main()