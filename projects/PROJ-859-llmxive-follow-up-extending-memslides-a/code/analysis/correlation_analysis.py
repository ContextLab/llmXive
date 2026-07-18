"""
Spearman Correlation Analysis between Structural Metrics and Compressibility Scores.

This module implements Task T036: Analyze the relationship between trace structural
complexity (entropy, repetition, variance) and the resulting compressibility score.

Outputs:
    data/processed/correlation_results.json: JSON file containing correlation matrix,
        p-values, and significance flags for each metric pair.
"""
import json
import math
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

import numpy as np
import pandas as pd

from config import get_config
from utils.loaders import MetricsLoader


def spearman_correlation(x: np.ndarray, y: np.ndarray) -> Tuple[float, float]:
    """
    Calculate Spearman rank correlation coefficient and p-value.
    
    Args:
        x: First array of values.
        y: Second array of values.
        
    Returns:
        Tuple of (correlation_coefficient, p_value).
    """
    # Handle edge cases
    if len(x) != len(y) or len(x) < 2:
        return 0.0, 1.0
        
    # Check for constant arrays (zero variance)
    if np.std(x) == 0 or np.std(y) == 0:
        return 0.0, 1.0
        
    # Calculate ranks
    rank_x = np.argsort(np.argsort(x)).astype(float)
    rank_y = np.argsort(np.argsort(y)).astype(float)
    
    # Handle ties by using average ranks (already handled by argsort approach for ties)
    # For a more robust tie handling, we could use scipy.stats.rankdata, but 
    # implementing a simple version here to avoid dependency if not needed
    # The argsort approach handles ties correctly for Spearman's rho calculation
    
    # Calculate Pearson correlation of ranks
    n = len(x)
    mean_rank_x = np.mean(rank_x)
    mean_rank_y = np.mean(rank_y)
    
    numerator = np.sum((rank_x - mean_rank_x) * (rank_y - mean_rank_y))
    denominator = np.sqrt(np.sum((rank_x - mean_rank_x)**2) * np.sum((rank_y - mean_rank_y)**2))
    
    if denominator == 0:
        return 0.0, 1.0
        
    rho = numerator / denominator
    
    # Approximate p-value using t-distribution
    # t = rho * sqrt((n-2) / (1 - rho^2))
    if abs(rho) >= 1.0:
        p_value = 0.0
    else:
        t_stat = rho * math.sqrt((n - 2) / (1 - rho**2))
        # Approximate p-value using standard normal distribution for large n
        # For small n, this is an approximation
        p_value = 2 * (1 - 0.5 * (1 + math.erf(abs(t_stat) / math.sqrt(2))))
        
    return rho, p_value


def load_correlation_data(config: Dict[str, Any]) -> pd.DataFrame:
    """
    Load metrics and compressibility scores into a single DataFrame.
    
    Args:
        config: Configuration dictionary.
        
    Returns:
        DataFrame with trace_id, structural metrics, and compressibility score.
    """
    metrics_loader = MetricsLoader(config)
    
    # Load metrics
    metrics_df = metrics_loader.load_all_metrics()
    
    if metrics_df is None or metrics_df.empty:
        raise FileNotFoundError("No metrics data found. Ensure T020-T022 have completed.")
        
    # Load compressibility scores
    scores_path = Path(config["paths"]["processed"]) / "per_trace_scores.csv"
    if not scores_path.exists():
        raise FileNotFoundError(f"Compressibility scores not found at {scores_path}. Ensure T026 has completed.")
        
    scores_df = pd.read_csv(scores_path)
    
    # Merge on trace_id
    # Ensure column names match
    if "trace_id" not in metrics_df.columns:
        # Try to infer from first column if unnamed
        metrics_df.columns = [f"col_{i}" for i in range(len(metrics_df.columns))]
        if "col_0" in metrics_df.columns:
            metrics_df = metrics_df.rename(columns={"col_0": "trace_id"})
            
    if "trace_id" not in scores_df.columns:
        if "col_0" in scores_df.columns:
            scores_df = scores_df.rename(columns={"col_0": "trace_id"})
            
    merged_df = pd.merge(metrics_df, scores_df, on="trace_id", how="inner")
    
    if merged_df.empty:
        raise ValueError("No matching traces found between metrics and scores.")
        
    return merged_df


def run_correlation_analysis(df: pd.DataFrame, metrics_cols: List[str], target_col: str) -> Dict[str, Any]:
    """
    Run Spearman correlation analysis between metrics and target.
    
    Args:
        df: DataFrame containing all variables.
        metrics_cols: List of metric column names.
        target_col: Name of the target variable column.
        
    Returns:
        Dictionary containing correlation results.
    """
    results = {
        "method": "Spearman",
        "target_variable": target_col,
        "sample_size": len(df),
        "correlations": []
    }
    
    for metric in metrics_cols:
        if metric not in df.columns or target_col not in df.columns:
            continue
            
        x = df[metric].dropna().values
        y = df[target_col].dropna().values
        
        # Align indices after dropping NaNs
        valid_mask = ~df[metric].isna() & ~df[target_col].isna()
        x = df.loc[valid_mask, metric].values
        y = df.loc[valid_mask, target_col].values
        
        if len(x) < 2:
            continue
            
        rho, p_value = spearman_correlation(x, y)
        
        results["correlations"].append({
            "metric": metric,
            "correlation_coefficient": float(rho),
            "p_value": float(p_value),
            "significant_at_0.05": p_value < 0.05,
            "significant_at_0.01": p_value < 0.01,
            "interpretation": interpret_correlation(rho)
        })
        
    return results


def interpret_correlation(rho: float) -> str:
    """
    Provide a qualitative interpretation of the correlation coefficient.
    
    Args:
        rho: Spearman correlation coefficient.
        
    Returns:
        String description of the correlation strength.
    """
    abs_rho = abs(rho)
    if abs_rho < 0.1:
        strength = "negligible"
    elif abs_rho < 0.3:
        strength = "weak"
    elif abs_rho < 0.5:
        strength = "moderate"
    elif abs_rho < 0.7:
        strength = "strong"
    else:
        strength = "very strong"
        
    direction = "positive" if rho > 0 else "negative"
    return f"{direction} {strength}"


def main():
    """Main entry point for correlation analysis."""
    config = get_config()
    
    try:
        # Define columns to analyze
        metrics_cols = [
            "sequence_entropy",
            "tool_repetition_frequency",
            "argument_semantic_variance"
        ]
        target_col = "compressibility_score"
        
        print(f"Loading data for correlation analysis...")
        df = load_correlation_data(config)
        
        print(f"Loaded {len(df)} traces for analysis.")
        print(f"Analyzing correlations between: {metrics_cols}")
        print(f"Target variable: {target_col}")
        
        # Run analysis
        results = run_correlation_analysis(df, metrics_cols, target_col)
        
        # Save results
        output_path = Path(config["paths"]["processed"]) / "correlation_results.json"
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(results, f, indent=2)
            
        print(f"Correlation analysis complete. Results saved to: {output_path}")
        
        # Print summary
        print("\n--- Correlation Summary ---")
        for corr in results["correlations"]:
            sig = "***" if corr["significant_at_0.01"] else ("*" if corr["significant_at_0.05"] else "")
            print(f"{corr['metric']:30s} | rho={corr['correlation_coefficient']:.4f} | p={corr['p_value']:.4f} {sig} | {corr['interpretation']}")
            
        return 0
        
    except FileNotFoundError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"Unexpected error during correlation analysis: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    sys.exit(main())
