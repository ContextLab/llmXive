"""
Sensitivity Analysis Sweep for Continuous Metrics (T020b).

This script performs a sensitivity analysis sweep for continuous metrics
(episode_length, messages, bandwidth, latency) using paired t-tests across
a range of significance levels and Cohen's d calculation.

Output: results/sensitivity_continuous.csv
Columns: alpha, metric, p_value, cohen_d, significant
"""
import os
import sys
import json
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from experiments.stats_analyzer import load_experiment_data, run_paired_ttest
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Constants for the sensitivity sweep
ALPHA_LEVELS = [0.001, 0.005, 0.01, 0.05, 0.10, 0.15, 0.20]
CONTINUOUS_METRICS = ['episode_length', 'messages', 'bandwidth', 'latency']


def calculate_cohen_d(group1: List[float], group2: List[float]) -> float:
    """
    Calculate Cohen's d effect size for two groups.
    
    Cohen's d = (mean1 - mean2) / pooled_std
    where pooled_std = sqrt(((n1-1)*std1^2 + (n2-1)*std2^2) / (n1+n2-2))
    """
    arr1 = np.array(group1)
    arr2 = np.array(group2)
    
    n1, n2 = len(arr1), len(arr2)
    if n1 < 2 or n2 < 2:
        return 0.0
    
    mean1, mean2 = np.mean(arr1), np.mean(arr2)
    std1, std2 = np.std(arr1, ddof=1), np.std(arr2, ddof=1)
    
    # Pooled standard deviation
    pooled_var = ((n1 - 1) * std1**2 + (n2 - 1) * std2**2) / (n1 + n2 - 2)
    pooled_std = np.sqrt(pooled_var)
    
    if pooled_std == 0:
        return 0.0
        
    return (mean1 - mean2) / pooled_std


def run_sensitivity_sweep(data_dir: Path) -> List[Dict[str, Any]]:
    """
    Run sensitivity analysis sweep for continuous metrics.
    
    For each metric and each alpha level:
    1. Perform paired t-test between Foundation and Native Direct protocols
    2. Calculate Cohen's d effect size
    3. Determine significance based on alpha
    
    Args:
        data_dir: Path to the directory containing experiment results
        
    Returns:
        List of dictionaries with results for each metric/alpha combination
    """
    logger.info(f"Loading experiment data from {data_dir}")
    
    try:
        # Load the experiment data (assumes run_simulation.py has been executed)
        # The data structure is expected to be a JSON file with results per seed
        data_file = data_dir / "simulation_results.json"
        if not data_file.exists():
            logger.error(f"Experiment results not found at {data_file}. Please run run_simulation.py first.")
            return []
        
        with open(data_file, 'r') as f:
            all_results = json.load(f)
        
        # Organize data by protocol and metric
        foundation_data = {metric: [] for metric in CONTINUOUS_METRICS}
        native_data = {metric: [] for metric in CONTINUOUS_METRICS}
        
        for run in all_results:
            protocol = run.get('protocol')
            for metric in CONTINUOUS_METRICS:
                value = run.get(metric)
                if value is not None:
                    if protocol == 'foundation':
                        foundation_data[metric].append(value)
                    elif protocol == 'native_direct':
                        native_data[metric].append(value)
        
        # Check if we have enough data
        for metric in CONTINUOUS_METRICS:
            if len(foundation_data[metric]) == 0 or len(native_data[metric]) == 0:
                logger.warning(f"Not enough data for metric {metric}: foundation={len(foundation_data[metric])}, native={len(native_data[metric])}")
        
        results = []
        
        logger.info(f"Running sensitivity sweep for {len(CONTINUOUS_METRICS)} metrics and {len(ALPHA_LEVELS)} alpha levels")
        
        for metric in CONTINUOUS_METRICS:
            f_vals = foundation_data[metric]
            n_vals = native_data[metric]
            
            if len(f_vals) < 2 or len(n_vals) < 2:
                logger.warning(f"Skipping {metric}: insufficient samples (f={len(f_vals)}, n={len(n_vals)})")
                continue
            
            # Calculate Cohen's d once (it's independent of alpha)
            cohen_d = calculate_cohen_d(f_vals, n_vals)
            
            for alpha in ALPHA_LEVELS:
                # Run paired t-test
                t_stat, p_value, _ = run_paired_ttest(f_vals, n_vals)
                
                # Determine significance
                significant = p_value < alpha
                
                result_entry = {
                    'alpha': alpha,
                    'metric': metric,
                    'p_value': p_value,
                    'cohen_d': cohen_d,
                    'significant': significant
                }
                results.append(result_entry)
                
                logger.debug(f"Metric: {metric}, Alpha: {alpha}, p-value: {p_value:.4f}, "
                           f"Cohen's d: {cohen_d:.4f}, Significant: {significant}")
        
        return results
        
    except Exception as e:
        logger.error(f"Error during sensitivity sweep: {e}", exc_info=True)
        return []


