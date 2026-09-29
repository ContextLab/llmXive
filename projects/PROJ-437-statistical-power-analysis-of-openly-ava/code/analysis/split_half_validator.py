"""
Split-half validation module for statistical power analysis.

This module implements the bootstrap loop for estimating empirical replication
probabilities across different sample sizes. It performs strict memory isolation
between training and test sets to prevent data leakage.
"""

import logging
import sys
import json
import gc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.genmod.generalized_linear_model import GLM
from statsmodels.genmod import families
from statsmodels.tools import add_constant

from models.replication_result import ReplicationResult
from utils.seed_manager import set_global_seed, get_seed
from analysis.glm_fitter import fit_glm, GLMFitError, ConvergenceLogger
from utils.memory_monitor import check_memory_threshold, trigger_gc

logger = logging.getLogger(__name__)

class SplitHalfValidationError(Exception):
    """Custom exception for split-half validation errors."""
    pass


def validate_split_half(
    data: pd.DataFrame,
    sample_size: int,
    alpha: float = 0.05,
    seed: Optional[int] = None,
    max_iterations: int = 50,
    magnitude_threshold: float = 0.20
) -> Tuple[List[ReplicationResult], Dict[str, Any]]:
    """
    Perform a single split-half validation iteration.

    Args:
        data: Preprocessed ROI time-series data with columns including 'condition'
        sample_size: Number of subjects to use for this iteration
        alpha: Significance threshold
        seed: Random seed for reproducibility
        max_iterations: Maximum bootstrap iterations (used here as loop count)
        magnitude_threshold: Maximum allowed relative difference (e.g., 0.20 for 20%)

    Returns:
        Tuple of (list of ReplicationResult, metadata dict)
    """
    if seed is not None:
        set_global_seed(seed)

    n_total = len(data)
    if n_total < sample_size * 2:
        raise SplitHalfValidationError(
            f"Insufficient data: requested {sample_size * 2} subjects, "
            f"but only {n_total} available."
        )

    # Shuffle indices
    indices = np.random.permutation(n_total)
    
    # Split into train and test
    mid_point = sample_size
    train_indices = indices[:mid_point]
    test_indices = indices[mid_point : mid_point * 2]

    train_data = data.iloc[train_indices].reset_index(drop=True)
    test_data = data.iloc[test_indices].reset_index(drop=True)

    # Fit GLM on training set
    try:
        glm_result_train = fit_glm(
            train_data, 
            target_col='condition', 
            seed=seed
        )
        
        # Check convergence status immediately
        if not glm_result_train.get('converged', False):
            return [], {'status': 'convergence_failed', 'reason': 'Training GLM did not converge'}
        
        effect_size_train = glm_result_train.get('cohen_d')
        p_value_train = glm_result_train.get('p_value')
        
        if effect_size_train is None or p_value_train is None:
            raise SplitHalfValidationError("GLM fit returned invalid effect size or p-value")

    except GLMFitError as e:
        logger.warning(f"GLM fit failed on training set: {e}")
        return [], {'status': 'convergence_failed', 'reason': str(e)}

    # Predict on test set using training coefficients
    # Note: In a real scenario, we would apply the training model to test data
    # Here we simulate the test fit using the same design matrix structure
    try:
        # For split-half validation, we re-fit on test set to compare
        # This is the standard approach: fit on train, check if effect direction/magnitude holds on test
        glm_result_test = fit_glm(
            test_data,
            target_col='condition',
            seed=seed
        )
        
        if not glm_result_test.get('converged', False):
            return [], {'status': 'convergence_failed', 'reason': 'Test GLM did not converge'}
            
        effect_size_test = glm_result_test.get('cohen_d')
        p_value_test = glm_result_test.get('p_value')
        
        if effect_size_test is None or p_value_test is None:
            raise SplitHalfValidationError("Test GLM fit returned invalid effect size or p-value")

    except GLMFitError as e:
        logger.warning(f"GLM fit failed on test set: {e}")
        return [], {'status': 'convergence_failed', 'reason': str(e)}

    # Determine replication success
    # Criteria:
    # 1. Direction match (sign of effect sizes)
    # 2. Magnitude within ±20% of training estimate
    # 3. p < alpha in test set (or at least significant direction)
    
    direction_match = np.sign(effect_size_train) == np.sign(effect_size_test)
    
    if abs(effect_size_train) > 0:
        magnitude_diff = abs(effect_size_test - effect_size_train) / abs(effect_size_train)
        magnitude_match = magnitude_diff <= magnitude_threshold
    else:
        # If training effect is zero, any non-zero test effect is a mismatch
        magnitude_match = (effect_size_test == 0)
    
    p_significant = p_value_test < alpha

    replication_success = direction_match and magnitude_match and p_significant

    result = ReplicationResult(
        effect_size_est=effect_size_test,
        p_value=p_value_test,
        replication_success=replication_success,
        smoothing_kernel_used="temporal_4s",  # Default, updated by caller
        iteration_seed=seed
    )

    return [result], {
        'status': 'success',
        'train_effect': effect_size_train,
        'test_effect': effect_size_test,
        'p_value': p_value_test,
        'direction_match': direction_match,
        'magnitude_match': magnitude_match,
        'p_significant': p_significant
    }


