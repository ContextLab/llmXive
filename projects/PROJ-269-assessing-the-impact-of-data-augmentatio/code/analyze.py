import os
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import List, Dict, Optional, Tuple, Any
from scipy import stats

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants
SIGNIFICANCE_THRESHOLD = 0.05
BOOTSTRAP_ITERATIONS = 1000
CONFIDENCE_LEVEL = 0.95
DISCLAIMER_TEXT = "DISCLAIMER: Findings are associational and do not imply causation. Results are specific to the datasets and configurations tested."

def load_simulation_results(filepath: Path) -> Dict[str, Any]:
    """Load simulation results from a JSON file."""
    if not filepath.exists():
        raise FileNotFoundError(f"Results file not found: {filepath}")
    
    with open(filepath, 'r') as f:
        return json.load(f)

def calculate_error_rates(p_values: List[float]) -> Dict[str, float]:
    """
    Calculate Type I and Type II error rates based on p-values.
    
    Type I Error (False Positive): Rejecting null when it is true.
    Type II Error (False Negative): Failing to reject null when alternative is true.
    
    In this context, we calculate the proportion of p-values < 0.05.
    For Type I (Null condition): This is the false positive rate.
    For Type II (Alt condition): 1 - (1 - false negative rate) = power, but we return the error rate directly.
    
    Args:
        p_values: List of p-values from hypothesis tests.
        
    Returns:
        Dictionary with 'error_rate' and 'total_tests'.
    """
    if not p_values:
        return {'error_rate': 0.0, 'total_tests': 0}
    
    p_array = np.array(p_values)
    rejections = np.sum(p_array < SIGNIFICANCE_THRESHOLD)
    total = len(p_array)
    
    error_rate = rejections / total if total > 0 else 0.0
    
    return {
        'error_rate': float(error_rate),
        'total_tests': int(total),
        'rejections': int(rejections)
    }

def calculate_bootstrap_ci(
    p_values: List[float], 
    n_iterations: int = BOOTSTRAP_ITERATIONS, 
    confidence_level: float = CONFIDENCE_LEVEL
) -> Dict[str, float]:
    """
    Calculate bootstrap confidence intervals for the error rate.
    
    Args:
        p_values: List of p-values from hypothesis tests.
        n_iterations: Number of bootstrap iterations.
        confidence_level: Confidence level for the interval (default 0.95).
        
    Returns:
        Dictionary with 'lower_bound', 'upper_bound', and 'point_estimate'.
    """
    if not p_values:
        return {
            'lower_bound': 0.0,
            'upper_bound': 0.0,
            'point_estimate': 0.0
        }
    
    p_array = np.array(p_values)
    total = len(p_array)
    
    # Calculate the proportion of rejections for the original sample
    original_rejections = np.sum(p_array < SIGNIFICANCE_THRESHOLD)
    original_error_rate = original_rejections / total
    
    # Bootstrap resampling
    bootstrap_rates = []
    for _ in range(n_iterations):
        # Resample with replacement
        resampled_indices = np.random.choice(total, size=total, replace=True)
        resampled_p = p_array[resampled_indices]
        
        # Calculate error rate for resample
        resampled_rejections = np.sum(resampled_p < SIGNIFICANCE_THRESHOLD)
        resampled_rate = resampled_rejections / total
        bootstrap_rates.append(resampled_rate)
    
    bootstrap_rates = np.array(bootstrap_rates)
    
    # Calculate confidence interval
    alpha = 1 - confidence_level
    lower_idx = int((alpha / 2) * n_iterations)
    upper_idx = int((1 - alpha / 2) * n_iterations)
    
    lower_bound = np.percentile(bootstrap_rates, (alpha / 2) * 100)
    upper_bound = np.percentile(bootstrap_rates, (1 - alpha / 2) * 100)
    
    return {
        'lower_bound': float(lower_bound),
        'upper_bound': float(upper_bound),
        'point_estimate': float(original_error_rate)
    }

def ks_test_wrapper(p_values_baseline: List[float], p_values_augmented: List[float]) -> Dict[str, float]:
    """
    Perform Kolmogorov-Smirnov test on two sets of p-values.
    
    Args:
        p_values_baseline: P-values from baseline simulation.
        p_values_augmented: P-values from augmented simulation.
        
    Returns:
        Dictionary with 'ks_statistic' and 'p_value'.
    """
    if not p_values_baseline or not p_values_augmented:
        logger.warning("Empty p-value list provided to KS test. Returning NaN.")
        return {'ks_statistic': float('nan'), 'p_value': float('nan')}
    
    stat, p_val = stats.ks_2samp(p_values_baseline, p_values_augmented)
    
    return {
        'ks_statistic': float(stat),
        'p_value': float(p_val)
    }

