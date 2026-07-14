import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional, Tuple

# Import from local project modules
from config import get_config, ensure_dirs
from utils import setup_logging, log_info, log_warning, get_timestamp

# Import analysis functions
from analysis import welch_t_test, calculate_cohen_d

def load_cleaned_dataset() -> Optional[pd.DataFrame]:
    """Load the cleaned dataset from data/processed/cleaned_dataset.csv."""
    config = get_config()
    path = Path(config['paths']['data_processed']) / 'cleaned_dataset.csv'
    
    if not path.exists():
        log_warning(f"Cleaned dataset not found at {path}. Skipping power analysis.")
        return None
    
    try:
        df = pd.read_csv(path)
        log_info(f"Loaded cleaned dataset with {len(df)} records from {path}")
        return df
    except Exception as e:
        log_warning(f"Failed to load cleaned dataset: {e}")
        return None

def load_statistical_report() -> Dict[str, Any]:
    """Load existing statistical report from data/results/statistical_report.json."""
    config = get_config()
    path = Path(config['paths']['data_results']) / 'statistical_report.json'
    
    if path.exists():
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except Exception as e:
            log_warning(f"Failed to load existing statistical report: {e}")
            return {}
    return {}

def save_statistical_report(report: Dict[str, Any]) -> None:
    """Save statistical report to data/results/statistical_report.json."""
    config = get_config()
    ensure_dirs()
    path = Path(config['paths']['data_results']) / 'statistical_report.json'
    
    with open(path, 'w') as f:
        json.dump(report, f, indent=2)
    log_info(f"Saved updated statistical report to {path}")

def calculate_power_and_mdes(
    effect_size: float,
    n1: int,
    n2: int,
    alpha: float = 0.05,
    alternative: str = 'two-sided'
) -> Tuple[float, float]:
    """
    Calculate statistical power and Minimum Detectable Effect Size (MDES).
    
    Args:
        effect_size: Cohen's d (standardized effect size)
        n1: Sample size of group 1
        n2: Sample size of group 2
        alpha: Significance level (default 0.05)
        alternative: Type of test ('two-sided', 'greater', 'less')
    
    Returns:
        Tuple of (power, mdes)
    """
    if n1 <= 0 or n2 <= 0:
        log_warning("Invalid sample sizes for power calculation")
        return 0.0, float('inf')
    
    # Pooled sample size for power calculation
    n = (2 * n1 * n2) / (n1 + n2)
    
    # Calculate power using scipy's non-centrality parameter approach
    # For Welch's t-test, we approximate using the pooled variance assumption
    # This is a standard approximation for power analysis in independent samples
    
    from scipy import stats
    
    # Non-centrality parameter
    ncp = effect_size * np.sqrt(n / 2)
    
    # Critical t-value for two-sided test
    df = n1 + n2 - 2  # Approximate degrees of freedom
    if alternative == 'two-sided':
        t_crit = stats.t.ppf(1 - alpha / 2, df)
    elif alternative == 'greater':
        t_crit = stats.t.ppf(1 - alpha, df)
    else:  # 'less'
        t_crit = stats.t.ppf(alpha, df)
    
    # Power calculation
    if alternative == 'two-sided':
        power = (1 - stats.t.cdf(t_crit, df, ncp) + 
                stats.t.cdf(-t_crit, df, ncp))
    elif alternative == 'greater':
        power = 1 - stats.t.cdf(t_crit, df, ncp)
    else:  # 'less'
        power = stats.t.cdf(t_crit, df, ncp)
    
    # Clamp power to [0, 1]
    power = max(0.0, min(1.0, power))
    
    # Calculate MDES (Minimum Detectable Effect Size)
    # MDES is the effect size that would give us 80% power
    target_power = 0.80
    if alternative == 'two-sided':
        t_crit_80 = stats.t.ppf(1 - alpha / 2, df)
        # Solve for effect_size where power = 0.80
        # Using iterative approach for accuracy
        mdes = _find_mdes(target_power, n, alpha, df, alternative)
    else:
        mdes = _find_mdes(target_power, n, alpha, df, alternative)
    
    return power, mdes

