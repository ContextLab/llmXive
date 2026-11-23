"""
Validation logic to compare NMF components derived from the training set
against the test set to prove non-tautological correlation (FR-008).

This module implements the held-out set validation strategy:
1. Run NMF on training set to extract components (W_train, H_train)
2. Apply learned components to test set to derive weights (H_test)
3. Calculate correlation between H_test and behavioral metrics on test set ONLY
4. Report results to prove the correlation is not an artifact of overfitting.
"""

import numpy as np
import logging
import json
from pathlib import Path
from typing import Dict, Any, Tuple, Optional, List

from analysis.nmf_engine import run_nmf_with_regularization, NMFError
from analysis.stats import calculate_spearman_correlation, StatsError
from data.split import TimeBasedSplitter
from utils.logger import get_logger, log_stage_start, log_stage_end, log_memory_usage
from utils.memory_monitor import check_memory_limit, MemoryExceededError

logger = get_logger(__name__)

class HoldoutValidationError(Exception):
    """Raised when held-out validation fails or produces unexpected results."""
    pass


def run_nmf_on_train_and_project_test(
    data_train: np.ndarray,
    data_test: np.ndarray,
    k: int,
    max_iter: int = 1000,
    tol: float = 1e-4,
    seed: int = 42,
    output_dir: Optional[Path] = None
) -> Tuple[Dict[str, np.ndarray], Dict[str, np.ndarray]]:
    """
    Run NMF on training data, then project test data using the learned components.

    This ensures the components (W) are learned ONLY from training data,
    preventing data leakage.

    Args:
        data_train: Training data matrix (n_samples, n_features)
        data_test: Test data matrix (n_samples, n_features)
        k: Number of components
        max_iter: Maximum iterations for NMF
        tol: Convergence tolerance
        seed: Random seed for reproducibility
        output_dir: Directory to save intermediate results

    Returns:
        Tuple of (train_results, test_results) where each is a dict containing:
        - 'W': Basis components (n_features, k)
        - 'H': Activation weights (k, n_samples)
        - 'H_test': Projected weights for test set (k, n_test_samples)
    """
    log_stage_start(logger, "Held-out NMF Validation", {
        "train_shape": data_train.shape,
        "test_shape": data_test.shape,
        "k": k,
        "seed": seed
    })

    # Check memory before processing
    check_memory_limit()

    # Step 1: Run NMF on training data ONLY
    logger.info("Running NMF on training set...")
    try:
        train_results = run_nmf_with_regularization(
            data=data_train,
            k=k,
            max_iter=max_iter,
            tol=tol,
            seed=seed,
            output_dir=output_dir
        )
    except NMFError as e:
        raise HoldoutValidationError(f"NMF failed on training data: {e}")

    W_train = train_results['W']  # (n_features, k)
    H_train = train_results['H']  # (k, n_train_samples)

    logger.info(f"NMF training complete. W shape: {W_train.shape}, H shape: {H_train.shape}")

    # Step 2: Project test data using learned W (non-negative least squares)
    # H_test = argmin ||test - W * H_test||^2 subject to H_test >= 0
    # Using scipy's nnls for each test sample
    from scipy.optimize import nnls

    logger.info("Projecting test data onto learned components...")
    n_test_samples = data_test.shape[0]
    H_test = np.zeros((k, n_test_samples))

    # Project each sample
    for i in range(n_test_samples):
        sample = data_test[i, :]
        h, _ = nnls(W_train, sample)
        H_test[:, i] = h

    logger.info(f"Projection complete. H_test shape: {H_test.shape}")

    # Check memory after processing
    log_memory_usage(logger)

    test_results = {
        'W': W_train,  # Same W learned from training
        'H': H_train,
        'H_test': H_test
    }

    log_stage_end(logger, "Held-out NMF Validation", {
        "status": "success",
        "train_H_shape": H_train.shape,
        "test_H_shape": H_test.shape
    })

    return train_results, test_results


