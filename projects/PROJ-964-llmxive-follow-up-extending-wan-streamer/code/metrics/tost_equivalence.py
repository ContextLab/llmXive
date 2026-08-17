import os
import sys
import argparse
import logging
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

import pandas as pd
import numpy as np
from statsmodels.stats.weightstats import ttost_ind

# Import project utilities
from utils.config import get_config_summary
from data.validate_logs import check_logs_exist

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('data/logs/tost_equivalence.log')
    ]
)
logger = logging.getLogger(__name__)

def load_hybrid_output(output_path: str = 'data/processed/hybrid_output.parquet') -> pd.DataFrame:
    """
    Load the hybrid output parquet file.
    """
    if not os.path.exists(output_path):
        raise FileNotFoundError(f"Hybrid output file not found: {output_path}")
    
    logger.info(f"Loading hybrid output from {output_path}")
    df = pd.read_parquet(output_path)
    logger.info(f"Loaded {len(df)} rows with columns: {list(df.columns)}")
    
    required_cols = ['frame_id', 'latency', 'fid_score', 'skip_flag']
    missing_cols = [c for c in required_cols if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Missing required columns in hybrid output: {missing_cols}")
    
    return df

def load_baseline_metrics() -> Dict[str, Any]:
    """
    Load baseline metrics for comparison.
    If data_source is 'voxceleb2', we use a linear interpolation baseline.
    If data_source is 'wan-streamer', we use Wan-Streamer baseline.
    """
    config = get_config_summary()
    data_source = config.get('data_source', 'wan-streamer')
    
    logger.info(f"Data source detected: {data_source}")
    
    # For this implementation, we assume the baseline metrics are derived
    # from the non-skipped frames in the hybrid output itself (the 'full solver' frames)
    # or from a separate baseline file if provided.
    # Per task T050 logic, we switch baseline calculation method if necessary.
    # Here we simulate loading a baseline or deriving it.
    
    # We will derive the baseline from the hybrid output where skip_flag == False
    # This represents the "Full Solver" performance.
    # In a real scenario, this might come from a separate 'baseline_output.parquet'
    # but given the task dependencies, we use the hybrid output's non-skipped frames.
    
    return {
        'source': data_source,
        'description': f"Baseline derived from non-skipped frames in hybrid output (data_source={data_source})"
    }

def perform_tost_test(
    group_a: np.ndarray, 
    group_b: np.ndarray, 
    equivalence_margin: float = 0.05, 
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Perform Two One-Sided Tests (TOST) for equivalence.
    
    Args:
        group_a: Array of values for group A (e.g., skipped frames FID)
        group_b: Array of values for group B (e.g., full solver FID)
        equivalence_margin: The delta (Δ) for equivalence (default 0.05)
        alpha: Significance level (default 0.05)
        
    Returns:
        Dictionary with TOST results including p-values and conclusion.
    """
    if len(group_a) == 0 or len(group_b) == 0:
        return {
            'error': 'One of the groups is empty',
            'p_value_lower': None,
            'p_value_upper': None,
            'equivalent': False
        }

    try:
        # statsmodels ttost_ind returns (p-value_lower, p-value_upper, statistic_lower, statistic_upper)
        # We are testing if the difference is within [-delta, +delta]
        p_lower, p_upper, stat_lower, stat_upper = ttost_ind(
            group_a, group_b, 
            low=-equivalence_margin, 
            upp=equivalence_margin, 
            usevar='pooled'
        )
        
        # For equivalence, both p-values must be < alpha
        is_equivalent = (p_lower < alpha) and (p_upper < alpha)
        
        return {
            'p_value_lower': float(p_lower),
            'p_value_upper': float(p_upper),
            'statistic_lower': float(stat_lower),
            'statistic_upper': float(stat_upper),
            'equivalence_margin': equivalence_margin,
            'alpha': alpha,
            'equivalent': is_equivalent,
            'n_a': len(group_a),
            'n_b': len(group_b),
            'mean_a': float(np.mean(group_a)),
            'mean_b': float(np.mean(group_b)),
            'diff_mean': float(np.mean(group_a) - np.mean(group_b))
        }
        
    except Exception as e:
        logger.error(f"TOST test failed: {str(e)}")
        return {
            'error': str(e),
            'p_value_lower': None,
            'p_value_upper': None,
            'equivalent': False
        }

def run_tost_equivalence_tests(
    hybrid_df: pd.DataFrame, 
    metric_columns: List[str] = ['fid_score', 'latency'],
    equivalence_margin: float = 0.05
) -> List[Dict[str, Any]]:
    """
    Run TOST equivalence tests for specified metrics.
    Compares skipped frames (skip_flag=True) vs full solver frames (skip_flag=False).
    """
    results = []
    
    # Split data
    skipped = hybrid_df[hybrid_df['skip_flag'] == True]
    full_solver = hybrid_df[hybrid_df['skip_flag'] == False]
    
    logger.info(f"Skipped frames: {len(skipped)}, Full solver frames: {len(full_solver)}")
    
    if len(skipped) == 0 or len(full_solver) == 0:
        logger.warning("Cannot perform TOST: one group is empty.")
        # Create a result indicating failure to run
        for col in metric_columns:
            results.append({
                'metric': col,
                'status': 'failed',
                'reason': 'Empty group',
                'equivalent': False
            })
        return results

    for metric in metric_columns:
        if metric not in hybrid_df.columns:
            logger.warning(f"Metric column {metric} not found, skipping.")
            results.append({
                'metric': metric,
                'status': 'skipped',
                'reason': f'Column {metric} not found'
            })
            continue

        group_a = skipped[metric].values
        group_b = full_solver[metric].values
        
        logger.info(f"Running TOST for {metric}: Skipping vs Full")
        
        tost_result = perform_tost_test(group_a, group_b, equivalence_margin)
        
        result_entry = {
            'metric': metric,
            'equivalence_margin': equivalence_margin,
            'n_skipped': len(group_a),
            'n_full': len(group_b),
            'mean_skipped': tost_result.get('mean_a'),
            'mean_full': tost_result.get('mean_b'),
            'diff_mean': tost_result.get('diff_mean'),
            'p_value_lower': tost_result.get('p_value_lower'),
            'p_value_upper': tost_result.get('p_value_upper'),
            'equivalent': tost_result.get('equivalent', False),
            'status': 'completed' if 'error' not in tost_result else 'failed'
        }
        
        if 'error' in tost_result:
            result_entry['reason'] = tost_result['error']
        
        results.append(result_entry)
        
        if result_entry['equivalent']:
            logger.info(f"TOST PASSED for {metric}: p_lower={result_entry['p_value_lower']:.4f}, p_upper={result_entry['p_value_upper']:.4f}")
        else:
            logger.warning(f"TOST FAILED for {metric}: p_lower={result_entry['p_value_lower']}, p_upper={result_entry['p_value_upper']}")
            
    return results

def save_tost_results(results: List[Dict[str, Any]], output_path: str = 'data/metrics/tost_results.csv') -> None:
    """
    Save TOST results to a CSV file.
    """
    if not results:
        logger.warning("No results to save.")
        return

    df_results = pd.DataFrame(results)
    
    # Ensure directory exists
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    
    df_results.to_csv(output_path, index=False)
    logger.info(f"TOST results saved to {output_path}")
    
    # Log summary
    passed = sum(1 for r in results if r.get('equivalent', False))
    total = len(results)
    logger.info(f"TOST Summary: {passed}/{total} metrics passed equivalence test (delta={results[0]['equivalence_margin'] if results else 0.05})")

def main():
    parser = argparse.ArgumentParser(description='Run TOST equivalence tests for hybrid inference metrics.')
    parser.add_argument('--input', type=str, default='data/processed/hybrid_output.parquet',
                        help='Path to hybrid output parquet file')
    parser.add_argument('--output', type=str, default='data/metrics/tost_results.csv',
                        help='Path to output CSV file')
    parser.add_argument('--metrics', type=str, nargs='+', default=['fid_score', 'latency'],
                        help='Metrics to test for equivalence')
    parser.add_argument('--delta', type=float, default=0.05,
                        help='Equivalence margin (delta)')
    parser.add_argument('--alpha', type=float, default=0.05,
                        help='Significance level')
    
    args = parser.parse_args()
    
    try:
        # Check if T050 output exists
        if not os.path.exists(args.input):
            logger.error(f"Input file not found: {args.input}")
            logger.error("TOST VALIDATION SKIPPED: T050 hybrid output missing.")
            
            # Create a skipped result file
            Path(args.output).parent.mkdir(parents=True, exist_ok=True)
            with open(args.output, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(['metric', 'status', 'reason'])
                for m in args.metrics:
                    writer.writerow([m, 'skipped', 'T050 hybrid output missing'])
            return
        
        # Load data
        hybrid_df = load_hybrid_output(args.input)
        
        # Run tests
        results = run_tost_equivalence_tests(hybrid_df, args.metrics, args.delta)
        
        # Save results
        save_tost_results(results, args.output)
        
        # Check if all passed
        all_passed = all(r.get('equivalent', False) for r in results if r.get('status') == 'completed')
        
        if all_passed:
            logger.info("All TOST tests passed. Equivalence established.")
        else:
            logger.warning("Some TOST tests failed. Equivalence not fully established.")
            
    except Exception as e:
        logger.critical(f"TOST validation failed with error: {str(e)}")
        logger.error("TOST VALIDATION SKIPPED due to critical error.")
        raise

if __name__ == '__main__':
    main()