def save_results(results: List[Dict[str, Any]], output_path: Path) -> bool:
    """
    Save sensitivity analysis results to CSV.
    
    Args:
        results: List of result dictionaries
        output_path: Path to the output CSV file
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to DataFrame and save
        df = pd.DataFrame(results)
        
        # Sort by metric and alpha for readability
        df = df.sort_values(by=['metric', 'alpha'])
        
        # Save to CSV
        df.to_csv(output_path, index=False)
        
        logger.info(f"Results saved to {output_path}")
        logger.info(f"Total records: {len(results)}")
        
        return True
        
    except Exception as e:
        logger.error(f"Error saving results: {e}", exc_info=True)
        return False


def check_prerequisites(data_dir: Path) -> bool:
    """
    Check if all prerequisites for running the sensitivity analysis are met.
    
    Args:
        data_dir: Path to the data directory
        
    Returns:
        True if all prerequisites are met, False otherwise
    """
    required_file = data_dir / "simulation_results.json"
    if not required_file.exists():
        logger.error(f"Prerequisite not met: {required_file} does not exist. "
                    "Please run run_simulation.py first.")
        return False
    
    # Check if we have enough seeds
    try:
        with open(required_file, 'r') as f:
            data = json.load(f)
        if len(data) < 10:
            logger.warning(f"Low number of seeds found: {len(data)}. "
                         "Recommend running at least 30 seeds for robust statistics.")
    except Exception as e:
        logger.error(f"Error checking prerequisites: {e}")
        return False
        
    return True


def main():
    """Main entry point for the sensitivity analysis script."""
    parser = argparse.ArgumentParser(
        description='Sensitivity analysis sweep for continuous metrics (T020b)'
    )
    parser.add_argument(
        '--data-dir',
        type=str,
        default='data',
        help='Directory containing experiment results (default: data)'
    )
    parser.add_argument(
        '--output',
        type=str,
        default='results/sensitivity_continuous.csv',
        help='Output CSV file path (default: results/sensitivity_continuous.csv)'
    )
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    output_path = Path(args.output)
    
    logger.info("Starting sensitivity analysis sweep for continuous metrics (T020b)")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"Output file: {output_path}")
    
    # Check prerequisites
    if not check_prerequisites(data_dir):
        logger.error("Prerequisites not met. Aborting.")
        sys.exit(1)
    
    # Run sensitivity sweep
    results = run_sensitivity_sweep(data_dir)
    
    if not results:
        logger.error("No results generated. Aborting.")
        sys.exit(1)
    
    # Save results
    if not save_results(results, output_path):
        logger.error("Failed to save results. Aborting.")
        sys.exit(1)
    
    logger.info("Sensitivity analysis sweep completed successfully.")
    logger.info(f"Output saved to: {output_path.resolve()}")


if __name__ == '__main__':
    main()
