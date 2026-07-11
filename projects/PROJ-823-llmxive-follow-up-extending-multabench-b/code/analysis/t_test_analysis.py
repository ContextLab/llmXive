"""
Statistical analysis module for User Story 3.
Performs one-sample t-tests (or Wilcoxon signed-rank tests) comparing
CPU-Conditioned performance against fixed GPU-Tuned baselines.
"""
import os
import sys
import json
import csv
import argparse
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
from scipy import stats

# Local imports
from utils.logging import get_logger, log_info, log_error, log_warning
from config import ensure_directories

logger = get_logger(__name__)

# Constants
NORMALITY_THRESHOLD = 0.05  # Shapiro-Wilk p-value threshold for normality
MIN_SAMPLES = 2  # Minimum samples required for t-test


def load_conditioned_metrics(metrics_path: Path) -> Dict[str, Dict[str, float]]:
    """
    Load conditioned metrics from the aggregated JSON file.
    
    Args:
        metrics_path: Path to the conditioned metrics JSON file
        
    Returns:
        Dictionary mapping dataset_id to metrics
    """
    if not metrics_path.exists():
        raise FileNotFoundError(f"Conditioned metrics file not found: {metrics_path}")
        
    with open(metrics_path, 'r') as f:
        data = json.load(f)
        
    # Handle different possible structures
    if isinstance(data, list):
        return {item['dataset_id']: item for item in data}
    elif isinstance(data, dict):
        if 'metrics' in data:
            return {item['dataset_id']: item for item in data['metrics']}
        return data
    else:
        raise ValueError(f"Unexpected metrics file format: {type(data)}")


