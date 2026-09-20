"""
Statistical analysis module for llmXive alignment study.
Implements Benjamini-Hochberg FDR and Bonferroni corrections.
"""
import os
import sys
import json
import argparse
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional
from scipy import stats

from config import get_processed_data_path, ensure_dirs
from simulation.rubric import calculate_alignment_score

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def load_simulation_data(input_path: str) -> pd.DataFrame:
    """Load simulation results from CSV."""
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def benjamini_hochberg_fdr(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Benjamini-Hochberg FDR correction.
    
    Args:
        p_values: Array of raw p-values
        alpha: Significance level
      
    Returns:
        Tuple of (adjusted p-values, boolean array of significant results)
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([], dtype=bool)
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = p_values[sorted_indices]
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        adjusted_p[sorted_indices[i]] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative minimum from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[sorted_indices[i]] = min(adjusted_p[sorted_indices[i]], 
                                             adjusted_p[sorted_indices[i + 1]])
    
    # Cap at 1.0
    adjusted_p = np.clip(adjusted_p, 0, 1.0)
    
    # Determine significance
    significant = adjusted_p < alpha
    
    return adjusted_p, significant

def bonferroni_correction(p_values: np.ndarray, alpha: float = 0.05) -> Tuple[np.ndarray, np.ndarray]:
    """
    Apply Bonferroni correction.
    
    Args:
        p_values: Array of raw p-values
        alpha: Significance level
      
    Returns:
        Tuple of (adjusted p-values, boolean array of significant results)
    """
    n = len(p_values)
    if n == 0:
        return np.array([]), np.array([], dtype=bool)
    
    # Adjust p-values
    adjusted_p = np.clip(p_values * n, 0, 1.0)
    
    # Determine significance
    significant = adjusted_p < alpha
    
    return adjusted_p, significant

def pairwise_ttest_with_fdr(df: pd.DataFrame, 
                             group_col: str, 
                             value_col: str, 
                             correction_method: str = 'fdr',
                             alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform pairwise t-tests with multiple comparison correction.
    
    Args:
        df: DataFrame with groups and values
        group_col: Column name for grouping
        value_col: Column name for values
        correction_method: 'fdr' or 'bonferroni'
        alpha: Significance level
    
    Returns:
        Dictionary with test results
    """
    groups = df[group_col].unique()
    if len(groups) < 2:
        return {"error": "Need at least 2 groups for pairwise comparison"}
    
    # Extract data for each group
    group_data = {g: df[df[group_col] == g][value_col].values for g in groups}
    
    # Perform all pairwise t-tests
    results = []
    p_values = []
    
    for i in range(len(groups)):
        for j in range(i + 1, len(groups)):
            g1, g2 = groups[i], groups[j]
            stat, p_val = stats.ttest_ind(group_data[g1], group_data[g2])
            results.append({
                'group1': g1,
                'group2': g2,
                'statistic': stat,
                'p_value': p_val
            })
            p_values.append(p_val)
    
    # Apply correction
    p_values = np.array(p_values)
    if correction_method == 'fdr':
        adjusted_p, significant = benjamini_hochberg_fdr(p_values, alpha)
    elif correction_method == 'bonferroni':
        adjusted_p, significant = bonferroni_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    # Update results
    for idx, result in enumerate(results):
        result['adjusted_p_value'] = adjusted_p[idx]
        result['significant'] = significant[idx]
    
    return {
        'correction_method': correction_method,
        'alpha': alpha,
        'tests': results,
        'summary': {
            'total_tests': len(results),
            'significant_count': int(sum(significant)),
            'non_significant_count': int(len(results) - sum(significant))
        }
    }

def analyze_alignment_scores_by_density(df: pd.DataFrame, 
                                         density_col: str = 'density_level',
                                         score_col: str = 'alignment_score',
                                         correction_method: str = 'fdr',
                                         alpha: float = 0.05) -> Dict[str, Any]:
    """
    Analyze alignment scores across density levels.
    
    Args:
        df: DataFrame with density levels and scores
        density_col: Column name for density levels
        score_col: Column name for alignment scores
        correction_method: 'fdr' or 'bonferroni'
        alpha: Significance level
    
    Returns:
        Dictionary with analysis results
    """
    logger.info(f"Analyzing alignment scores by {density_col}")
    
    # Check if columns exist
    if density_col not in df.columns or score_col not in df.columns:
        available_cols = list(df.columns)
        raise ValueError(f"Columns '{density_col}' and/or '{score_col}' not found. Available: {available_cols}")
    
    # Perform pairwise t-tests
    ttest_results = pairwise_ttest_with_fdr(df, density_col, score_col, correction_method, alpha)
    
    # Calculate summary statistics
    summary_stats = df.groupby(density_col)[score_col].agg(['mean', 'std', 'count'])
    
    return {
        'density_analysis': {
            'summary_statistics': summary_stats.to_dict(),
            'pairwise_tests': ttest_results
        }
    }

def find_latency_threshold(df: pd.DataFrame,
                            latency_col: str = 'total_latency_ms',
                            score_col: str = 'alignment_score',
                            threshold_pct: float = 0.95,
                            correction_method: str = 'fdr',
                            alpha: float = 0.05) -> Dict[str, Any]:
    """
    Identify the latency threshold where alignment scores significantly degrade.
    
    Args:
        df: DataFrame with latency and score data
        latency_col: Column name for latency
        score_col: Column name for alignment score
        threshold_pct: Percentile for threshold calculation
        correction_method: 'fdr' or 'bonferroni'
        alpha: Significance level
    
    Returns:
        Dictionary with threshold analysis
    """
    logger.info(f"Finding latency threshold using {correction_method} correction")
    
    # Bin data by latency
    latency_bins = pd.qcut(df[latency_col], q=10, duplicates='drop')
    df['latency_bin'] = latency_bins
    
    # Calculate mean score per bin
    bin_stats = df.groupby('latency_bin')[score_col].agg(['mean', 'std', 'count'])
    
    # Identify significant degradation points
    degradation_points = []
    p_values = []
    
    bins = sorted(bin_stats.index)
    for i in range(len(bins) - 1):
        bin1, bin2 = bins[i], bins[i+1]
        data1 = df[df['latency_bin'] == bin1][score_col]
        data2 = df[df['latency_bin'] == bin2][score_col]
        
        if len(data1) > 1 and len(data2) > 1:
            stat, p_val = stats.ttest_ind(data1, data2)
            p_values.append(p_val)
            degradation_points.append({
                'bin_from': str(bin1),
                'bin_to': str(bin2),
                'p_value': p_val,
                'mean_from': data1.mean(),
                'mean_to': data2.mean()
            })
    
    if not p_values:
        return {"error": "No valid degradation points found"}
    
    # Apply correction
    p_values = np.array(p_values)
    if correction_method == 'fdr':
        adjusted_p, significant = benjamini_hochberg_fdr(p_values, alpha)
    elif correction_method == 'bonferroni':
        adjusted_p, significant = bonferroni_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    # Find first significant degradation
    threshold = None
    for idx, point in enumerate(degradation_points):
        if significant[idx]:
            threshold = point['bin_to'].left  # Lower bound of the bin where degradation starts
            break
    
    # If no significant degradation, use the percentile
    if threshold is None:
        threshold = np.percentile(df[latency_col], threshold_pct)
    
    return {
        'threshold_ms': float(threshold),
        'threshold_method': 'statistical' if threshold is not None else 'percentile',
        'degradation_points': degradation_points,
        'correction_method': correction_method,
        'alpha': alpha,
        'significant_degradation_count': int(sum(significant))
    }

def calculate_power(n: int, effect_size: float, alpha: float = 0.05) -> float:
    """
    Calculate statistical power for a two-sample t-test.
    
    Args:
        n: Sample size per group
        effect_size: Cohen's d effect size
        alpha: Significance level
    
    Returns:
        Statistical power (probability of detecting effect if it exists)
    """
    # Using normal approximation for power calculation
    # For two-sample t-test: power = Φ(δ * sqrt(n/2) - z_{1-α/2})
    # where δ is effect size, z is critical value
    
    z_alpha = stats.norm.ppf(1 - alpha / 2)
    delta = effect_size * np.sqrt(n / 2)
    power = stats.norm.cdf(delta - z_alpha) + stats.norm.cdf(-delta - z_alpha)
    
    return float(power)

def validate_sample_size(n: int, effect_size: float = 0.5, alpha: float = 0.05, min_power: float = 0.8) -> bool:
    """
    Validate if sample size is sufficient for desired power.
    
    Args:
        n: Sample size per group
        effect_size: Expected effect size (Cohen's d)
        alpha: Significance level
        min_power: Minimum required power
    
    Returns:
        True if sample size is sufficient, False otherwise
    """
    power = calculate_power(n, effect_size, alpha)
    logger.info(f"Sample size {n} gives power {power:.3f} for effect size {effect_size}")
    return power >= min_power

def save_fdr_analysis_report(results: Dict[str, Any], output_path: str) -> None:
    """Save FDR analysis results to JSON."""
    ensure_dirs(Path(output_path))
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    logger.info(f"Saved analysis report to {output_path}")

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description='Statistical analysis for alignment study')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with simulation results')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for analysis report')
    parser.add_argument('--correction', type=str, default='fdr', choices=['fdr', 'bonferroni'],
                        help='Multiple comparison correction method')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_simulation_data(args.input)
        
        # Run density analysis
        density_results = analyze_alignment_scores_by_density(
            df, 
            correction_method=args.correction, 
            alpha=args.alpha
        )
        
        # Run threshold analysis
        threshold_results = find_latency_threshold(
            df,
            correction_method=args.correction,
            alpha=args.alpha
        )
        
        # Compile full report
        report = {
            'analysis_parameters': {
                'input_file': args.input,
                'correction_method': args.correction,
                'alpha': args.alpha
            },
            'density_analysis': density_results['density_analysis'],
            'threshold_analysis': threshold_results
        }
        
        # Save report
        save_fdr_analysis_report(report, args.output)
        
        print(f"Analysis complete. Report saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()