def analyze_baseline_results(
    results: Dict[str, Any], 
    condition_type: str
) -> Dict[str, Any]:
    """
    Analyze a single set of baseline results (either Type I or Type II).
    
    Args:
        results: Dictionary containing simulation results with 'p_values'.
        condition_type: 'type_i' or 'type_ii' to label the analysis.
        
    Returns:
        Dictionary containing error rates and confidence intervals.
    """
    p_values = results.get('p_values', [])
    
    if not p_values:
        logger.warning(f"No p-values found for {condition_type} condition.")
        return {
            'condition': condition_type,
            'error_rate': 0.0,
            'total_tests': 0,
            'rejections': 0,
            'confidence_interval': {'lower_bound': 0.0, 'upper_bound': 0.0, 'point_estimate': 0.0}
        }
    
    error_metrics = calculate_error_rates(p_values)
    ci_metrics = calculate_bootstrap_ci(p_values)
    
    return {
        'condition': condition_type,
        'error_rate': error_metrics['error_rate'],
        'total_tests': error_metrics['total_tests'],
        'rejections': error_metrics['rejections'],
        'confidence_interval': {
            'lower_bound': ci_metrics['lower_bound'],
            'upper_bound': ci_metrics['upper_bound'],
            'point_estimate': ci_metrics['point_estimate']
        },
        'p_values_sample': p_values[:5] if len(p_values) > 5 else p_values  # For inspection
    }

def generate_report(
    baseline_type_i: Dict[str, Any],
    baseline_type_ii: Dict[str, Any],
    dataset_name: str,
    sample_size: int
) -> Dict[str, Any]:
    """
    Generate a comprehensive report for baseline results.
    
    Args:
        baseline_type_i: Analysis results for Type I error condition.
        baseline_type_ii: Analysis results for Type II error condition.
        dataset_name: Name of the dataset used.
        sample_size: Sample size used in the simulation.
        
    Returns:
        Dictionary containing the full report structure.
    """
    report = {
        'metadata': {
            'dataset': dataset_name,
            'sample_size': sample_size,
            'analysis_type': 'baseline',
            'significance_threshold': SIGNIFICANCE_THRESHOLD,
            'bootstrap_iterations': BOOTSTRAP_ITERATIONS,
            'disclaimer': DISCLAIMER_TEXT
        },
        'results': {
            'type_i_error': baseline_type_i,
            'type_ii_error': baseline_type_ii
        }
    }
    
    # Calculate power for Type II
    type_ii_error_rate = baseline_type_ii.get('error_rate', 0.0)
    power = 1.0 - type_ii_error_rate
    report['results']['power'] = {
        'value': power,
        'description': 'Statistical power (1 - Type II error rate)'
    }
    
    return report

def main():
    """
    Main entry point for analyzing baseline simulation results.
    This function is designed to be called by an orchestration script or directly.
    It processes all baseline result files in the results directory.
    """
    base_dir = Path.cwd()
    results_dir = base_dir / 'results'
    
    if not results_dir.exists():
        logger.error(f"Results directory not found: {results_dir}")
        return
    
    # Find baseline result files
    # Expected naming: [dataset]_[size]_baseline_null.json and [dataset]_[size]_baseline_alt.json
    baseline_files = list(results_dir.glob("*_baseline_*.json"))
    
    if not baseline_files:
        logger.warning("No baseline result files found in results directory.")
        return
    
    logger.info(f"Found {len(baseline_files)} baseline result files.")
    
    analysis_results = []
    
    for file_path in baseline_files:
        try:
            logger.info(f"Processing: {file_path.name}")
            data = load_simulation_results(file_path)
            
            # Determine condition type from filename
            if 'null' in file_path.name:
                condition_type = 'type_i'
            elif 'alt' in file_path.name:
                condition_type = 'type_ii'
            else:
                logger.warning(f"Could not determine condition type for {file_path.name}. Skipping.")
                continue
            
            analysis = analyze_baseline_results(data, condition_type)
            analysis['source_file'] = file_path.name
            analysis_results.append(analysis)
            
            # Generate and save report
            # Extract dataset and size from filename
            parts = file_path.stem.split('_')
            if len(parts) >= 3:
                dataset_name = '_'.join(parts[:-2])
                sample_size = int(parts[-2])
            else:
                dataset_name = 'unknown'
                sample_size = 0
                
            report = generate_report(
                baseline_type_i=analysis if condition_type == 'type_i' else {},
                baseline_type_ii=analysis if condition_type == 'type_ii' else {},
                dataset_name=dataset_name,
                sample_size=sample_size
            )
            
            # Save report to a new file
            report_path = file_path.parent / f"{file_path.stem}_analysis.json"
            with open(report_path, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"Saved analysis report to: {report_path}")
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}", exc_info=True)
            continue
    
    logger.info(f"Analysis complete. Processed {len(analysis_results)} files.")

if __name__ == "__main__":
    main()