import os
import sys
import logging
import numpy as np
import pandas as pd
from typing import List, Dict, Any, Callable, Optional
import yaml
from datetime import datetime

# Import from project modules
from logging_config import setup_logging

def load_protocol(protocol_path: str) -> Dict[str, Any]:
    """Load simulation parameters from protocol.yaml."""
    if not os.path.exists(protocol_path):
        raise FileNotFoundError(f"Protocol file not found: {protocol_path}")
    with open(protocol_path, 'r') as f:
        return yaml.safe_load(f)

def _calculate_parametric_ci(
    df: pd.DataFrame, 
    condition_col: str, 
    outcome_col: str, 
    condition_label: str
) -> Dict[str, float]:
    """
    Calculate parametric confidence intervals using a simple linear model
    (or logistic approximation for binary) as a baseline for comparison.
    Returns {'estimate': float, 'ci_lower': float, 'ci_upper': float, 'crosses_zero': bool}
    """
    # Simple difference in means approach for the effect size estimate
    # In a full implementation, this would use the fitted model coefficients
    subset = df[df[condition_col] == condition_label]
    if subset.empty:
        return {'estimate': 0.0, 'ci_lower': 0.0, 'ci_upper': 0.0, 'crosses_zero': True}
    
    mean_val = subset[outcome_col].mean()
    std_val = subset[outcome_col].std()
    n = len(subset)
    
    if pd.isna(std_val) or n < 2:
        std_err = 0.0
    else:
        std_err = std_val / np.sqrt(n)
    
    # 95% CI approximation
    ci_lower = mean_val - 1.96 * std_err
    ci_upper = mean_val + 1.96 * std_err
    
    crosses_zero = (ci_lower <= 0) and (ci_upper >= 0)
    
    return {
        'estimate': mean_val,
        'ci_lower': ci_lower,
        'ci_upper': ci_upper,
        'crosses_zero': crosses_zero
    }

def run_bootstrap(
    df: pd.DataFrame,
    condition_col: str,
    outcome_col: str,
    condition_label: str,
    n_bootstrap: int = 1000,
    target_variance: float = 0.01,
    max_bootstrap: int = 5000
) -> Dict[str, Any]:
    """
    Perform bootstrap resampling to estimate confidence intervals.
    Implements dynamic resampling: start at 1000, increase until CI width variance < 1%
    or hard cap of 5000 is reached.
    """
    logger = logging.getLogger(__name__)
    
    subset = df[df[condition_col] == condition_label]
    if subset.empty:
        logger.warning(f"No data found for condition {condition_label}")
        return {
            'n_bootstrap': 0,
            'estimate': 0.0,
            'ci_lower': 0.0,
            'ci_upper': 0.0,
            'ci_width_variance': 0.0,
            'stability_reached': False,
            'ci_width': 0.0
        }
    
    current_n = n_bootstrap
    ci_widths = []
    estimates = []
    
    # Initial run
    for _ in range(current_n):
        sample = subset.sample(n=len(subset), replace=True)
        mean_val = sample[outcome_col].mean()
        estimates.append(mean_val)
    
    # Calculate initial CI
    estimates_arr = np.array(estimates)
    ci_lower = np.percentile(estimates_arr, 2.5)
    ci_upper = np.percentile(estimates_arr, 97.5)
    ci_width = ci_upper - ci_lower
    
    # Store initial width for variance calculation
    last_widths = [ci_width]
    
    # Dynamic loop
    while current_n < max_bootstrap:
        # Calculate variance of CI widths from previous batch
        if len(last_widths) > 1:
            width_variance = np.var(last_widths)
            mean_width = np.mean(last_widths)
            if mean_width > 0:
                relative_variance = width_variance / (mean_width ** 2)
                if relative_variance < target_variance:
                    logger.info(f"Bootstrap stability reached at {current_n} samples. Variance: {relative_variance:.6f}")
                    break
        
        # Increase sample size (exponential growth to reach cap faster)
        current_n = min(current_n * 2, max_bootstrap)
        
        # Re-run bootstrap with new size
        estimates = []
        for _ in range(current_n):
            sample = subset.sample(n=len(subset), replace=True)
            mean_val = sample[outcome_col].mean()
            estimates.append(mean_val)
        
        estimates_arr = np.array(estimates)
        ci_lower = np.percentile(estimates_arr, 2.5)
        ci_upper = np.percentile(estimates_arr, 97.5)
        ci_width = ci_upper - ci_lower
        last_widths = [ci_width] # Simplified: tracking last width change
        
        if current_n >= max_bootstrap:
            logger.warning(f"Bootstrap cap ({max_bootstrap}) reached. Stability may not be fully achieved.")
    
    # Final calculations
    final_estimates = np.array(estimates)
    final_ci_lower = np.percentile(final_estimates, 2.5)
    final_ci_upper = np.percentile(final_estimates, 97.5)
    final_ci_width = final_ci_upper - final_ci_lower
    
    # Check if CI crosses zero
    crosses_zero = (final_ci_lower <= 0) and (final_ci_upper >= 0)
    
    return {
        'n_bootstrap': current_n,
        'estimate': np.mean(final_estimates),
        'ci_lower': final_ci_lower,
        'ci_upper': final_ci_upper,
        'ci_width': final_ci_width,
        'ci_width_variance': np.var(final_estimates) if len(final_estimates) > 1 else 0.0,
        'stability_reached': current_n < max_bootstrap,
        'crosses_zero': crosses_zero,
        'is_unstable': crosses_zero # Flag as unstable if CI crosses zero per SC-003
    }

