"""
Statistical analysis module for the llmXive A2UI latency study.

Provides functions for:
- Loading simulation data
- Benjamini-Hochberg FDR correction
- Bonferroni correction
- Pairwise t-tests with FDR
- Alignment score analysis by density
- Latency threshold identification
- Statistical power calculation
"""
import os
import sys
import json
import argparse
import logging
from pathlib import Path
import pandas as pd
import numpy as np
from scipy import stats
from typing import Dict, List, Tuple, Optional, Any

# Configure logging
logger = logging.getLogger(__name__)

def load_simulation_data(input_path: str) -> pd.DataFrame:
    """
    Load simulation results from a CSV file.
    
    Args:
        input_path: Path to the simulation results CSV file
        
    Returns:
        DataFrame containing simulation results
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")
    
    df = pd.read_csv(path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Benjamini-Hochberg FDR correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (rejection decisions, adjusted p-values)
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    # Sort p-values and keep track of original indices
    sorted_indices = np.argsort(p_values)
    sorted_p = np.array([p_values[i] for i in sorted_indices])
    
    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        adjusted_p[i] = sorted_p[i] * n / (i + 1)
    
    # Ensure monotonicity (cumulative minimum from the end)
    for i in range(n - 2, -1, -1):
        adjusted_p[i] = min(adjusted_p[i], adjusted_p[i + 1])
    
    # Make sure adjusted p-values don't exceed 1
    adjusted_p = np.clip(adjusted_p, 0, 1)
    
    # Determine rejections
    rejections = adjusted_p <= alpha
    
    # Restore original order
    final_rejections = [False] * n
    final_adjusted_p = [0.0] * n
    for i, idx in enumerate(sorted_indices):
        final_rejections[idx] = rejections[i]
        final_adjusted_p[idx] = adjusted_p[i]
    
    return final_rejections, final_adjusted_p

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Apply Bonferroni correction to a list of p-values.
    
    Args:
        p_values: List of raw p-values
        alpha: Significance level (default 0.05)
        
    Returns:
        Tuple of (rejection decisions, adjusted p-values)
    """
    n = len(p_values)
    if n == 0:
        return [], []
    
    adjusted_p = [min(p * n, 1.0) for p in p_values]
    rejections = [p <= alpha for p in adjusted_p]
    
    return rejections, adjusted_p

def pairwise_ttest_with_fdr(
    df: pd.DataFrame, 
    group_col: str, 
    value_col: str,
    alpha: float = 0.05,
    correction_method: str = 'fdr'
) -> Dict[str, Any]:
    """
    Perform pairwise t-tests between groups with FDR correction.
    
    Args:
        df: DataFrame containing the data
        group_col: Column name for grouping
        value_col: Column name for values to compare
        alpha: Significance level
        correction_method: 'fdr' or 'bonferroni'
        
    Returns:
        Dictionary containing test results
    """
    groups = df[group_col].unique()
    group_names = sorted([str(g) for g in groups])
    
    results = []
    p_values = []
    
    # Perform all pairwise t-tests
    for i in range(len(group_names)):
        for j in range(i + 1, len(group_names)):
            group1 = group_names[i]
            group2 = group_names[j]
            
            vals1 = df[df[group_col] == group1][value_col].values
            vals2 = df[df[group_col] == group2][value_col].values
            
            if len(vals1) == 0 or len(vals2) == 0:
                continue
            
            t_stat, p_val = stats.ttest_ind(vals1, vals2, equal_var=False)
            
            results.append({
                'group1': group1,
                'group2': group2,
                't_statistic': float(t_stat),
                'p_value': float(p_val),
                'n1': len(vals1),
                'n2': len(vals2)
            })
            p_values.append(p_val)
    
    # Apply correction
    if correction_method == 'fdr':
        rejections, adjusted_p = benjamini_hochberg_fdr(p_values, alpha)
    elif correction_method == 'bonferroni':
        rejections, adjusted_p = bonferroni_correction(p_values, alpha)
    else:
        raise ValueError(f"Unknown correction method: {correction_method}")
    
    # Attach results
    for i, result in enumerate(results):
        result['rejected'] = rejections[i]
        result['adjusted_p_value'] = adjusted_p[i]
    
    return {
        'tests': results,
        'correction_method': correction_method,
        'alpha': alpha,
        'total_tests': len(results),
        'significant_tests': sum(rejections)
    }

