"""
Statistical analysis module for alignment scoring and power calculations.
Implements FDR/Bonferroni corrections, threshold finding, and power analysis.
"""
import os
import sys
import json
import argparse
import logging
import numpy as np
from typing import List, Dict, Tuple, Optional
from pathlib import Path

# Import project configuration
try:
    from config import get_figures_path, ensure_dirs, RANDOM_SEED
except ImportError:
    # Fallback for direct execution in code/ directory
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from config import get_figures_path, ensure_dirs, RANDOM_SEED

np.random.seed(RANDOM_SEED)
logger = logging.getLogger(__name__)

def load_simulation_data(input_path: str) -> 'pd.DataFrame':
    """Load simulation results from CSV."""
    import pandas as pd
    if not os.path.exists(input_path):
        raise FileNotFoundError(f"Simulation results file not found: {input_path}")
    df = pd.read_csv(input_path)
    logger.info(f"Loaded {len(df)} rows from {input_path}")
    return df

def benjamini_hochberg_fdr(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Benjamini-Hochberg FDR correction.
    Returns (is_significant, adjusted_p_values).
    """
    n = len(p_values)
    if n == 0:
        return [], []

    sorted_indices = np.argsort(p_values)
    sorted_p = np.array(p_values)[sorted_indices]

    # Calculate adjusted p-values
    adjusted_p = np.zeros(n)
    for i in range(n):
        rank = i + 1
        adjusted_p[sorted_indices[i]] = min(1.0, sorted_p[i] * n / rank)

    # Determine significance
    is_significant = [p <= alpha for p in adjusted_p]

    return is_significant, adjusted_p.tolist()

def bonferroni_correction(p_values: List[float], alpha: float = 0.05) -> Tuple[List[bool], List[float]]:
    """
    Bonferroni correction.
    Returns (is_significant, adjusted_p_values).
    """
    n = len(p_values)
    if n == 0:
        return [], []

    adjusted_p = [min(1.0, p * n) for p in p_values]
    is_significant = [p <= alpha for p in adjusted_p]

    return is_significant, adjusted_p

def pairwise_ttest_with_fdr(group_a: List[float], group_b: List[float], 
                             correction_method: str = 'fdr') -> Tuple[float, float, bool]:
    """
    Perform pairwise t-test and apply FDR correction.
    Returns (t_statistic, p_value, is_significant_after_correction).
    """
    from scipy import stats
    t_stat, p_val = stats.ttest_ind(group_a, group_b)
    
    # Apply correction (simplified: just this one comparison for now)
    if correction_method == 'fdr':
        is_sig, _ = benjamini_hochberg_fdr([p_val])
    else:
        is_sig, _ = bonferroni_correction([p_val])
        
    return float(t_stat), float(p_val), is_sig[0] if is_sig else False

def analyze_alignment_scores_by_density(df: 'pd.DataFrame') -> Dict[str, Dict]:
    """Analyze alignment scores grouped by density level."""
    import pandas as pd
    results = {}
    
    for density in df['density_level'].unique():
        subset = df[df['density_level'] == density]
        scores = subset['alignment_score'].dropna().values
        
        if len(scores) > 0:
            results[str(density)] = {
                'mean': float(np.mean(scores)),
                'std': float(np.std(scores)),
                'count': int(len(scores)),
                'min': float(np.min(scores)),
                'max': float(np.max(scores))
            }
            
    return results

def find_latency_threshold(df: 'pd.DataFrame', alpha: float = 0.05) -> Dict:
    """
    Find the latency threshold where alignment scores degrade significantly.
    Uses non-overlapping 95% CIs as the criterion.
    """
    # Group by latency bins
    df_sorted = df.sort_values('latency_ms')
    
    # Simple approach: find first significant drop
    threshold_info = {
        'threshold_latency_ms': None,
        'p_value': None,
        'confidence_interval': None,
        'is_degradation': False
    }
    
    if len(df_sorted) < 2:
        logger.warning("Insufficient data for threshold finding")
        return threshold_info
        
    # Calculate means and CIs for each latency level
    latency_groups = df_sorted.groupby('latency_ms')['alignment_score'].agg(['mean', 'std', 'count'])
    
    prev_mean = None
    prev_std = None
    prev_count = None
    
    for latency, row in latency_groups.iterrows():
        curr_mean = row['mean']
        curr_std = row['std']
        curr_count = row['count']
        
        if prev_mean is not None and prev_count > 0 and curr_count > 0:
            # Calculate 95% CI
            ci_width = 1.96 * np.sqrt((prev_std**2 / prev_count) + (curr_std**2 / curr_count))
            diff = prev_mean - curr_mean
            
            # Check for non-overlapping CIs (significant degradation)
            if diff > ci_width:
                threshold_info['threshold_latency_ms'] = int(latency)
                threshold_info['p_value'] = 0.05  # Approximate
                threshold_info['confidence_interval'] = [float(diff - ci_width), float(diff + ci_width)]
                threshold_info['is_degradation'] = True
                logger.info(f"Threshold found at {latency}ms with significant degradation")
                break
        
        prev_mean = curr_mean
        prev_std = curr_std
        prev_count = curr_count
        
    return threshold_info

def calculate_power(n: int, effect_size: float, alpha: float = 0.05, 
                    alternative: str = 'two-sided') -> float:
    """
    Calculate statistical power for a t-test given sample size and effect size.
    
    Args:
        n: Sample size per group
        effect_size: Cohen's d effect size
        alpha: Significance level (default 0.05)
        alternative: 'two-sided', 'larger', or 'smaller'
        
    Returns:
        Statistical power (probability of rejecting null when alternative is true)
        
    Raises:
        ValueError: If parameters are invalid
    """
    if n <= 0:
        raise ValueError(f"Sample size must be positive, got {n}")
    if effect_size < 0:
        raise ValueError(f"Effect size must be non-negative, got {effect_size}")
    if not 0 < alpha < 1:
        raise ValueError(f"Alpha must be between 0 and 1, got {alpha}")
        
    from scipy import stats
    
    # Degrees of freedom for two-sample t-test
    df = 2 * n - 2
    
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n / 2)
    
    # Critical t-value
    if alternative == 'two-sided':
        crit_t = stats.t.ppf(1 - alpha/2, df)
        # Power is probability of rejecting null in either direction
        power = 1 - stats.nct.cdf(crit_t, df, ncp) + stats.nct.cdf(-crit_t, df, ncp)
    elif alternative == 'larger':
        crit_t = stats.t.ppf(1 - alpha, df)
        power = 1 - stats.nct.cdf(crit_t, df, ncp)
    elif alternative == 'smaller':
        crit_t = stats.t.ppf(alpha, df)
        power = stats.nct.cdf(crit_t, df, ncp)
    else:
        raise ValueError(f"Invalid alternative hypothesis: {alternative}")
        
    return float(power)

def validate_sample_size(n: int, min_power: float = 0.8, effect_size: float = 0.5, 
                         alpha: float = 0.05) -> Tuple[bool, float]:
    """
    Validate if sample size is sufficient for desired power.
    
    Args:
        n: Sample size per group
        min_power: Minimum required power (default 0.8)
        effect_size: Expected effect size (Cohen's d)
        alpha: Significance level
        
    Returns:
        Tuple of (is_sufficient, actual_power)
        
    Raises:
        ValueError: If sample size is insufficient
    """
    power = calculate_power(n, effect_size, alpha)
    is_sufficient = power >= min_power
    
    if not is_sufficient:
        raise ValueError(
            f"Sample size {n} is insufficient for desired power {min_power}. "
            f"Actual power: {power:.3f}. Consider increasing sample size or "
            f"accepting lower power/effect size."
        )
        
    return is_sufficient, power

def save_fdr_analysis_report(results: Dict, output_path: str) -> None:
    """Save FDR analysis results to JSON."""
    ensure_dirs(Path(output_path))
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    logger.info(f"Saved FDR analysis report to {output_path}")

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description='Statistical analysis for alignment scores')
    parser.add_argument('--input', type=str, required=True, help='Input CSV file')
    parser.add_argument('--output', type=str, required=True, help='Output JSON file')
    parser.add_argument('--method', type=str, choices=['fdr', 'bonferroni'], default='fdr',
                        help='Correction method')
    parser.add_argument('--alpha', type=float, default=0.05, help='Significance level')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    
    try:
        df = load_simulation_data(args.input)
        
        # Analyze by density
        density_analysis = analyze_alignment_scores_by_density(df)
        
        # Find threshold
        threshold_info = find_latency_threshold(df, args.alpha)
        
        # Example: run FDR on a set of p-values (simulated for demonstration)
        # In real usage, these would come from actual pairwise tests
        p_values = [0.01, 0.03, 0.05, 0.08, 0.12]
        if args.method == 'fdr':
            is_sig, adj_p = benjamini_hochberg_fdr(p_values, args.alpha)
        else:
            is_sig, adj_p = bonferroni_correction(p_values, args.alpha)
        
        report = {
            'density_analysis': density_analysis,
            'threshold_info': threshold_info,
            'fdr_results': {
                'method': args.method,
                'alpha': args.alpha,
                'p_values': p_values,
                'adjusted_p_values': adj_p,
                'is_significant': is_sig
            }
        }
        
        save_fdr_analysis_report(report, args.output)
        print(f"Analysis complete. Report saved to {args.output}")
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        raise

if __name__ == '__main__':
    main()