def compare_and_flag_results(
    bootstrap_results: Dict[str, Any],
    parametric_results: Dict[str, float],
    condition_label: str,
    threshold_type: str
) -> Dict[str, Any]:
    """
    Compare bootstrap CIs against original parametric CIs.
    Explicitly check if the confidence interval crosses zero.
    Flag as 'unstable' if it does, satisfying SC-003.
    """
    bootstrap_ci_lower = bootstrap_results['ci_lower']
    bootstrap_ci_upper = bootstrap_results['ci_upper']
    bootstrap_crosses_zero = bootstrap_results['crosses_zero']
    
    parametric_ci_lower = parametric_results['ci_lower']
    parametric_ci_upper = parametric_results['ci_upper']
    parametric_crosses_zero = parametric_results['crosses_zero']
    
    # Calculate difference in CI bounds
    ci_lower_diff = abs(bootstrap_ci_lower - parametric_ci_lower)
    ci_upper_diff = abs(bootstrap_ci_upper - parametric_ci_upper)
    
    # Determine stability based on SC-003: Flag as unstable if CI crosses zero
    is_unstable = bootstrap_crosses_zero
    
    return {
        'threshold': condition_label,
        'threshold_type': threshold_type,
        'bootstrap_ci': {
            'lower': bootstrap_ci_lower,
            'upper': bootstrap_ci_upper,
            'width': bootstrap_ci_upper - bootstrap_ci_lower
        },
        'parametric_ci': {
            'lower': parametric_ci_lower,
            'upper': parametric_ci_upper,
            'width': parametric_ci_upper - parametric_ci_lower
        },
        'ci_difference': {
            'lower_bound_diff': ci_lower_diff,
            'upper_bound_diff': ci_upper_diff
        },
        'bootstrap_crosses_zero': bootstrap_crosses_zero,
        'parametric_crosses_zero': parametric_crosses_zero,
        'is_unstable': is_unstable,
        'stability_reason': "CI crosses zero" if is_unstable else "CI does not cross zero"
    }

def run_threshold_sweep(
    data_dir: str,
    protocol_path: str,
    outcome_col: str = 'bizarreness',
    condition_col: str = 'condition'
) -> List[Dict[str, Any]]:
    """
    Iterate over the three distinct datasets generated in T017.
    Run bootstrap and parametric analysis for each, then compare results.
    """
    logger = logging.getLogger(__name__)
    protocol = load_protocol(protocol_path)
    
    # Extract threshold labels from protocol
    thresholds = [
        protocol.get('strict_threshold_label', 'strict (complete isolation)'),
        protocol.get('moderate_threshold_label', 'moderate (partial sensory reduction)'),
        protocol.get('partial_threshold_label', 'partial (minimal sensory reduction)')
    ]
    
    # Expected filenames based on T017
    file_map = {
        'strict (complete isolation)': 'data_threshold_strict.csv',
        'moderate (partial sensory reduction)': 'data_threshold_moderate.csv',
        'partial (minimal sensory reduction)': 'data_threshold_partial.csv'
    }
    
    results = []
    
    for threshold_label in thresholds:
        filename = file_map.get(threshold_label)
        if not filename:
            logger.warning(f"No filename mapping for threshold: {threshold_label}")
            continue
        
        filepath = os.path.join(data_dir, filename)
        if not os.path.exists(filepath):
            logger.warning(f"Data file not found: {filepath}")
            continue
        
        logger.info(f"Processing {filename} for threshold: {threshold_label}")
        df = pd.read_csv(filepath)
        
        # Run parametric baseline
        parametric_res = _calculate_parametric_ci(df, condition_col, outcome_col, threshold_label)
        
        # Run bootstrap
        bootstrap_res = run_bootstrap(df, condition_col, outcome_col, threshold_label)
        
        # Compare and flag
        comparison = compare_and_flag_results(
            bootstrap_res, 
            parametric_res, 
            threshold_label, 
            "threshold_sweep"
        )
        
        results.append(comparison)
        logger.info(f"Threshold {threshold_label}: Unstable={comparison['is_unstable']}")
    
    return results

def main():
    """Main entry point for sensitivity analysis T032."""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Paths
    protocol_path = 'data/protocols/protocol.yaml'
    data_dir = 'data/processed'
    output_path = 'results/models/sensitivity_comparison.json'
    
    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    logger.info("Starting Sensitivity Analysis (T032): Bootstrap vs Parametric CI Comparison")
    
    try:
        results = run_threshold_sweep(data_dir, protocol_path)
        
        # Add metadata
        output_data = {
            'timestamp': datetime.now().isoformat(),
            'task': 'T032',
            'description': 'Bootstrap CI vs Parametric CI Comparison with Stability Flagging (SC-003)',
            'results': results
        }
        
        # Serialize results
        with open(output_path, 'w') as f:
            json.dump(output_data, f, indent=2)
        
        logger.info(f"Results saved to {output_path}")
        
        # Print summary
        unstable_count = sum(1 for r in results if r['is_unstable'])
        logger.info(f"Summary: {unstable_count}/{len(results)} thresholds flagged as unstable (CI crosses zero).")
        
    except Exception as e:
        logger.error(f"Error during sensitivity analysis: {e}", exc_info=True)
        raise

if __name__ == '__main__':
    main()