def run_split_half_validation(
    data: pd.DataFrame,
    sample_size: int,
    num_iterations: int = 50,
    alpha: float = 0.05,
    base_seed: int = 42,
    smoothing_kernel: str = "temporal_4s"
) -> Tuple[float, List[ReplicationResult], Dict[str, Any]]:
    """
    Run the full bootstrap loop for split-half validation.

    Discards iterations that fail to converge.
    Flags the run as "Unreliable" if > 20% of iterations fail to converge.

    Args:
        data: Preprocessed ROI time-series data
        sample_size: Target sample size per half
        num_iterations: Number of bootstrap iterations
        alpha: Significance threshold
        base_seed: Base random seed
        smoothing_kernel: Kernel identifier for logging

    Returns:
        Tuple of (empirical_replication_rate, list of results, metadata)
    """
    if not isinstance(data, pd.DataFrame) or data.empty:
        raise SplitHalfValidationError("Input data must be a non-empty DataFrame")

    set_global_seed(base_seed)
    
    results: List[ReplicationResult] = []
    metadata_list: List[Dict[str, Any]] = []
    convergence_failures = 0
    total_attempts = 0

    logger.info(f"Starting split-half validation: N={sample_size}, iterations={num_iterations}")

    for i in range(num_iterations):
        total_attempts += 1
        current_seed = base_seed + i
        
        try:
            iteration_results, meta = validate_split_half(
                data=data,
                sample_size=sample_size,
                alpha=alpha,
                seed=current_seed,
                max_iterations=1,
                magnitude_threshold=0.20
            )
            
            if meta.get('status') == 'convergence_failed':
                convergence_failures += 1
                metadata_list.append({
                    'iteration': i,
                    'status': 'convergence_failed',
                    'reason': meta.get('reason', 'Unknown')
                })
                logger.debug(f"Iteration {i} failed convergence: {meta.get('reason')}")
                continue
            
            if iteration_results:
                results.append(iteration_results[0])
                metadata_list.append({
                    'iteration': i,
                    'status': 'success',
                    'details': meta
                })
            
            # Memory cleanup
            if i % 10 == 0:
                check_memory_threshold()
                trigger_gc()
                gc.collect()
                
        except Exception as e:
            convergence_failures += 1
            logger.warning(f"Iteration {i} raised exception: {e}")
            metadata_list.append({
                'iteration': i,
                'status': 'error',
                'reason': str(e)
            })

    # Calculate failure rate
    failure_rate = convergence_failures / total_attempts if total_attempts > 0 else 1.0
    reliability_flag = "Unreliable" if failure_rate > 0.20 else "Reliable"
    
    logger.info(f"Split-half validation complete: {len(results)}/{total_attempts} successful, "
                f"failure rate={failure_rate:.2f}, status={reliability_flag}")

    # Calculate empirical replication rate
    if len(results) == 0:
        empirical_rate = 0.0
    else:
        successful_replications = sum(1 for r in results if r.replication_success)
        empirical_rate = successful_replications / len(results)

    return empirical_rate, results, {
        'total_attempts': total_attempts,
        'successful_iterations': len(results),
        'convergence_failures': convergence_failures,
        'failure_rate': failure_rate,
        'reliability_flag': reliability_flag,
        'empirical_replication_rate': empirical_rate,
        'sample_size': sample_size,
        'alpha': alpha,
        'smoothing_kernel': smoothing_kernel
    }


def main():
    """
    CLI entry point for split-half validation.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Run split-half validation for power analysis")
    parser.add_argument("--data", type=str, required=True, help="Path to preprocessed data CSV")
    parser.add_argument("--sample-size", type=int, default=20, help="Sample size per half")
    parser.add_argument("--iterations", type=int, default=50, help="Number of bootstrap iterations")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance threshold")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/aggregated/split_half_results.json",
                        help="Output JSON file path")
    parser.add_argument("--kernel", type=str, default="temporal_4s", help="Smoothing kernel used")

    args = parser.parse_args()

    # Load data
    logger.info(f"Loading data from {args.data}")
    if not Path(args.data).exists():
        logger.error(f"Data file not found: {args.data}")
        sys.exit(1)

    data = pd.read_csv(args.data)

    # Run validation
    rate, results, meta = run_split_half_validation(
        data=data,
        sample_size=args.sample_size,
        num_iterations=args.iterations,
        alpha=args.alpha,
        base_seed=args.seed,
        smoothing_kernel=args.kernel
    )

    # Save results
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    output_data = {
        'empirical_replication_rate': rate,
        'metadata': meta,
        'individual_results': [
            {
                'effect_size_est': r.effect_size_est,
                'p_value': r.p_value,
                'replication_success': r.replication_success,
                'smoothing_kernel_used': r.smoothing_kernel_used
            }
            for r in results
        ]
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    logger.info(f"Results saved to {output_path}")
    print(f"Empirical Replication Rate: {rate:.4f}")
    print(f"Reliability Status: {meta['reliability_flag']}")

    if meta['reliability_flag'] == "Unreliable":
        logger.warning(f"High convergence failure rate ({meta['failure_rate']:.2f}) detected. "
                       f"Run flagged as Unreliable.")
        sys.exit(0)  # Exit 0 but log warning

    sys.exit(0)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()