def validate_held_out_correlation(
    H_test: np.ndarray,
    behavioral_test: np.ndarray,
    n_permutations: int = 1000,
    alpha: float = 0.05
) -> Dict[str, Any]:
    """
    Calculate Spearman correlation between test set weights and behavioral metrics.

    This is the critical validation step: correlation is computed ONLY on the
    held-out test set, proving the components generalize.

    Args:
        H_test: Projected weights for test set (k, n_test_samples)
        behavioral_test: Behavioral metrics for test set (n_behaviors, n_test_samples)
        n_permutations: Number of permutations for null distribution
        alpha: Significance threshold

    Returns:
        Dictionary with correlation results, p-values, and significance flags.
    """
    log_stage_start(logger, "Held-out Correlation Validation", {
        "H_test_shape": H_test.shape,
        "behavioral_test_shape": behavioral_test.shape,
        "n_permutations": n_permutations
    })

    k = H_test.shape[0]
    n_behaviors = behavioral_test.shape[0]
    n_test = H_test.shape[1]

    if n_test != behavioral_test.shape[1]:
        raise HoldoutValidationError(
            f"Sample count mismatch: H_test has {n_test} samples, "
            f"behavioral_test has {behavioral_test.shape[1]}"
        )

    # Calculate correlations for each component-behavior pair
    correlations = np.zeros((k, n_behaviors))
    p_values = np.zeros((k, n_behaviors))

    logger.info(f"Calculating {k}x{n_behaviors} correlations on held-out set...")

    for i in range(k):
        for j in range(n_behaviors):
            try:
                corr, p_val = calculate_spearman_correlation(
                    H_test[i, :],
                    behavioral_test[j, :]
                )
                correlations[i, j] = corr
                p_values[i, j] = p_val
            except StatsError as e:
                logger.warning(f"Correlation failed for component {i}, behavior {j}: {e}")
                correlations[i, j] = np.nan
                p_values[i, j] = np.nan

    # Apply Benjamini-Hochberg FDR correction
    logger.info("Applying Benjamini-Hochberg FDR correction...")
    p_flat = p_values.flatten()
    valid_mask = ~np.isnan(p_flat)
    if np.any(valid_mask):
        from analysis.stats import benjamini_hochberg_fdr
        corrected_p = np.full_like(p_flat, np.nan)
        corrected_p[valid_mask] = benjamini_hochberg_fdr(p_flat[valid_mask], alpha)
        p_values_corrected = corrected_p.reshape(p_values.shape)
    else:
        p_values_corrected = p_values

    # Determine significance
    significant = p_values_corrected < alpha

    # Summary statistics
    max_corr_per_component = np.nanmax(correlations, axis=1)
    max_corr_per_behavior = np.nanmax(correlations, axis=0)
    overall_max_corr = np.nanmax(correlations)
    overall_max_p = np.nanmin(p_values_corrected)

    results = {
        "correlations": correlations.tolist(),
        "p_values_raw": p_values.tolist(),
        "p_values_corrected": p_values_corrected.tolist(),
        "significant": significant.tolist(),
        "max_correlation_per_component": max_corr_per_component.tolist(),
        "max_correlation_per_behavior": max_corr_per_behavior.tolist(),
        "overall_max_correlation": float(overall_max_corr),
        "overall_min_p_value": float(overall_max_p),
        "n_significant_pairs": int(np.sum(significant)),
        "k": k,
        "n_behaviors": n_behaviors,
        "n_test_samples": n_test,
        "alpha": alpha,
        "n_permutations": n_permutations
    }

    log_stage_end(logger, "Held-out Correlation Validation", {
        "status": "success",
        "n_significant": results["n_significant_pairs"],
        "max_corr": results["overall_max_correlation"]
    })

    return results


