"""
Leave-one-experiment-out cross-validation and bootstrap resampling for robustness analysis.

This module implements:
1. True leave-one-out (LOO) if >= 3 independent runs and USE_BOOTSTRAP is false.
2. Bootstrap resampling if < 3 runs or USE_BOOTSTRAP is true.

Outputs:
- data/results/cross_val_alpha_limits.json: List of 95th percentile alpha upper limits.
- data/results/cross_val_summary.json: Aggregated statistics (mean, std, CV).
"""
import os
import sys
import json
import logging
import numpy as np
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple

# Project root handling
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from config import get_logger, ProjectConfig
from data.state_manager import check_bootstrap_flag, read_state
from data.fallback_logic import bootstrap_resample_dataset
from data.loaders import HarmonizedDataset
from models.likelihood import YukawaLikelihood, load_covariance_matrix
from inference.mcmc import run_mcmc
from utils.directories import ensure_data_directories

logger = get_logger(__name__)

def load_harmonized_data() -> HarmonizedDataset:
    """Load the harmonized dataset and covariance matrix."""
    config = ProjectConfig()
    data_path = config.processed_data_dir / "harmonized_data.csv"
    cov_path = config.processed_data_dir / "covariance_matrix.npy"

    if not data_path.exists():
        raise FileNotFoundError(f"Harmonized data not found at {data_path}")
    if not cov_path.exists():
        raise FileNotFoundError(f"Covariance matrix not found at {cov_path}")

    # Load dataset
    df = HarmonizedDataset.load_from_csv(data_path)
    cov_matrix = np.load(cov_path)

    return HarmonizedDataset(
        separation_m=df['separation_m'].values,
        force_n=df['force_n'].values,
        uncertainty=df['uncertainty'].values,
        covariance_matrix=cov_matrix,
        run_ids=df.get('run_id', None).values if 'run_id' in df.columns else None
    )

def run_single_inference(
    separation: np.ndarray,
    force: np.ndarray,
    covariance: np.ndarray,
    n_steps: int = 1000,
    n_walkers: int = 32
) -> float:
    """
    Run a simplified MCMC inference on a specific dataset subset.
    Returns the 95th percentile upper limit for alpha.
    """
    # Create a temporary likelihood object
    # We assume the covariance matrix is already constructed correctly for the subset
    likelihood_func = YukawaLikelihood(separation, force, covariance)

    # Run MCMC
    # Note: We use a reduced step count for robustness iterations to save time,
    # but ensure convergence is checked or a minimum is reached.
    samples, info = run_mcmc(
        likelihood_func,
        n_steps=n_steps,
        n_walkers=n_walkers,
        n_burnin=int(n_steps * 0.2),
        verbose=False
    )

    if samples is None or len(samples) == 0:
        logger.warning("MCMC failed to produce samples for this iteration.")
        return np.nan

    # Extract alpha samples (assuming alpha is the first parameter)
    alpha_samples = samples[:, 0]
    upper_limit = np.percentile(alpha_samples, 95)
    return upper_limit

def perform_leave_one_out(
    dataset: HarmonizedDataset,
    n_iterations: int = 3
) -> List[float]:
    """
    Perform true leave-one-experiment-out cross-validation.
    Assumes dataset has 'run_ids' and >= 3 unique runs.
    """
    if dataset.run_ids is None:
        raise ValueError("Dataset must have 'run_ids' for leave-one-out.")

    unique_runs = np.unique(dataset.run_ids)
    if len(unique_runs) < 3:
        raise ValueError(f"Need at least 3 runs for LOO, found {len(unique_runs)}.")

    alpha_limits = []
    logger.info(f"Starting Leave-One-Out with {len(unique_runs)} runs.")

    for i, run_to_exclude in enumerate(unique_runs):
        logger.info(f"Iteration {i+1}/{len(unique_runs)}: Excluding run {run_to_exclude}")

        # Filter data
        mask = dataset.run_ids != run_to_exclude
        sep_subset = dataset.separation_m[mask]
        force_subset = dataset.force_n[mask]

        # Re-calculate covariance for the subset
        # This is expensive but necessary for correctness.
        # We assume the full covariance matrix is block-diagonal or full.
        # We need to extract the sub-matrix corresponding to the kept indices.
        keep_indices = np.where(mask)[0]
        cov_subset = dataset.covariance_matrix[np.ix_(keep_indices, keep_indices)]

        # Run inference
        try:
            limit = run_single_inference(sep_subset, force_subset, cov_subset)
            alpha_limits.append(limit)
        except Exception as e:
            logger.error(f"Inference failed for LOO iteration {i+1}: {e}")
            alpha_limits.append(np.nan)

    return alpha_limits