def _find_mdes(
    target_power: float,
    n: float,
    alpha: float,
    df: int,
    alternative: str
) -> float:
    """
    Find the Minimum Detectable Effect Size using binary search.
    
    Args:
        target_power: Target power level (typically 0.80)
        n: Effective sample size
        alpha: Significance level
        df: Degrees of freedom
        alternative: Type of test
    
    Returns:
        MDES value
    """
    from scipy import stats
    
    low, high = 0.0, 3.0  # Reasonable range for Cohen's d
    
    # Binary search for MDES
    for _ in range(50):  # Sufficient iterations for convergence
        mid = (low + high) / 2
        ncp = mid * np.sqrt(n / 2)
        
        if alternative == 'two-sided':
            t_crit = stats.t.ppf(1 - alpha / 2, df)
            power = (1 - stats.t.cdf(t_crit, df, ncp) + 
                    stats.t.cdf(-t_crit, df, ncp))
        elif alternative == 'greater':
            t_crit = stats.t.ppf(1 - alpha, df)
            power = 1 - stats.t.cdf(t_crit, df, ncp)
        else:
            t_crit = stats.t.ppf(alpha, df)
            power = stats.t.cdf(t_crit, df, ncp)
        
        if power < target_power:
            low = mid
        else:
            high = mid
        
        if abs(high - low) < 1e-6:
            break
    
    return (low + high) / 2

def run_power_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Run power analysis for both cognitive metrics.
    
    Args:
        df: Cleaned dataset with columns 'stimulus_type', 
            'perseverative_errors', 'categories_completed'
    
    Returns:
        Dictionary with power analysis results
    """
    results = {
        'timestamp': get_timestamp(),
        'analyses': {}
    }
    
    metrics = ['perseverative_errors', 'categories_completed']
    
    for metric in metrics:
        if metric not in df.columns:
            log_warning(f"Metric {metric} not found in dataset, skipping")
            continue
        
        # Group data
        nostalgia_group = df[df['stimulus_type'] == 'nostalgia'][metric].dropna()
        control_group = df[df['stimulus_type'] == 'control'][metric].dropna()
        
        n1 = len(nostalgia_group)
        n2 = len(control_group)
        
        if n1 < 2 or n2 < 2:
            log_warning(f"Insufficient sample size for {metric}: nostalgia={n1}, control={n2}")
            results['analyses'][metric] = {
                'status': 'insufficient_sample_size',
                'nostalgia_n': n1,
                'control_n': n2
            }
            continue
        
        # Calculate effect size (Cohen's d)
        mean1 = nostalgia_group.mean()
        mean2 = control_group.mean()
        std1 = nostalgia_group.std()
        std2 = control_group.std()
        
        # Pooled standard deviation
        pooled_std = np.sqrt(((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2))
        
        if pooled_std == 0:
            log_warning(f"Zero pooled standard deviation for {metric}, skipping power analysis")
            results['analyses'][metric] = {
                'status': 'zero_variance',
                'nostalgia_n': n1,
                'control_n': n2
            }
            continue
        
        effect_size = abs(mean1 - mean2) / pooled_std
        
        # Calculate power and MDES
        power, mdes = calculate_power_and_mdes(
            effect_size=effect_size,
            n1=n1,
            n2=n2,
            alpha=0.05,
            alternative='two-sided'
        )
        
        results['analyses'][metric] = {
            'status': 'success',
            'nostalgia_n': int(n1),
            'control_n': int(n2),
            'effect_size_cohen_d': float(effect_size),
            'statistical_power': float(power),
            'minimum_detectable_effect_size': float(mdes),
            'alpha': 0.05,
            'target_power': 0.80
        }
        
        log_info(f"Power analysis for {metric}: power={power:.4f}, MDES={mdes:.4f}")
    
    return results

def main():
    """Main entry point for T021: Power and MDES analysis."""
    log_info("Starting T021: Statistical Power and MDES Analysis")
    
    # Load cleaned dataset
    df = load_cleaned_dataset()
    if df is None:
        log_warning("No cleaned dataset found. Cannot proceed with power analysis.")
        return
    
    # Load existing statistical report
    report = load_statistical_report()
    
    # Run power analysis
    power_results = run_power_analysis(df)
    
    # Append to report
    report['power_analysis'] = power_results
    
    # Save updated report
    save_statistical_report(report)
    
    log_info("T021 completed successfully")

if __name__ == '__main__':
    main()
