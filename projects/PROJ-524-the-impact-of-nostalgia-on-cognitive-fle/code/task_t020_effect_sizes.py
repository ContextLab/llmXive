"""
Task T020: Calculate and report Cohen's d with 95% confidence intervals.

This module calculates Cohen's d effect sizes and their 95% confidence intervals
for the primary comparisons (nostalgia vs control) on:
1. Perseverative Errors
2. Categories Completed

It reads the cleaned dataset produced by T014a and writes the results to
data/results/effect_sizes.json.
"""
import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Tuple, List

# Import from existing project API
from config import get_config, ensure_dirs, get_env_str
from utils import setup_logging, log_info, log_warning, log_error, get_timestamp
from analysis import calculate_cohen_d, calculate_effect_size_ci

# Constants
PRIMARY_METRICS = ['perseverative_errors', 'categories_completed']
OUTPUT_FILE = 'data/results/effect_sizes.json'


def load_cleaned_dataset() -> pd.DataFrame:
    """Load the cleaned dataset from data/processed/cleaned_dataset.csv."""
    config = get_config()
    input_path = Path(config['paths']['processed_data']) / 'cleaned_dataset.csv'
    
    if not input_path.exists():
        raise FileNotFoundError(
            f"Cleaned dataset not found at {input_path}. "
            "Ensure T014a has been completed."
        )
    
    df = pd.read_csv(input_path)
    log_info(f"Loaded {len(df)} records from {input_path}")
    return df


def calculate_effect_sizes(df: pd.DataFrame, metric: str) -> Dict[str, Any]:
    """
    Calculate Cohen's d and 95% CI for a specific metric between nostalgia and control groups.
    
    Args:
        df: Cleaned dataset with 'stimulus_type' and metric columns
        metric: Name of the cognitive metric column
        
    Returns:
        Dictionary with effect size results
    """
    # Group data
    nostalgia_group = df[df['stimulus_type'] == 'nostalgia'][metric].dropna()
    control_group = df[df['stimulus_type'] == 'control'][metric].dropna()
    
    if len(nostalgia_group) == 0 or len(control_group) == 0:
        log_warning(f"Empty group for metric {metric}: Nostalgia={len(nostalgia_group)}, Control={len(control_group)}")
        return {
            'metric': metric,
            'nostalgia_n': len(nostalgia_group),
            'control_n': len(control_group),
            'cohen_d': None,
            'ci_lower': None,
            'ci_upper': None,
            'ci_confidence_level': 0.95,
            'status': 'insufficient_data'
        }
    
    # Calculate means and standard deviations
    mean_nostalgia = nostalgia_group.mean()
    mean_control = control_group.mean()
    std_nostalgia = nostalgia_group.std(ddof=1)
    std_control = control_group.std(ddof=1)
    
    # Calculate pooled standard deviation
    n1, n2 = len(nostalgia_group), len(control_group)
    if n1 + n2 <= 2:
        log_error(f"Sample size too small for {metric}: {n1 + n2}")
        return {
            'metric': metric,
            'nostalgia_n': n1,
            'control_n': n2,
            'cohen_d': None,
            'ci_lower': None,
            'ci_upper': None,
            'ci_confidence_level': 0.95,
            'status': 'sample_size_too_small'
        }
    
    pooled_std = np.sqrt(((n1 - 1) * std_nostalgia**2 + (n2 - 1) * std_control**2) / (n1 + n2 - 2))
    
    if pooled_std == 0:
        log_warning(f"Zero pooled standard deviation for {metric}")
        return {
            'metric': metric,
            'nostalgia_n': n1,
            'control_n': n2,
            'nostalgia_mean': float(mean_nostalgia),
            'control_mean': float(mean_control),
            'cohen_d': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'ci_confidence_level': 0.95,
            'status': 'zero_variance'
        }
    
    # Calculate Cohen's d
    cohen_d = (mean_nostalgia - mean_control) / pooled_std
    
    # Calculate 95% CI using the non-central t-distribution approximation
    # Using the formula from Hedges & Olkin (1985)
    ci_lower, ci_upper = calculate_effect_size_ci(cohen_d, n1, n2, confidence_level=0.95)
    
    status = 'success'
    log_info(f"Cohen's d for {metric}: {cohen_d:.4f} (95% CI [{ci_lower:.4f}, {ci_upper:.4f}])")
    
    return {
        'metric': metric,
        'nostalgia_n': int(n1),
        'control_n': int(n2),
        'nostalgia_mean': float(mean_nostalgia),
        'control_mean': float(mean_control),
        'nostalgia_std': float(std_nostalgia),
        'control_std': float(std_control),
        'pooled_std': float(pooled_std),
        'cohen_d': float(cohen_d),
        'ci_lower': float(ci_lower),
        'ci_upper': float(ci_upper),
        'ci_confidence_level': 0.95,
        'status': status
    }


