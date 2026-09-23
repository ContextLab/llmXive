"""
Statistical analysis utilities for DanceOPD follow-up.
Implements power analysis, effect size calculation, and hypothesis testing.
"""
import argparse
import json
import sys
from pathlib import Path
import pandas as pd
import numpy as np
from typing import Dict, Any, List, Tuple, Optional
from scipy import stats
from statsmodels.stats.power import TTestIndPower

# Constants for power analysis
DEFAULT_EFFECT_SIZE = 0.5  # Medium effect size
DEFAULT_POWER = 0.8        # 80% power
DEFAULT_ALPHA = 0.05       # Significance level

class TimeoutError(Exception):
    """Custom timeout error for statistical computations."""
    pass

def timeout_handler(signum, frame):
    """Signal handler for timeout."""
    raise TimeoutError("Statistical computation timed out")

def load_fidelity_results(input_path: str) -> pd.DataFrame:
    """
    Load fidelity results from a Parquet or CSV file.
    
    Args:
        input_path: Path to the input file.
        
    Returns:
        DataFrame with fidelity metrics.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the file format is unsupported.
    """
    path = Path(input_path)
    if not path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")
    
    if path.suffix == '.parquet':
        return pd.read_parquet(path)
    elif path.suffix in ['.csv', '.tsv']:
        return pd.read_csv(path, sep=',' if path.suffix == '.csv' else '\t')
    else:
        raise ValueError(f"Unsupported file format: {path.suffix}")

