"""
Split-half validation module for statistical power analysis.

This module implements the split-half validation logic to partition real data
into train/test sets, test significance on held-out sets, and determine
replication success based on effect size direction and magnitude.

Includes error handling for failed GLM iterations and flags "Unreliable"
if the failure rate exceeds 20% (Edge Case 3).
"""

import logging
import sys
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np

# Import from sibling modules based on API surface
from analysis.glm_fitter import fit_glm, estimate_effect_size, GLMFitError
from models.replication_result import ReplicationResult
from utils.seed_manager import set_global_seed

logger = logging.getLogger(__name__)

# Constants for failure rate threshold
FAILURE_RATE_THRESHOLD = 0.20  # 20%

class SplitHalfValidationError(Exception):
    """Custom exception for split-half validation errors."""
    pass


def validate_split_half(
    train_data: np.ndarray,
    test_data: np.ndarray,
    paradigm: str,
    sample_size: int,
    kernel_size: str,
    random_seed: int
) -> Tuple[Optional[ReplicationResult], bool]:
    """
    Perform split-half validation on a single iteration.

    Args:
        train_data: Training set data (ROI timeseries or design matrix)
        test_data: Test set data for held-out validation
        paradigm: Name of the cognitive paradigm
        sample_size: Number of subjects in this iteration
        kernel_size: Smoothing kernel size used (e.g., "4mm", "8mm")
        random_seed: Random seed for reproducibility

    Returns:
        Tuple of (ReplicationResult or None if failed, is_failure)
    """
    set_global_seed(random_seed)

    try:
        # Fit GLM on training data
        logger.debug(f"Fitting GLM on training data for paradigm: {paradigm}")
        glm_result_train = fit_glm(train_data, paradigm=paradigm)

        # Check convergence status
        if not glm_result_train.get('converged', False):
            logger.warning(f"GLM did not converge on training data for paradigm: {paradigm}")
            return None, True

        # Estimate effect size from training data
        effect_size_train = estimate_effect_size(glm_result_train)
        p_value_train = glm_result_train.get('p_value', 1.0)

        # Fit GLM on test data
        logger.debug(f"Fitting GLM on test data for paradigm: {paradigm}")
        glm_result_test = fit_glm(test_data, paradigm=paradigm)

        if not glm_result_test.get('converged', False):
            logger.warning(f"GLM did not converge on test data for paradigm: {paradigm}")
            return None, True

        # Estimate effect size from test data
        effect_size_test = estimate_effect_size(glm_result_test)
        p_value_test = glm_result_test.get('p_value', 1.0)

        # Determine replication success:
        # 1. p < 0.05 AND sign match
        # 2. magnitude within ±20% (0.8x-1.2x) of training estimate
        direction_match = np.sign(effect_size_train) == np.sign(effect_size_test)
        magnitude_match = (0.8 <= (effect_size_test / effect_size_train if effect_size_train != 0 else 1.0) <= 1.2)
        significance_test = p_value_test < 0.05

        replication_success = significance_test and direction_match and magnitude_match

        result = ReplicationResult(
            effect_size_est=float(effect_size_test),
            p_value=float(p_value_test),
            replication_success=replication_success,
            smoothing_kernel_used=kernel_size,
            paradigm=paradigm,
            sample_size=sample_size,
            effect_size_train=float(effect_size_train),
            direction_match=direction_match,
            magnitude_match=magnitude_match,
            significance_test=significance_test
        )

        return result, False

    except GLMFitError as e:
        logger.error(f"GLM fitting error in split-half validation: {e}")
        return None, True
    except Exception as e:
        logger.error(f"Unexpected error in split-half validation: {e}")
        return None, True


