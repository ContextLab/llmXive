import os
import sys
import json
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, List, Tuple, Optional
from scipy import stats

from config import get_processed_data_path, get_figures_path, ensure_dirs
from utils.logging import get_experiment_logger, log_info, log_error

logger = get_experiment_logger(__name__)

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (boolean rejection list, adjusted p-values)
    """
    n = len(p_values)
    if n == 0:
        return [], []
        
    # Sort p-values and keep track of original indices
    indexed_p_values = list(enumerate(p_values))
    sorted_p_values = sorted(indexed_p_values, key=lambda x: x[1])
    
    # Calculate adjusted p-values
    adjusted_p_values = [0.0] * n
    rank = 1
    
    # Work backwards to ensure monotonicity
    prev_adj = 1.0
    for idx, p_val in reversed(sorted_p_values):
        # BH adjusted p-value: p * n / rank
        adj_p = p_val * n / rank
        # Ensure monotonicity (adjusted p-values should not decrease as rank increases)
        adj_p = min(adj_p, prev_adj)
        adjusted_p_values[idx] = adj_p
        prev_adj = adj_p
        rank += 1
        
    # Determine rejections
    rejections = [p < alpha for p in adjusted_p_values]
    
    return rejections, adjusted_p_values

def pairwise_ttest_with_fdr(
    group1_scores: List[float],
    group2_scores: List[float],
    alpha: float = 0.05
) -> Dict[str, float]:
    """
    Perform independent t-test between two groups and apply FDR correction.
    
    Args:
        group1_scores: Scores from group 1 (e.g., hybrid model)
        group2_scores: Scores from group 2 (e.g., generative baseline)
        alpha: Significance level
        
    Returns:
        Dictionary with t-statistic, p-value, and FDR-adjusted p-value
    """
    t_stat, p_val = stats.ttest_ind(group1_scores, group2_scores, equal_var=False)
    
    # For single comparison, FDR adjustment is trivial but included for API consistency
    _, adjusted_p = benjamini_hochberg_fdr([p_val], alpha)
    
    return {
        "t_statistic": float(t_stat),
        "p_value": float(p_val),
        "adjusted_p_value": float(adjusted_p[0]) if adjusted_p else float('nan'),
        "significant": float(adjusted_p[0]) < alpha if adjusted_p else False
    }

def analyze_alignment_scores_by_density(
    df: pd.DataFrame,
    density_col: str = "density_level",
    score_col: str = "alignment_score",
    model_col: str = "model_type",
    alpha: float = 0.05
) -> Dict[str, any]:
    """
    Analyze alignment scores by density level and model type.
    
    Args:
        df: DataFrame with simulation results
        density_col: Column name for density levels
        score_col: Column name for alignment scores
        model_col: Column name for model types
        alpha: Significance level
        
    Returns:
        Dictionary with analysis results per density level
    """
    results = {}
    
    for density in sorted(df[density_col].unique()):
        density_df = df[df[density_col] == density]
        
        hybrid_scores = density_df[density_df[model_col] == "hybrid"][score_col].dropna()
        baseline_scores = density_df[density_df[model_col] == "generative_baseline"][score_col].dropna()
        
        if len(hybrid_scores) == 0 or len(baseline_scores) == 0:
            continue
            
        # Calculate means and confidence intervals
        hybrid_mean = hybrid_scores.mean()
        hybrid_std = hybrid_scores.std()
        hybrid_n = len(hybrid_scores)
        hybrid_ci_lower = hybrid_mean - 1.96 * hybrid_std / np.sqrt(hybrid_n)
        hybrid_ci_upper = hybrid_mean + 1.96 * hybrid_std / np.sqrt(hybrid_n)
        
        baseline_mean = baseline_scores.mean()
        baseline_std = baseline_scores.std()
        baseline_n = len(baseline_scores)
        baseline_ci_lower = baseline_mean - 1.96 * baseline_std / np.sqrt(baseline_n)
        baseline_ci_upper = baseline_mean + 1.96 * baseline_std / np.sqrt(baseline_n)
        
        # Perform t-test
        t_test_result = pairwise_ttest_with_fdr(
            hybrid_scores.tolist(),
            baseline_scores.tolist(),
            alpha
        )
        
        results[density] = {
            "hybrid": {
                "mean": float(hybrid_mean),
                "std": float(hybrid_std),
                "n": int(hybrid_n),
                "ci_lower": float(hybrid_ci_lower),
                "ci_upper": float(hybrid_ci_upper)
            },
            "baseline": {
                "mean": float(baseline_mean),
                "std": float(baseline_std),
                "n": int(baseline_n),
                "ci_lower": float(baseline_ci_lower),
                "ci_upper": float(baseline_ci_upper)
            },
            "t_test": t_test_result
        }
        
    return results

def find_latency_threshold(
    df: pd.DataFrame,
    latency_col: str = "total_latency",
    score_col: str = "alignment_score",
    model_col: str = "model_type",
    alpha: float = 0.05
) -> Optional[float]:
    """
    Identify the latency threshold where generative baseline CI drops below 
    hybrid model CI (p < 0.05).
    
    This function sorts unique latency values and checks at each point whether
    the generative baseline's confidence interval is significantly lower than
    the hybrid model's.
    
    Args:
        df: DataFrame with simulation results
        latency_col: Column name for latency values
        score_col: Column name for alignment scores
        model_col: Column name for model types
        alpha: Significance level
        
    Returns:
        The latency threshold value if found, None otherwise
    """
    # Get unique latency values sorted
    unique_latencies = sorted(df[latency_col].unique())
    
    if len(unique_latencies) < 2:
        log_info("Not enough unique latency values to determine threshold")
        return None
        
    threshold = None
    
    for i in range(len(unique_latencies)):
        current_latency = unique_latencies[i]
        
        # Filter data up to and including current latency
        mask = df[latency_col] <= current_latency
        subset_df = df[mask]
        
        # Separate by model type
        hybrid_scores = subset_df[subset_df[model_col] == "hybrid"][score_col].dropna()
        baseline_scores = subset_df[subset_df[model_col] == "generative_baseline"][score_col].dropna()
        
        if len(hybrid_scores) < 5 or len(baseline_scores) < 5:
            continue
            
        # Calculate confidence intervals
        hybrid_mean = hybrid_scores.mean()
        hybrid_std = hybrid_scores.std()
        hybrid_n = len(hybrid_scores)
        hybrid_ci_lower = hybrid_mean - 1.96 * hybrid_std / np.sqrt(hybrid_n)
        
        baseline_mean = baseline_scores.mean()
        baseline_std = baseline_scores.std()
        baseline_n = len(baseline_scores)
        baseline_ci_upper = baseline_mean + 1.96 * baseline_std / np.sqrt(baseline_n)
        
        # Check if baseline CI is below hybrid CI
        # Specifically: baseline upper CI < hybrid lower CI
        if baseline_ci_upper < hybrid_ci_lower:
            # Perform t-test to confirm significance
            t_test_result = pairwise_ttest_with_fdr(
                hybrid_scores.tolist(),
                baseline_scores.tolist(),
                alpha
            )
            
            if t_test_result["significant"]:
                threshold = current_latency
                log_info(f"Found threshold at latency {threshold}: "
                         f"baseline_ci_upper={baseline_ci_upper:.4f} < hybrid_ci_lower={hybrid_ci_lower:.4f}, "
                         f"p={t_test_result['adjusted_p_value']:.4f}")
                break
                
    return threshold

def save_fdr_analysis_report(
    results: Dict,
    threshold: Optional[float],
    output_path: Path
) -> None:
    """
    Save the FDR analysis results and threshold to a JSON file.
    
    Args:
        results: Analysis results from analyze_alignment_scores_by_density
        threshold: Identified latency threshold
        output_path: Path to save the report
    """
    report = {
        "analysis_by_density": results,
        "latency_threshold": threshold,
        "threshold_description": (
            f"Latency threshold where generative baseline CI drops below hybrid model CI (p < 0.05)"
            if threshold is not None 
            else "No significant threshold found"
        )
    }
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)
        
    log_info(f"Saved FDR analysis report to {output_path}")

def main():
    """
    Main entry point for latency threshold analysis.
    
    Reads simulation results, performs FDR-corrected statistical tests,
    identifies the latency threshold, and saves the report.
    """
    parser = argparse.ArgumentParser(
        description="Identify latency threshold where generative baseline CI drops below hybrid model CI"
    )
    parser.add_argument(
        "--input",
        type=str,
        default=None,
        help="Path to simulation results CSV (default: uses config path)"
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Path to output report JSON (default: uses config path)"
    )
    parser.add_argument(
        "--alpha",
        type=float,
        default=0.05,
        help="Significance level for FDR correction (default: 0.05)"
    )
    
    args = parser.parse_args()
    
    # Determine input path
    if args.input:
        input_path = Path(args.input)
    else:
        input_path = get_processed_data_path() / "simulation_results.csv"
        
    if not input_path.exists():
        log_error(f"Input file not found: {input_path}")
        sys.exit(1)
        
    # Determine output path
    if args.output:
        output_path = Path(args.output)
    else:
        output_path = get_figures_path() / "fdr_analysis_report.json"
        
    log_info(f"Loading simulation results from {input_path}")
    df = pd.read_csv(input_path)
    
    # Verify required columns
    required_cols = ["alignment_score", "model_type", "total_latency"]
    missing_cols = [col for col in required_cols if col not in df.columns]
    if missing_cols:
        log_error(f"Missing required columns: {missing_cols}")
        sys.exit(1)
        
    # Perform analysis by density
    log_info("Analyzing alignment scores by density level")
    density_results = analyze_alignment_scores_by_density(
        df,
        score_col="alignment_score",
        model_col="model_type",
        alpha=args.alpha
    )
    
    # Find latency threshold
    log_info("Searching for latency threshold")
    threshold = find_latency_threshold(
        df,
        latency_col="total_latency",
        score_col="alignment_score",
        model_col="model_type",
        alpha=args.alpha
    )
    
    # Save report
    save_fdr_analysis_report(density_results, threshold, output_path)
    
    # Print summary
    log_info("=" * 60)
    log_info("LATENCY THRESHOLD ANALYSIS SUMMARY")
    log_info("=" * 60)
    if threshold is not None:
        log_info(f"✓ Latency threshold identified: {threshold:.4f}s")
        log_info("  At this point, generative baseline performance is significantly")
        log_info("  worse than hybrid model (p < 0.05, FDR corrected).")
    else:
        log_info("✗ No significant latency threshold found at p < 0.05")
        log_info("  Generative baseline did not show statistically significant")
        log_info("  degradation relative to hybrid model at any tested latency.")
    log_info("=" * 60)
    
    return threshold

if __name__ == "__main__":
    main()