def analyze_alignment_scores_by_density(
    df: pd.DataFrame,
    density_col: str = 'density_level',
    score_col: str = 'alignment_score'
) -> Dict[str, Any]:
    """
    Analyze alignment scores across different density levels.
    
    Args:
        df: DataFrame containing simulation results
        density_col: Column name for density levels
        score_col: Column name for alignment scores
        
    Returns:
        Dictionary containing analysis results
    """
    analysis = {}
    
    for density in sorted(df[density_col].unique()):
        subset = df[df[density_col] == density]
        scores = subset[score_col].values
        
        analysis[str(density)] = {
            'mean': float(np.mean(scores)),
            'std': float(np.std(scores)),
            'median': float(np.median(scores)),
            'min': float(np.min(scores)),
            'max': float(np.max(scores)),
            'count': len(scores),
            'q25': float(np.percentile(scores, 25)),
            'q75': float(np.percentile(scores, 75))
        }
    
    return analysis

def find_latency_threshold(
    df: pd.DataFrame,
    latency_col: str = 'total_latency_ms',
    score_col: str = 'alignment_score',
    density_col: str = 'density_level',
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Identify the latency threshold where fidelity degrades significantly.
    
    Args:
        df: DataFrame containing simulation results
        latency_col: Column name for latency values
        score_col: Column name for alignment scores
        density_col: Column name for density levels
        alpha: Significance level
        
    Returns:
        Dictionary containing threshold analysis
    """
    # Sort by latency
    df_sorted = df.sort_values(by=latency_col)
    
    # Calculate rolling statistics
    window_size = max(5, len(df_sorted) // 10)
    df_sorted['rolling_mean'] = df_sorted[score_col].rolling(window=window_size, min_periods=1).mean()
    df_sorted['rolling_std'] = df_sorted[score_col].rolling(window=window_size, min_periods=1).std()
    
    # Find point of significant degradation
    threshold_data = {
        'threshold_latency_ms': None,
        'threshold_score': None,
        'p_value': None,
        'confidence_interval_95': None,
        'is_significant': False
    }
    
    # Compare each point to the baseline (first 20% of data)
    baseline_size = max(5, len(df_sorted) // 5)
    baseline_scores = df_sorted.iloc[:baseline_size][score_col].values
    baseline_mean = np.mean(baseline_scores)
    baseline_std = np.std(baseline_scores)
    
    for i in range(baseline_size, len(df_sorted)):
        current_score = df_sorted.iloc[i][score_col]
        current_latency = df_sorted.iloc[i][latency_col]
        
        # Z-score test against baseline
        if baseline_std > 0:
            z_score = (current_score - baseline_mean) / baseline_std
            p_val = 2 * (1 - stats.norm.cdf(abs(z_score)))
        else:
            p_val = 1.0
        
        if p_val < alpha:
            # Calculate 95% CI for the current point
            ci_low = current_score - 1.96 * baseline_std
            ci_high = current_score + 1.96 * baseline_std
            
            threshold_data = {
                'threshold_latency_ms': float(current_latency),
                'threshold_score': float(current_score),
                'p_value': float(p_val),
                'confidence_interval_95': [float(ci_low), float(ci_high)],
                'is_significant': True,
                'baseline_mean': float(baseline_mean),
                'baseline_std': float(baseline_std)
            }
            break
    
    return threshold_data

def calculate_power(
    n: int,
    effect_size: float,
    alpha: float = 0.05,
    alternative: str = 'two-sided'
) -> float:
    """
    Calculate statistical power for a two-sample t-test.
    
    Args:
        n: Sample size per group
        effect_size: Cohen's d effect size
        alpha: Significance level (default 0.05)
        alternative: Type of test ('two-sided', 'greater', 'less')
        
    Returns:
        Statistical power (probability of correctly rejecting null hypothesis)
        
    Raises:
        ValueError: If sample size is insufficient for the effect size
    """
    if n <= 0:
        raise ValueError("Sample size must be positive")
    if effect_size == 0:
        return alpha  # Power equals alpha when effect size is zero
    
    # Use scipy's power analysis
    # For two-sample t-test, we need to adjust for two groups
    try:
        # Calculate the non-centrality parameter
        # For two-sample t-test with equal n: ncp = d * sqrt(n/2)
        ncp = effect_size * np.sqrt(n / 2)
        
        # Degrees of freedom
        df = 2 * n - 2
        
        # Critical t-value
        if alternative == 'two-sided':
            crit_t = stats.t.ppf(1 - alpha/2, df)
        else:
            crit_t = stats.t.ppf(1 - alpha, df)
        
        # Calculate power
        # Power = P(t > crit_t | H1 is true)
        # Using non-central t-distribution
        if alternative == 'two-sided':
            power = (1 - stats.nct.cdf(crit_t, df, ncp)) + stats.nct.cdf(-crit_t, df, ncp)
        elif alternative == 'greater':
            power = 1 - stats.nct.cdf(crit_t, df, ncp)
        else:  # 'less'
            power = stats.nct.cdf(-crit_t, df, ncp)
        
        return float(power)
        
    except Exception as e:
        logger.warning(f"Power calculation failed: {e}")
        raise

def validate_sample_size(
    n: int,
    expected_effect_size: float = 0.5,
    min_power: float = 0.8,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Validate if sample size is sufficient for the expected effect size.
    
    Args:
        n: Sample size per group
        expected_effect_size: Expected Cohen's d
        min_power: Minimum required power (default 0.8)
        alpha: Significance level
        
    Returns:
        Dictionary with validation results
    """
    power = calculate_power(n, expected_effect_size, alpha)
    
    result = {
        'sample_size': n,
        'expected_effect_size': expected_effect_size,
        'calculated_power': power,
        'min_required_power': min_power,
        'is_sufficient': power >= min_power,
        'alpha': alpha
    }
    
    if not result['is_sufficient']:
        logger.warning(
            f"Sample size {n} is insufficient for effect size {expected_effect_size}. "
            f"Power: {power:.3f} < {min_power}"
        )
        # Calculate required sample size
        required_n = 0
        for test_n in range(n, 10000):
            test_power = calculate_power(test_n, expected_effect_size, alpha)
            if test_power >= min_power:
                required_n = test_n
                break
        
        result['required_sample_size'] = required_n if required_n > 0 else None
        result['power_deficit'] = min_power - power
    
    return result

def save_fdr_analysis_report(
    results: Dict[str, Any],
    output_path: str
) -> None:
    """
    Save FDR analysis results to a JSON file.
    
    Args:
        results: Dictionary containing analysis results
        output_path: Path for output JSON file
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2, default=str)
    
    logger.info(f"Saved FDR analysis report to {output_path}")

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description='Statistical analysis for A2UI latency study')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file with simulation results')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file for analysis report')
    parser.add_argument('--correction', type=str, default='fdr', choices=['fdr', 'bonferroni'],
                      help='Correction method for multiple comparisons')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        # Load data
        df = load_simulation_data(args.input)
        
        # Analyze by density
        density_analysis = analyze_alignment_scores_by_density(df)
        
        # Pairwise t-tests
        ttest_results = pairwise_ttest_with_fdr(
            df, 
            group_col='density_level', 
            value_col='alignment_score',
            alpha=args.alpha,
            correction_method=args.correction
        )
        
        # Find latency threshold
        threshold_results = find_latency_threshold(df)
        
        # Compile report
        report = {
            'density_analysis': density_analysis,
            'pairwise_tests': ttest_results,
            'latency_threshold': threshold_results,
            'parameters': {
                'alpha': args.alpha,
                'correction_method': args.correction
            }
        }
        
        # Save report
        save_fdr_analysis_report(report, args.output)
        
        print(f"Analysis complete. Report saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()