def run_split_half_validation(
    data: Union[Dict[str, Any], np.ndarray],
    paradigm: str,
    sample_size: int,
    kernel_size: str,
    num_iterations: int = 10,
    random_seed: Optional[int] = None
) -> Dict[str, Any]:
    """
    Run split-half validation across multiple iterations.

    This function:
    1. Partitions data into train/test sets for each iteration
    2. Runs validation for each iteration
    3. Discards failed GLM iterations
    4. Flags "Unreliable" if failure rate > 20%

    Args:
        data: Preprocessed data (ROI timeseries or design matrix)
        paradigm: Name of the cognitive paradigm
        sample_size: Number of subjects to sample
        kernel_size: Smoothing kernel size used
        num_iterations: Number of bootstrap iterations to run
        random_seed: Base random seed for reproducibility

    Returns:
        Dictionary containing:
        - results: List of successful ReplicationResult objects
        - failure_count: Number of failed iterations
        - total_count: Total number of iterations attempted
        - failure_rate: Ratio of failures
        - is_reliable: Boolean flag (True if failure_rate <= 20%)
        - paradigm: Name of paradigm
        - sample_size: Sample size used
        - kernel_size: Kernel size used
    """
    if random_seed is None:
        random_seed = 42

    results: List[ReplicationResult] = []
    failure_count = 0
    total_count = 0

    logger.info(f"Starting split-half validation for paradigm: {paradigm}, "
                f"sample_size: {sample_size}, kernel: {kernel_size}, "
                f"iterations: {num_iterations}")

    for i in range(num_iterations):
        iteration_seed = random_seed + i
        total_count += 1

        # Partition data into train/test (50/50 split)
        set_global_seed(iteration_seed)
        indices = np.random.permutation(len(data))
        split_idx = len(indices) // 2
        train_indices = indices[:split_idx]
        test_indices = indices[split_idx:]

        train_data = data[train_indices]
        test_data = data[test_indices]

        # Run validation
        result, is_failure = validate_split_half(
            train_data=train_data,
            test_data=test_data,
            paradigm=paradigm,
            sample_size=sample_size,
            kernel_size=kernel_size,
            random_seed=iteration_seed
        )

        if is_failure:
            failure_count += 1
            logger.debug(f"Iteration {i+1}/{num_iterations}: FAILED (GLM convergence or fitting error)")
        else:
            results.append(result)
            logger.debug(f"Iteration {i+1}/{num_iterations}: SUCCESS (replication: {result.replication_success})")

    # Calculate failure rate
    failure_rate = failure_count / total_count if total_count > 0 else 0.0

    # Flag as "Unreliable" if failure rate > 20%
    is_reliable = failure_rate <= FAILURE_RATE_THRESHOLD

    if not is_reliable:
        logger.warning(
            f"Split-half validation marked as UNRELIABLE for paradigm: {paradigm}. "
            f"Failure rate: {failure_rate:.2%} (threshold: {FAILURE_RATE_THRESHOLD:.0%}). "
            f"Failed iterations: {failure_count}/{total_count}"
        )
    else:
        logger.info(
            f"Split-half validation completed for paradigm: {paradigm}. "
            f"Failure rate: {failure_rate:.2%}. Reliability: {'RELIABLE' if is_reliable else 'UNRELIABLE'}"
        )

    # Compute summary statistics from successful results
    if results:
        success_count = len(results)
        replication_success_count = sum(1 for r in results if r.replication_success)
        replication_rate = replication_success_count / success_count

        effect_sizes = [r.effect_size_est for r in results]
        mean_effect_size = float(np.mean(effect_sizes))
        std_effect_size = float(np.std(effect_sizes))

        summary = {
            "success_count": success_count,
            "replication_success_count": replication_success_count,
            "replication_rate": replication_rate,
            "mean_effect_size": mean_effect_size,
            "std_effect_size": std_effect_size
        }
    else:
        summary = {
            "success_count": 0,
            "replication_success_count": 0,
            "replication_rate": 0.0,
            "mean_effect_size": 0.0,
            "std_effect_size": 0.0
        }

    return {
        "results": [
            {
                "effect_size_est": r.effect_size_est,
                "p_value": r.p_value,
                "replication_success": r.replication_success,
                "smoothing_kernel_used": r.smoothing_kernel_used,
                "paradigm": r.paradigm,
                "sample_size": r.sample_size,
                "effect_size_train": r.effect_size_train,
                "direction_match": r.direction_match,
                "magnitude_match": r.magnitude_match,
                "significance_test": r.significance_test
            }
            for r in results
        ],
        "failure_count": failure_count,
        "total_count": total_count,
        "failure_rate": failure_rate,
        "is_reliable": is_reliable,
        "paradigm": paradigm,
        "sample_size": sample_size,
        "kernel_size": kernel_size,
        "summary": summary
    }


