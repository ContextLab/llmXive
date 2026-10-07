"""
Split-half validator for bootstrap power analysis.

This module implements the bootstrap loop:
1. Load full dataset
2. For each sample size, run >= 50 random split-half iterations
3. Subsample subjects into train/test sets per iteration
4. Fit GLM on training half
5. Check convergence and magnitude/direction match
6. Aggregate replication success rates
"""

import gc
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd

from utils.seed_manager import set_global_seed, get_seed
from utils.data_leakage_guard import verify_no_leakage, force_memory_isolation
from analysis.glm_fitter import fit_glm_batch, ConvergenceLogger

logger = logging.getLogger(__name__)

class SplitHalfValidationError(Exception):
    """Raised when split-half validation fails."""
    pass

def load_preprocessed_data(data_path: Union[str, Path]) -> pd.DataFrame:
    """
    Load preprocessed ROI timeseries data.
    
    Args:
        data_path: Path to the data file.
        
    Returns:
        DataFrame with subject data.
    """
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Preprocessed data not found: {data_path}")
    
    if data_path.suffix == '.csv':
        return pd.read_csv(data_path)
    elif data_path.suffix == '.npy':
        data = np.load(data_path)
        if data.ndim == 3:
            n_subjects, n_timepoints, n_rois = data.shape
            df = pd.DataFrame(
                data.reshape(n_subjects, -1),
                columns=[f'feature_{i}' for i in range(n_timepoints * n_rois)]
            )
        else:
            df = pd.DataFrame(data)
        return df
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")

def validate_split_half(train_data: pd.DataFrame, test_data: pd.DataFrame, 
                        design_matrix: np.ndarray, seed: int) -> Dict[str, Any]:
    """
    Perform a single split-half validation iteration.
    
    Args:
        train_data: Training set data.
        test_data: Test set data.
        design_matrix: Design matrix for GLM.
        seed: Random seed for this iteration.
        
    Returns:
        Dictionary with replication success status and metrics.
    """
    set_global_seed(seed)
    
    # Verify no data leakage
    try:
        verify_no_leakage(train_data, test_data)
    except Exception as e:
        logger.error(f"Data leakage detected: {e}")
        return {
            "replication_success": 0,
            "reason": "data_leakage",
            "error": str(e)
        }
    
    # Fit GLM on training data
    train_result = fit_glm_batch(
        train_data, design_matrix, len(train_data), seed=seed,
        iteration_id=seed, paradigm="split_half"
    )
    
    if not train_result['converged']:
        return {
            "replication_success": 0,
            "reason": "train_convergence_failure",
            "train_effect_size": train_result['effect_size']
        }
    
    # Fit GLM on test data
    test_result = fit_glm_batch(
        test_data, design_matrix, len(test_data), seed=seed + 1000,
        iteration_id=seed + 1000, paradigm="split_half"
    )
    
    if not test_result['converged']:
        return {
            "replication_success": 0,
            "reason": "test_convergence_failure",
            "train_effect_size": train_result['effect_size'],
            "test_effect_size": test_result['effect_size']
        }
    
    # Check magnitude match (within 20%)
    train_d = train_result['effect_size']
    test_d = test_result['effect_size']
    
    if train_d == 0:
        magnitude_match = (test_d == 0)
    else:
        magnitude_match = abs(test_d - train_d) <= 0.2 * abs(train_d)
    
    # Check direction match
    direction_match = np.sign(train_d) == np.sign(test_d)
    
    # Check p-value threshold
    p_threshold_match = test_result['p_value'] < 0.05
    
    replication_success = int(magnitude_match and direction_match and p_threshold_match)
    
    return {
        "replication_success": replication_success,
        "train_effect_size": train_d,
        "test_effect_size": test_d,
        "magnitude_match": magnitude_match,
        "direction_match": direction_match,
        "p_threshold_match": p_threshold_match,
        "train_p_value": train_result['p_value'],
        "test_p_value": test_result['p_value']
    }