def load_gpu_baselines(baselines_path: Path) -> Dict[str, Dict[str, float]]:
    """
    Load GPU-Tuned baselines from the validated CSV file.
    
    Args:
        baselines_path: Path to the GPU-Tuned baselines CSV file
        
    Returns:
        Dictionary mapping dataset_id to baseline values
    """
    if not baselines_path.exists():
        raise FileNotFoundError(f"GPU-Tuned baselines file not found: {baselines_path}")
        
    baselines = {}
    with open(baselines_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            dataset_id = row['dataset_id']
            # Assume 'baseline_value' contains the performance metric
            # We need to handle different metric types (AUC, RMSE, etc.)
            # For now, we'll use a generic 'value' field
            baseline_value = float(row['baseline_value'])
            baselines[dataset_id] = {
                'dataset_id': dataset_id,
                'baseline_value': baseline_value,
                'task_type': row.get('task_type', 'unknown')
            }
            
    return baselines


def check_normality(data: np.ndarray) -> Tuple[bool, float]:
    """
    Check if data follows a normal distribution using Shapiro-Wilk test.
    
    Args:
        data: Array of data points
        
    Returns:
        Tuple of (is_normal, p_value)
    """
    if len(data) < MIN_SAMPLES:
        return False, 0.0
        
    try:
        _, p_value = stats.shapiro(data)
        return p_value >= NORMALITY_THRESHOLD, p_value
    except Exception as e:
        logger.warning(f"Normality test failed: {e}")
        return False, 0.0


def perform_statistical_test(
    conditioned_values: List[float],
    baseline_value: float,
    dataset_id: str
) -> Dict[str, Any]:
    """
    Perform appropriate statistical test based on data normality.
    
    Args:
        conditioned_values: List of conditioned performance values
        baseline_value: Fixed GPU-Tuned baseline value
        dataset_id: Identifier for the dataset
        
    Returns:
        Dictionary with test results
    """
    if len(conditioned_values) < MIN_SAMPLES:
        return {
            'dataset_id': dataset_id,
            'test_type': 'insufficient_data',
            't_statistic': None,
            'p_value': None,
            'is_significant': None,
            'error': f'Insufficient data points: {len(conditioned_values)}'
        }
    
    # Convert to numpy array
    conditioned_array = np.array(conditioned_values)
    
    # Check normality
    is_normal, normality_p = check_normality(conditioned_array)
    
    if is_normal and len(conditioned_array) >= MIN_SAMPLES:
        # Perform one-sample t-test
        test_statistic, p_value = stats.ttest_1samp(
            conditioned_array, baseline_value
        )
        test_type = 't-test'
    else:
        # Perform Wilcoxon signed-rank test
        # Note: Wilcoxon requires at least 2 non-equal values
        if len(np.unique(conditioned_array)) < 2:
            return {
                'dataset_id': dataset_id,
                'test_type': 'wilcoxon_failed',
                't_statistic': None,
                'p_value': None,
                'is_significant': None,
                'error': 'All values identical, cannot perform Wilcoxon test'
            }
            
        test_statistic, p_value = stats.wilcoxon(
            conditioned_array, [baseline_value] * len(conditioned_array)
        )
        test_type = 'wilcoxon'
    
    # Determine significance (two-tailed test, alpha=0.05)
    is_significant = p_value < 0.05 if p_value is not None else None
    
    return {
        'dataset_id': dataset_id,
        'test_type': test_type,
        't_statistic': float(test_statistic) if test_statistic is not None else None,
        'p_value': float(p_value) if p_value is not None else None,
        'normality_p_value': float(normality_p),
        'is_normal': is_normal,
        'is_significant': is_significant,
        'mean_conditioned': float(np.mean(conditioned_array)),
        'std_conditioned': float(np.std(conditioned_array)),
        'baseline_value': float(baseline_value),
        'n_samples': len(conditioned_array)
    }


def aggregate_conditioned_metrics(
    conditioned_data: Dict[str, Dict[str, Any]],
    baseline_value: float
) -> List[float]:
    """
    Aggregate conditioned metrics for a single dataset.
    
    Args:
        conditioned_data: Conditioned metrics for a dataset
        baseline_value: Baseline value to compare against
        
    Returns:
        List of conditioned values for statistical testing
    """
    # Extract the relevant metric value
    # This assumes the metrics have been aggregated and contain a 'performance' field
    if 'performance' in conditioned_data:
        return [conditioned_data['performance']]
    
    # If we have multiple runs (e.g., from sensitivity analysis), extract all
    if 'metrics' in conditioned_data and isinstance(conditioned_data['metrics'], list):
        return [m['performance'] for m in conditioned_data['metrics'] if 'performance' in m]
    
    # Fallback: try to find any numeric field that looks like a performance metric
    numeric_fields = []
    for key, value in conditioned_data.items():
        if isinstance(value, (int, float)) and key not in ['dataset_id', 'run_id']:
            numeric_fields.append(value)
    
    return numeric_fields if numeric_fields else []


def run_t_test_analysis(
    conditioned_metrics_path: Path,
    gpu_baselines_path: Path,
    output_path: Path
) -> Dict[str, Any]:
    """
    Main function to run t-test analysis across all valid datasets.
    
    Args:
        conditioned_metrics_path: Path to conditioned metrics file
        gpu_baselines_path: Path to GPU-Tuned baselines file
        output_path: Path for output results
        
    Returns:
        Dictionary containing all test results
    """
    ensure_directories()
    
    # Load data
    logger.info(f"Loading conditioned metrics from {conditioned_metrics_path}")
    conditioned_data = load_conditioned_metrics(conditioned_metrics_path)
    
    logger.info(f"Loading GPU-Tuned baselines from {gpu_baselines_path}")
    gpu_baselines = load_gpu_baselines(gpu_baselines_path)
    
    # Find common datasets
    common_datasets = set(conditioned_data.keys()) & set(gpu_baselines.keys())
    logger.info(f"Found {len(common_datasets)} datasets with both conditioned metrics and baselines")
    
    if not common_datasets:
        logger.warning("No common datasets found between conditioned metrics and baselines")
        return {
            'results': [],
            'summary': {
                'total_datasets': 0,
                'valid_datasets': 0,
                'significant_results': 0,
                'non_significant_results': 0
            }
        }
    
    # Perform tests
    results = []
    significant_count = 0
    non_significant_count = 0
    error_count = 0
    
    for dataset_id in sorted(common_datasets):
        try:
            # Get conditioned values
            conditioned_values = aggregate_conditioned_metrics(
                conditioned_data[dataset_id],
                gpu_baselines[dataset_id]['baseline_value']
            )
            
            if not conditioned_values:
                logger.warning(f"No conditioned values found for {dataset_id}")
                continue
            
            # Perform statistical test
            test_result = perform_statistical_test(
                conditioned_values,
                gpu_baselines[dataset_id]['baseline_value'],
                dataset_id
            )
            
            results.append(test_result)
            
            if test_result.get('is_significant') is True:
                significant_count += 1
            elif test_result.get('is_significant') is False:
                non_significant_count += 1
            elif test_result.get('error'):
                error_count += 1
                
        except Exception as e:
            logger.error(f"Error processing dataset {dataset_id}: {e}")
            error_count += 1
            continue
    
    # Save results
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump({
            'results': results,
            'summary': {
                'total_datasets': len(common_datasets),
                'valid_datasets': len(results),
                'significant_results': significant_count,
                'non_significant_results': non_significant_count,
                'error_count': error_count
            }
        }, f, indent=2)
    
    logger.info(f"Saved t-test results to {output_path}")
    
    return {
        'results': results,
        'summary': {
            'total_datasets': len(common_datasets),
            'valid_datasets': len(results),
            'significant_results': significant_count,
            'non_significant_results': non_significant_count,
            'error_count': error_count
        }
    }


def main():
    """Main entry point for the t-test analysis pipeline."""
    parser = argparse.ArgumentParser(description='Perform t-test analysis on conditioned vs GPU-Tuned performance')
    parser.add_argument('--conditioned-metrics', type=str, required=True,
                      help='Path to conditioned metrics JSON file')
    parser.add_argument('--gpu-baselines', type=str, required=True,
                      help='Path to GPU-Tuned baselines CSV file')
    parser.add_argument('--output', type=str, required=True,
                      help='Path for output JSON file')
    
    args = parser.parse_args()
    
    conditioned_path = Path(args.conditioned_metrics)
    baselines_path = Path(args.gpu_baselines)
    output_path = Path(args.output)
    
    try:
        result = run_t_test_analysis(conditioned_path, baselines_path, output_path)
        print(json.dumps(result['summary'], indent=2))
        return 0
    except Exception as e:
        log_error(f"Analysis failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
