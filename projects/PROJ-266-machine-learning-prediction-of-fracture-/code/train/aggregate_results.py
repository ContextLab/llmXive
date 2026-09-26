"""
Aggregate results from multiple training runs (different seeds) into a single metrics file.
This script collects MAE and R2 distributions from independent seed runs and prepares
the data for statistical testing (Wilcoxon signed-rank test).
"""
import os
import json
import argparse
import logging
from pathlib import Path
from typing import Dict, Any, List

from code.utils.logger import get_logger
from code.train.stats import wilcoxon_test

logger = get_logger("aggregate")

def load_run_metrics(run_dir: str) -> Dict[str, Any]:
    """Load metrics from a single run directory."""
    metrics_path = os.path.join(run_dir, "metrics.json")
    if not os.path.exists(metrics_path):
        raise FileNotFoundError(f"Metrics file not found in {run_dir}")
    
    with open(metrics_path, 'r') as f:
        return json.load(f)

def aggregate_results(
    runs_dir: str,
    output_path: str,
    num_seeds: int = 5
) -> Dict[str, Any]:
    """
    Aggregate metrics from multiple runs.
    
    Args:
        runs_dir: Directory containing subdirectories for each seed run.
        output_path: Path to save aggregated results.
        num_seeds: Number of seed runs to aggregate.
        
    Returns:
        Aggregated results dictionary.
    """
    aggregated = {
        'n_runs': num_seeds,
        'mae_distribution': {
            'cnn': [],
            'linear': [],
            'random_forest': []
        },
        'r2_distribution': {
            'cnn': [],
            'linear': [],
            'random_forest': []
        },
        'wilcoxon_p_value': None,
        'wilcoxon_statistic': None,
        'wilcoxon_significant': False
    }
    
    # Collect metrics from each run
    for i in range(num_seeds):
        run_dir = os.path.join(runs_dir, f"seed_{i}")
        if not os.path.exists(run_dir):
            logger.warning(f"Run directory {run_dir} not found, skipping.")
            continue
        
        try:
            run_metrics = load_run_metrics(run_dir)
            
            # Extract MAE and R2 for each model
            if 'models' in run_metrics:
                if 'cnn' in run_metrics['models'] and 'mae' in run_metrics['models']['cnn']:
                    aggregated['mae_distribution']['cnn'].append(run_metrics['models']['cnn']['mae'])
                    aggregated['r2_distribution']['cnn'].append(run_metrics['models']['cnn']['r2'])
                
                if 'linear' in run_metrics['models'] and 'mae' in run_metrics['models']['linear']:
                    aggregated['mae_distribution']['linear'].append(run_metrics['models']['linear']['mae'])
                    aggregated['r2_distribution']['linear'].append(run_metrics['models']['linear']['r2'])
                
                if 'random_forest' in run_metrics['models'] and 'mae' in run_metrics['models']['random_forest']:
                    aggregated['mae_distribution']['random_forest'].append(run_metrics['models']['random_forest']['mae'])
                    aggregated['r2_distribution']['random_forest'].append(run_metrics['models']['random_forest']['r2'])
        except Exception as e:
            logger.error(f"Error loading metrics from {run_dir}: {e}")
    
    # Perform Wilcoxon test if we have enough data (at least 2 samples per group)
    if len(aggregated['mae_distribution']['cnn']) >= 2 and len(aggregated['mae_distribution']['linear']) >= 2:
        logger.info("Performing Wilcoxon test between CNN and Linear Regression...")
        try:
            wilcoxon_result = wilcoxon_test(
                aggregated['mae_distribution']['cnn'],
                aggregated['mae_distribution']['linear']
            )
            aggregated['wilcoxon_p_value'] = wilcoxon_result['p_value']
            aggregated['wilcoxon_statistic'] = wilcoxon_result['statistic']
            aggregated['wilcoxon_significant'] = wilcoxon_result['significant']
        except Exception as e:
            logger.error(f"Wilcoxon test failed: {e}")
    
    # Save aggregated results
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(aggregated, f, indent=2)
    
    logger.info(f"Aggregated results saved to {output_path}")
    logger.info(f"CNN MAE distribution: {aggregated['mae_distribution']['cnn']}")
    logger.info(f"Linear MAE distribution: {aggregated['mae_distribution']['linear']}")
    logger.info(f"Random Forest MAE distribution: {aggregated['mae_distribution']['random_forest']}")
    
    return aggregated

def main():
    """Main entry point for aggregation."""
    parser = argparse.ArgumentParser(description="Aggregate results from multiple runs")
    parser.add_argument('--runs-dir', type=str, default='models/runs',
                        help='Directory containing run subdirectories')
    parser.add_argument('--output', type=str, default='results/metrics.json',
                        help='Path to output aggregated metrics file')
    parser.add_argument('--num-seeds', type=int, default=5,
                        help='Number of seed runs to aggregate')
    
    args = parser.parse_args()
    
    aggregate_results(
        runs_dir=args.runs_dir,
        output_path=args.output,
        num_seeds=args.num_seeds
    )

if __name__ == '__main__':
    main()