def run_split_half_validation(data: pd.DataFrame, sample_size: int, 
                              n_iterations: int = 50, seed: Optional[int] = None,
                              design_matrix: Optional[np.ndarray] = None) -> List[Dict[str, Any]]:
    """
    Run the full split-half validation loop.
    
    Args:
        data: Full dataset.
        sample_size: Number of subjects per half.
        n_iterations: Number of bootstrap iterations.
        seed: Random seed for reproducibility.
        design_matrix: Optional design matrix.
        
    Returns:
        List of iteration results.
    """
    if seed is None:
        seed = get_seed()
    
    if design_matrix is None:
        # Simple design: intercept only
        design_matrix = np.ones((len(data), 1))
    
    results = []
    total_success = 0
    
    for i in range(n_iterations):
        iter_seed = seed + i
        set_global_seed(iter_seed)
        
        # Split data into train/test
        indices = np.random.permutation(len(data))
        half = len(indices) // 2
        
        train_indices = indices[:half]
        test_indices = indices[half:]
        
        train_data = data.iloc[train_indices].reset_index(drop=True)
        test_data = data.iloc[test_indices].reset_index(drop=True)
        
        # Ensure we have enough data
        if len(train_data) < 2 or len(test_data) < 2:
            logger.warning(f"Iteration {i}: Insufficient data for split. Skipping.")
            results.append({
                "iteration": i,
                "replication_success": 0,
                "reason": "insufficient_data"
            })
            continue
        
        # Run validation
        result = validate_split_half(train_data, test_data, design_matrix, iter_seed)
        result['iteration'] = i
        results.append(result)
        
        total_success += result['replication_success']
        
        # Force memory isolation between iterations
        force_memory_isolation(train_data)
        force_memory_isolation(test_data)
        gc.collect()
    
    replication_rate = total_success / n_iterations if n_iterations > 0 else 0.0
    
    logger.info(f"Split-half validation complete. Replication rate: {replication_rate:.3f} ({total_success}/{n_iterations})")
    
    return results

def aggregate_split_half_results(results: List[Dict[str, Any]], sample_size: int, 
                                 kernel: str = "4s") -> Dict[str, Any]:
    """
    Aggregate split-half results into summary statistics.
    
    Args:
        results: List of iteration results.
        sample_size: Sample size used.
        kernel: Smoothing kernel used.
        
    Returns:
        Aggregated results dictionary.
    """
    successes = [r['replication_success'] for r in results if 'replication_success' in r]
    total = len(successes)
    rate = sum(successes) / total if total > 0 else 0.0
    
    return {
        "sample_size": sample_size,
        "kernel": kernel,
        "replication_rate": rate,
        "iterations": total,
        "successful_iterations": sum(successes),
        "failed_iterations": total - sum(successes),
        "details": results
    }

def save_split_half_results(aggregated_results: List[Dict[str, Any]], 
                            output_path: str = "data/aggregated/split_half_results.json"):
    """
    Save aggregated split-half results to JSON.
    
    Args:
        aggregated_results: List of aggregated result dictionaries.
        output_path: Output file path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(aggregated_results, f, indent=2)
    
    logger.info(f"Saved split-half results to {output_path}")

def main():
    """CLI entry point for split-half validation."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Run split-half validation")
    parser.add_argument("--data", type=str, required=True, help="Path to preprocessed data")
    parser.add_argument("--sample-size", type=int, default=10, help="Sample size per half")
    parser.add_argument("--n-iterations", type=int, default=50, help="Number of iterations")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--kernel", type=str, default="4s", help="Smoothing kernel")
    parser.add_argument("--output", type=str, default="data/aggregated/split_half_results.json", help="Output file")
    
    args = parser.parse_args()
    
    # Load data
    data = load_preprocessed_data(args.data)
    logger.info(f"Loaded {len(data)} subjects from {args.data}")
    
    # Run validation
    results = run_split_half_validation(
        data, args.sample_size, args.n_iterations, args.seed
    )
    
    # Aggregate
    aggregated = aggregate_split_half_results(results, args.sample_size, args.kernel)
    
    # Save
    save_split_half_results([aggregated], args.output)
    
    print(f"Split-half validation complete. Replication rate: {aggregated['replication_rate']:.3f}")
    return aggregated

if __name__ == "__main__":
    main()