def run_effect_size_analysis(df: pd.DataFrame) -> List[Dict[str, Any]]:
    """Run effect size analysis for all primary metrics."""
    results = []
    
    for metric in PRIMARY_METRICS:
        if metric not in df.columns:
            log_error(f"Metric {metric} not found in dataset")
            results.append({
                'metric': metric,
                'status': 'missing_column',
                'error': f"Column '{metric}' not found in dataset"
            })
            continue
        
        result = calculate_effect_sizes(df, metric)
        results.append(result)
    
    return results


def save_results(results: List[Dict[str, Any]], output_path: Path) -> None:
    """Save effect size results to JSON file."""
    output_dir = output_path.parent
    ensure_dirs([output_dir])
    
    report = {
        'timestamp': get_timestamp(),
        'task_id': 'T020',
        'description': 'Cohen\'s d effect sizes with 95% confidence intervals',
        'metrics_analyzed': PRIMARY_METRICS,
        'results': results,
        'summary': {
            'total_metrics': len(PRIMARY_METRICS),
            'successful_calculations': sum(1 for r in results if r.get('status') == 'success'),
            'failed_calculations': sum(1 for r in results if r.get('status') not in ['success', 'insufficient_data'])
        }
    }
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, indent=2)
    
    log_info(f"Effect size results saved to {output_path}")


def main():
    """Main entry point for T020."""
    # Setup logging
    log_level = logging.INFO
    setup_logging(level=log_level)
    
    log_info("=" * 60)
    log_info("Task T020: Calculate Effect Sizes (Cohen's d with 95% CI)")
    log_info("=" * 60)
    
    try:
        # Load cleaned dataset
        df = load_cleaned_dataset()
        
        # Verify required columns
        required_cols = ['stimulus_type'] + PRIMARY_METRICS
        missing_cols = [col for col in required_cols if col not in df.columns]
        if missing_cols:
            raise ValueError(f"Missing required columns: {missing_cols}")
        
        # Run analysis
        log_info("Calculating effect sizes for primary metrics...")
        results = run_effect_size_analysis(df)
        
        # Save results
        output_path = Path(get_config()['paths']['results_data']) / 'effect_sizes.json'
        save_results(results, output_path)
        
        # Log summary
        success_count = sum(1 for r in results if r.get('status') == 'success')
        log_info(f"Analysis complete: {success_count}/{len(PRIMARY_METRICS)} metrics calculated successfully")
        
        # Print summary to console
        print("\n" + "=" * 60)
        print("EFFECT SIZE SUMMARY (Cohen's d)")
        print("=" * 60)
        for r in results:
            if r.get('status') == 'success':
                print(f"\n{r['metric'].replace('_', ' ').title()}:")
                print(f"  Nostalgia (n={r['nostalgia_n']}): M={r['nostalgia_mean']:.2f}, SD={r['nostalgia_std']:.2f}")
                print(f"  Control   (n={r['control_n']}): M={r['control_mean']:.2f}, SD={r['control_std']:.2f}")
                print(f"  Cohen's d = {r['cohen_d']:.4f} [95% CI: {r['ci_lower']:.4f}, {r['ci_upper']:.4f}]")
            else:
                print(f"\n{r['metric'].replace('_', ' ').title()}: FAILED - {r.get('status', 'unknown error')}")
        print("=" * 60)
        
        log_info("Task T020 completed successfully")
        return 0
        
    except Exception as e:
        log_error(f"Task T020 failed: {str(e)}")
        log_error(f"Error type: {type(e).__name__}")
        import traceback
        log_error(traceback.format_exc())
        return 1


if __name__ == '__main__':
    exit(main())