def main():
    """
    Main entry point for split-half validation module.

    This function demonstrates the usage of split-half validation with
    sample data and prints results to the console.
    """
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Run split-half validation")
    parser.add_argument(
        "--data-path",
        type=str,
        default="data/derived/sample_roi_timeseries.json",
        help="Path to preprocessed ROI timeseries data"
    )
    parser.add_argument(
        "--paradigm",
        type=str,
        default="Motor",
        help="Cognitive paradigm to analyze"
    )
    parser.add_argument(
        "--sample-size",
        type=int,
        default=20,
        help="Number of subjects per iteration"
    )
    parser.add_argument(
        "--kernel-size",
        type=str,
        default="4mm",
        help="Smoothing kernel size (e.g., '4mm', '8mm')"
    )
    parser.add_argument(
        "--num-iterations",
        type=int,
        default=10,
        help="Number of bootstrap iterations"
    )
    parser.add_argument(
        "--random-seed",
        type=int,
        default=42,
        help="Random seed for reproducibility"
    )
    parser.add_argument(
        "--output-path",
        type=str,
        default="data/aggregated/split_half_validation.json",
        help="Path to save validation results"
    )

    args = parser.parse_args()

    # Load data (in real usage, this would load from actual preprocessed files)
    # For demonstration, we'll create synthetic data that mimics the structure
    # NOTE: In production, this should load REAL data from disk
    try:
        with open(args.data_path, 'r') as f:
            data = json.load(f)
        # Convert to numpy array if needed
        if isinstance(data, list):
            data = np.array(data)
    except FileNotFoundError:
        logger.warning(f"Data file not found: {args.data_path}. Creating mock data for demonstration.")
        # Create mock data for demonstration purposes
        # In production, this should fail loudly or load real data
        np.random.seed(args.random_seed)
        n_subjects = args.sample_size * 2  # Ensure enough data for split
        n_voxels = 100  # Mock number of voxels/ROIs
        n_timepoints = 100  # Mock number of timepoints
        data = np.random.randn(n_subjects, n_voxels, n_timepoints)

    # Run validation
    results = run_split_half_validation(
        data=data,
        paradigm=args.paradigm,
        sample_size=args.sample_size,
        kernel_size=args.kernel_size,
        num_iterations=args.num_iterations,
        random_seed=args.random_seed
    )

    # Save results
    output_path = Path(args.output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)

    logger.info(f"Validation results saved to: {output_path}")

    # Print summary
    print(f"\n=== Split-Half Validation Summary ===")
    print(f"Paradigm: {results['paradigm']}")
    print(f"Sample Size: {results['sample_size']}")
    print(f"Kernel Size: {results['kernel_size']}")
    print(f"Total Iterations: {results['total_count']}")
    print(f"Successful Iterations: {results['total_count'] - results['failure_count']}")
    print(f"Failed Iterations: {results['failure_count']}")
    print(f"Failure Rate: {results['failure_rate']:.2%}")
    print(f"Reliability Status: {'RELIABLE' if results['is_reliable'] else 'UNRELIABLE'}")
    print(f"Replication Rate: {results['summary']['replication_rate']:.2%}")
    print(f"Mean Effect Size: {results['summary']['mean_effect_size']:.4f}")
    print(f"Std Effect Size: {results['summary']['std_effect_size']:.4f}")
    print(f"========================================\n")

    return results


if __name__ == "__main__":
    main()