def perform_bootstrap_resampling(
    dataset: HarmonizedDataset,
    n_iterations: int = 20
) -> List[float]:
    """
    Perform bootstrap resampling if LOO is not possible.
    Resamples rows with replacement and re-infers.
    """
    logger.info(f"Starting Bootstrap Resampling with {n_iterations} iterations.")
    alpha_limits = []

    n_points = len(dataset.separation_m)
    if n_points == 0:
        raise ValueError("Dataset is empty.")

    for i in range(n_iterations):
        logger.info(f"Bootstrap Iteration {i+1}/{n_iterations}")

        # Resample indices with replacement
        indices = np.random.choice(n_points, size=n_points, replace=True)

        sep_subset = dataset.separation_m[indices]
        force_subset = dataset.force_n[indices]

        # Re-calculate covariance for the resampled indices
        # Note: If the original covariance was block-diagonal based on runs,
        # simple row resampling might break the block structure.
        # However, per the task spec: "re-calculate mean and covariance for the sample".
        # We will extract the sub-matrix from the original full covariance if possible,
        # or re-estimate if the original was too large.
        # For this implementation, we assume the original covariance matrix is dense enough
        # or block-diagonal such that we can extract the sub-matrix.
        # If the original covariance was block-diagonal with bandwidth, we might need to
        # reconstruct the covariance for the new indices.
        # Given the constraints, we will try to extract the sub-matrix first.
        # If the original covariance is full N x N, this is straightforward.
        # If it was block-diagonal, the indices might not align perfectly with blocks.
        # The task says: "extract the corresponding block-diagonal covariance sub-matrix".
        # This implies the original matrix structure is preserved.

        try:
            cov_subset = dataset.covariance_matrix[np.ix_(indices, indices)]
        except Exception:
            logger.warning("Could not extract sub-matrix, re-estimating covariance.")
            # Fallback: estimate covariance from the resampled data
            # This is a simplification; a robust implementation would re-run the harmonization logic.
            # For now, we assume the covariance matrix is dense or the indices are valid.
            cov_subset = np.eye(n_points) * np.var(force_subset) # Placeholder fallback

        try:
            limit = run_single_inference(sep_subset, force_subset, cov_subset)
            alpha_limits.append(limit)
        except Exception as e:
            logger.error(f"Inference failed for Bootstrap iteration {i+1}: {e}")
            alpha_limits.append(np.nan)

    return alpha_limits

def calculate_cv(limits: List[float]) -> Tuple[float, float]:
    """Calculate mean and Coefficient of Variation (CV) of the limits."""
    valid_limits = [l for l in limits if not np.isnan(l)]
    if len(valid_limits) == 0:
        return np.nan, np.nan

    mean_limit = np.mean(valid_limits)
    std_limit = np.std(valid_limits)
    cv = (std_limit / mean_limit) * 100 if mean_limit != 0 else np.nan
    return mean_limit, cv

def main():
    """Main entry point for T030."""
    ensure_data_directories()
    config = ProjectConfig()

    # Check state for bootstrap flag
    state = read_state()
    use_bootstrap = state.get("USE_BOOTSTRAP", False)
    runs_count = state.get("runs_count", 0)

    logger.info(f"State: USE_BOOTSTRAP={use_bootstrap}, runs_count={runs_count}")

    # Load data
    try:
        dataset = load_harmonized_data()
    except FileNotFoundError as e:
        logger.error(f"Data loading failed: {e}")
        return

    alpha_limits = []

    # Decision Logic
    if not use_bootstrap and runs_count >= 3:
        logger.info("Condition met for Leave-One-Out Cross-Validation.")
        alpha_limits = perform_leave_one_out(dataset, n_iterations=runs_count)
    else:
        logger.info("Condition met for Bootstrap Resampling.")
        alpha_limits = perform_bootstrap_resampling(dataset, n_iterations=20)

    # Calculate CV
    mean_limit, cv = calculate_cv(alpha_limits)

    # Prepare output
    results_dir = config.results_dir
    results_dir.mkdir(parents=True, exist_ok=True)

    # Save detailed limits
    limits_path = results_dir / "cross_val_alpha_limits.json"
    with open(limits_path, 'w') as f:
        json.dump({
            "method": "LOO" if (not use_bootstrap and runs_count >= 3) else "Bootstrap",
            "limits": alpha_limits,
            "count": len(alpha_limits)
        }, f, indent=2)

    # Save summary
    summary_path = results_dir / "cross_val_summary.json"
    with open(summary_path, 'w') as f:
        json.dump({
            "mean_95_limit": float(mean_limit) if not np.isnan(mean_limit) else None,
            "cv_percent": float(cv) if not np.isnan(cv) else None,
            "method": "LOO" if (not use_bootstrap and runs_count >= 3) else "Bootstrap",
            "iterations": len(alpha_limits),
            "warning": "CV > 15%" if (not np.isnan(cv) and cv > 15) else "CV <= 15% or insufficient data"
        }, f, indent=2)

    # Log warning if CV > 15%
    if not np.isnan(cv) and cv > 15:
        logger.warning(f"CV of credible-upper-limits is {cv:.2f}%, which is > 15%. Stability is low.")
    else:
        logger.info(f"CV of credible-upper-limits is {cv:.2f}% (if applicable).")

    logger.info(f"Cross-validation complete. Results saved to {results_dir}")

if __name__ == "__main__":
    main()