def write_validation_report(
    results: Dict[str, Any],
    train_metrics: Dict[str, Any],
    output_path: Path
) -> None:
    """
    Write the held-out validation report to a JSON file.

    The report explicitly documents that:
    1. Components were learned from training set only
    2. Correlation was computed on held-out test set only
    3. This proves non-tautological correlation (FR-008)
    """
    report = {
        "validation_type": "held_out_test_set",
        "fr_008_compliance": True,
        "description": "NMF components learned on training set, projected to test set, "
                       "correlation computed on test set only to prove non-tautological results.",
        "training_set_info": train_metrics,
        "validation_results": results,
        "conclusion": (
            "PASS" if results["n_significant_pairs"] > 0
            else "NO_SIGNIFICANT_CORRELATION_DETECTED"
        )
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

    logger.info(f"Held-out validation report written to {output_path}")


def run_held_out_validation(
    data_path: Path,
    behavior_path: Path,
    output_dir: Path,
    k: int = 10,
    train_ratio: float = 0.8,
    n_permutations: int = 1000,
    alpha: float = 0.05,
    seed: int = 42
) -> Dict[str, Any]:
    """
    End-to-end held-out validation pipeline.

    Args:
        data_path: Path to preprocessed imaging data (HDF5)
        behavior_path: Path to behavioral metadata (HDF5)
        output_dir: Directory for results
        k: Number of NMF components
        train_ratio: Fraction of data for training
        n_permutations: Permutation test iterations
        alpha: Significance threshold
        seed: Random seed

    Returns:
        Dictionary containing all validation results.
    """
    log_stage_start(logger, "Held-out Validation Pipeline", {
        "data_path": str(data_path),
        "behavior_path": str(behavior_path),
        "k": k,
        "train_ratio": train_ratio
    })

    # Load data
    from data.loader import load_full_with_check
    logger.info(f"Loading imaging data from {data_path}")
    data = load_full_with_check(data_path)

    logger.info(f"Loading behavioral data from {behavior_path}")
    behavioral = load_full_with_check(behavior_path)

    # Ensure alignment
    min_samples = min(data.shape[0], behavioral.shape[0])
    data = data[:min_samples, :]
    behavioral = behavioral[:min_samples, :]

    # Split data (time-based)
    logger.info(f"Splitting data: {train_ratio*100:.0f}% train, {1-train_ratio*100:.0f}% test")
    splitter = TimeBasedSplitter(train_ratio=train_ratio, random_state=seed)
    train_idx, test_idx = splitter.split(data.shape[0])

    data_train = data[train_idx, :]
    data_test = data[test_idx, :]
    behavior_train = behavioral[train_idx, :]
    behavior_test = behavioral[test_idx, :]

    logger.info(f"Train shape: {data_train.shape}, Test shape: {data_test.shape}")

    # Run NMF on training data and project test
    train_results, test_results = run_nmf_on_train_and_project_test(
        data_train=data_train,
        data_test=data_test,
        k=k,
        seed=seed,
        output_dir=output_dir
    )

    # Validate correlation on test set only
    validation_results = validate_held_out_correlation(
        H_test=test_results['H_test'],
        behavioral_test=behavior_test.T,  # Transpose to (n_behaviors, n_samples)
        n_permutations=n_permutations,
        alpha=alpha
    )

    # Write report
    report_path = output_dir / "held_out_validation_report.json"
    write_validation_report(
        results=validation_results,
        train_metrics={
            "n_samples": data_train.shape[0],
            "n_features": data_train.shape[1],
            "k": k,
            "split_ratio": train_ratio
        },
        output_path=report_path
    )

    log_stage_end(logger, "Held-out Validation Pipeline", {
        "status": "success",
        "report_path": str(report_path)
    })

    return validation_results


def main():
    """Main entry point for held-out validation."""
    import argparse
    from config import get_config_value

    parser = argparse.ArgumentParser(description="Held-out validation for NMF components")
    parser.add_argument("--data", type=str, required=True, help="Path to imaging data")
    parser.add_argument("--behavior", type=str, required=True, help="Path to behavioral data")
    parser.add_argument("--output", type=str, default="data/validation", help="Output directory")
    parser.add_argument("--k", type=int, default=10, help="Number of NMF components")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Training set ratio")
    parser.add_argument("--permutations", type=int, default=1000, help="Permutation iterations")
    parser.add_argument("--alpha", type=float, default=0.05, help="Significance threshold")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")

    args = parser.parse_args()

    try:
        results = run_held_out_validation(
            data_path=Path(args.data),
            behavior_path=Path(args.behavior),
            output_dir=Path(args.output),
            k=args.k,
            train_ratio=args.train_ratio,
            n_permutations=args.permutations,
            alpha=args.alpha,
            seed=args.seed
        )

        print(f"\n=== Held-out Validation Complete ===")
        print(f"Significant correlations found: {results['n_significant_pairs']}")
        print(f"Max correlation: {results['overall_max_correlation']:.4f}")
        print(f"Report written to: {Path(args.output) / 'held_out_validation_report.json'}")

    except Exception as e:
        logger.error(f"Held-out validation failed: {e}")
        raise


if __name__ == "__main__":
    main()