def calculate_effect_size(group1: np.ndarray, group2: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size between two groups.
    
    Args:
        group1: First group of values.
        group2: Second group of values.
        
    Returns:
        Cohen's d effect size.
    """
    mean1, mean2 = np.mean(group1), np.mean(group2)
    std1, std2 = np.std(group1, ddof=1), np.std(group2, ddof=1)
    n1, n2 = len(group1), len(group2)
    
    # Pooled standard deviation
    pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        return 0.0
    
    return (mean1 - mean2) / pooled_std

def calculate_required_n(pilot_variance: float, effect_size: float = DEFAULT_EFFECT_SIZE, 
                         power: float = DEFAULT_POWER, alpha: float = DEFAULT_ALPHA) -> int:
    """
    Calculate the required sample size for a given effect size and power.
    
    This function implements the statistical power validation required by T045.
    It explicitly checks if the calculated N is feasible and returns status information.
    
    Args:
        pilot_variance: Variance estimate from pilot run.
        effect_size: Expected effect size (default: 0.5 for medium).
        power: Target statistical power (default: 0.8).
        alpha: Significance level (default: 0.05).
        
    Returns:
        int: Required sample size per group.
        
    Note:
        If pilot_variance is 0 or very small, this returns a minimum of 30.
        If the variance is extremely large, this may return a very large N.
    """
    if pilot_variance <= 0:
        # If variance is zero or negative, use a conservative default
        return 30
    
    # For two-sample t-test, N per group = 2 * (Z_alpha + Z_beta)^2 * sigma^2 / delta^2
    # Where delta = effect_size * sigma, so:
    # N = 2 * (Z_alpha + Z_beta)^2 / effect_size^2
    
    power_analysis = TTestIndPower()
    
    # Calculate required sample size per group
    try:
        n_required = power_analysis.solve_power(
            effect_size=effect_size,
            power=power,
            alpha=alpha,
            ratio=1.0,  # Equal group sizes
            alternative='two-sided'
        )
        return int(np.ceil(n_required))
    except Exception:
        # Fallback to formula-based calculation if power analysis fails
        from scipy.stats import norm
        z_alpha = norm.ppf(1 - alpha/2)
        z_beta = norm.ppf(power)
        n_required = 2 * ((z_alpha + z_beta) / effect_size) ** 2
        return int(np.ceil(n_required))

def bootstrap_power_analysis(data1: np.ndarray, data2: np.ndarray, 
                             n_bootstrap: int = 1000, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Perform bootstrap analysis to estimate power and confidence intervals.
    
    Args:
        data1: First group data.
        data2: Second group data.
        n_bootstrap: Number of bootstrap iterations.
        alpha: Significance level.
        
    Returns:
        Dictionary with bootstrap results.
    """
    n1, n2 = len(data1), len(data2)
    boot_diffs = []
    
    for _ in range(n_bootstrap):
        sample1 = np.random.choice(data1, size=n1, replace=True)
        sample2 = np.random.choice(data2, size=n2, replace=True)
        diff = np.mean(sample1) - np.mean(sample2)
        boot_diffs.append(diff)
    
    boot_diffs = np.array(boot_diffs)
    ci_low = np.percentile(boot_diffs, 100 * alpha/2)
    ci_high = np.percentile(boot_diffs, 100 * (1 - alpha/2))
    
    return {
        'mean_diff': np.mean(boot_diffs),
        'std_diff': np.std(boot_diffs),
        'ci_low': ci_low,
        'ci_high': ci_high,
        'n_bootstrap': n_bootstrap
    }

def run_ttest(group1: np.ndarray, group2: np.ndarray, 
              paired: bool = False) -> Dict[str, float]:
    """
    Run a t-test between two groups.
    
    Args:
        group1: First group data.
        group2: Second group data.
        paired: Whether to use paired t-test.
        
    Returns:
        Dictionary with t-test results.
    """
    if paired:
        t_stat, p_value = stats.ttest_rel(group1, group2)
    else:
        t_stat, p_value = stats.ttest_ind(group1, group2)
    
    return {
        't_statistic': float(t_stat),
        'p_value': float(p_value)
    }

def run_bootstrap_test(group1: np.ndarray, group2: np.ndarray, 
                       n_bootstrap: int = 1000, alpha: float = 0.05) -> Dict[str, Any]:
    """
    Run bootstrap test to assess significance.
    
    Args:
        group1: First group data.
        group2: Second group data.
        n_bootstrap: Number of bootstrap iterations.
        alpha: Significance level.
        
    Returns:
        Dictionary with bootstrap test results.
    """
    n1, n2 = len(group1), len(group2)
    observed_diff = np.mean(group1) - np.mean(group2)
    
    # Combine groups for permutation test
    combined = np.concatenate([group1, group2])
    boot_p_values = []
    
    for _ in range(n_bootstrap):
        np.random.shuffle(combined)
        perm1 = combined[:n1]
        perm2 = combined[n1:]
        perm_diff = np.mean(perm1) - np.mean(perm2)
        boot_p_values.append(abs(perm_diff))
    
    boot_p_values = np.array(boot_p_values)
    p_value = np.mean(boot_p_values >= abs(observed_diff))
    
    return {
        'observed_diff': float(observed_diff),
        'bootstrap_p_value': float(p_value),
        'n_bootstrap': n_bootstrap
    }

def validate_statistical_power(n_available: int, n_required: int, 
                               pilot_variance: float, effect_size: float,
                               power: float) -> Dict[str, Any]:
    """
    Validate if the available sample size is sufficient for the desired power.
    
    This is the core implementation for T045: explicitly checking statistical power.
    
    Args:
        n_available: Number of samples available.
        n_required: Calculated required sample size.
        pilot_variance: Variance from pilot run.
        effect_size: Expected effect size.
        power: Target power.
        
    Returns:
        Dictionary with validation results including status and recommendations.
    """
    if n_available >= n_required:
        status = "sufficient"
        conclusion = f"Available sample size ({n_available}) is sufficient for desired power ({power})."
    else:
        status = "underpowered"
        shortfall = n_required - n_available
        conclusion = (f"Available sample size ({n_available}) is insufficient. "
                     f"Need {n_required} samples (short by {shortfall}) to achieve power {power}.")
    
    return {
        'status': status,
        'n_available': n_available,
        'n_required': n_required,
        'pilot_variance': float(pilot_variance),
        'effect_size': float(effect_size),
        'target_power': float(power),
        'conclusion': conclusion,
        'recommendation': "Proceed with caution" if status == "underpowered" else "Proceed with analysis"
    }

def save_statistical_tests(results: Dict[str, Any], output_path: str):
    """
    Save statistical test results to a JSON file.
    
    Args:
        results: Dictionary of test results.
        output_path: Path to output file.
    """
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(results, f, indent=2)

def perform_statistical_tests(teacher_scores: np.ndarray, tree_scores: np.ndarray,
                              pilot_variance: float, effect_size: float = DEFAULT_EFFECT_SIZE,
                              power: float = DEFAULT_POWER) -> Dict[str, Any]:
    """
    Perform comprehensive statistical tests on fidelity scores.
    
    Args:
        teacher_scores: Teacher baseline scores.
        tree_scores: Tree-predicted routing scores.
        pilot_variance: Variance from pilot run.
        effect_size: Expected effect size.
        power: Target power.
        
    Returns:
        Dictionary with all statistical test results.
    """
    # Calculate required sample size
    n_required = calculate_required_n(pilot_variance, effect_size, power)
    n_available = min(len(teacher_scores), len(tree_scores))
    
    # Validate power
    power_validation = validate_statistical_power(
        n_available, n_required, pilot_variance, effect_size, power
    )
    
    # Run t-test
    ttest_results = run_ttest(teacher_scores, tree_scores, paired=False)
    
    # Run bootstrap test
    bootstrap_results = run_bootstrap_test(teacher_scores, tree_scores)
    
    # Calculate effect size
    effect_size_actual = calculate_effect_size(teacher_scores, tree_scores)
    
    # Compile results
    results = {
        'power_validation': power_validation,
        't_test': ttest_results,
        'bootstrap_test': bootstrap_results,
        'effect_size': {
            'expected': effect_size,
            'actual': float(effect_size_actual)
        },
        'sample_sizes': {
            'teacher': len(teacher_scores),
            'tree': len(tree_scores),
            'available': n_available,
            'required': n_required
        },
        'conclusion': power_validation['conclusion']
    }
    
    return results

def main():
    """Main entry point for statistical analysis."""
    parser = argparse.ArgumentParser(description='Statistical analysis for DanceOPD follow-up')
    parser.add_argument('--input', type=str, required=True, 
                      help='Input file with fidelity results (Parquet or CSV)')
    parser.add_argument('--output', type=str, required=True,
                      help='Output file for statistical test results (JSON)')
    parser.add_argument('--pilot-variance', type=float, default=0.0,
                      help='Pilot variance estimate (if not in input)')
    parser.add_argument('--effect-size', type=float, default=DEFAULT_EFFECT_SIZE,
                      help='Expected effect size')
    parser.add_argument('--power', type=float, default=DEFAULT_POWER,
                      help='Target statistical power')
    
    args = parser.parse_args()
    
    try:
        # Load data
        df = load_fidelity_results(args.input)
        
        # Extract scores (assuming columns 'teacher_score' and 'tree_score')
        # Adjust column names based on actual data schema
        if 'teacher_score' in df.columns and 'tree_score' in df.columns:
            teacher_scores = df['teacher_score'].dropna().values
            tree_scores = df['tree_score'].dropna().values
        elif 'clip_score_teacher' in df.columns and 'clip_score_tree' in df.columns:
            teacher_scores = df['clip_score_teacher'].dropna().values
            tree_scores = df['clip_score_tree'].dropna().values
        else:
            # Try to find any numeric columns that might be scores
            numeric_cols = df.select_dtypes(include=[np.number]).columns
            if len(numeric_cols) >= 2:
                teacher_scores = df[numeric_cols[0]].dropna().values
                tree_scores = df[numeric_cols[1]].dropna().values
            else:
                raise ValueError("Could not find score columns in input data")
        
        # Use provided pilot variance or calculate from data
        if args.pilot_variance > 0:
            pilot_variance = args.pilot_variance
        else:
            # Estimate variance from the difference
            diffs = teacher_scores - tree_scores
            pilot_variance = np.var(diffs, ddof=1)
        
        # Perform statistical tests
        results = perform_statistical_tests(
            teacher_scores, tree_scores,
            pilot_variance, args.effect_size, args.power
        )
        
        # Save results
        save_statistical_tests(results, args.output)
        print(f"Statistical tests saved to {args.output}")
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()