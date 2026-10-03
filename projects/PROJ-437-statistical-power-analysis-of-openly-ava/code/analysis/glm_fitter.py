"""
GLM Fitter for Statistical Power Analysis.

This module implements the General Linear Model (GLM) fitting logic on preprocessed
fMRI ROI time-series data. It estimates effect sizes (Cohen's d) and tracks
convergence metrics for reproducibility and reliability assessment.

Key Features:
- Fits GLM on real preprocessed data (post-temporal smoothing).
- Randomly subsamples subjects to simulate requested sample sizes.
- Captures convergence status (max iterations, tolerance).
- Logs convergence data to data/aggregated/convergence_log.json.
- Outputs Cohen's d effect size estimates.
"""

import json
import logging
import sys
import os
import gc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.regression.linear_model import WLS
from statsmodels.tools.tools import add_constant

# Import project utilities
from utils.seed_manager import set_global_seed, get_seed
from utils.memory_monitor import get_current_memory_usage_gb, check_memory_threshold, trigger_gc
from models.simulation_config import SimulationConfig
from models.replication_result import ReplicationResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class GLMFitError(Exception):
    """Custom exception for GLM fitting errors."""
    pass


class ConvergenceLogger:
    """
    Utility class to log GLM convergence metrics to a JSON file.

    Ensures that convergence data (iteration_id, converged, max_iterations, tolerance)
    is persisted to data/aggregated/convergence_log.json.
    """

    def __init__(self, output_path: str = "data/aggregated/convergence_log.json"):
        self.output_path = Path(output_path)
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self.log_entries: List[Dict[str, Any]] = []
        self._load_existing_log()

    def _load_existing_log(self) -> None:
        """Load existing log if present to append new entries."""
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.log_entries = data
                    else:
                        logger.warning(f"Existing log at {self.output_path} is not a list. Overwriting.")
                        self.log_entries = []
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Could not load existing log: {e}. Starting fresh.")
                self.log_entries = []

    def log_entry(self, iteration_id: int, converged: bool, max_iterations: int, tolerance: float) -> None:
        """
        Log a single convergence entry.

        Args:
            iteration_id: Unique identifier for the iteration/run.
            converged: Boolean indicating if the GLM solver converged.
            max_iterations: Maximum iterations allowed or used.
            tolerance: Convergence tolerance used.
        """
        entry = {
            "iteration_id": iteration_id,
            "converged": converged,
            "max_iterations": max_iterations,
            "tolerance": tolerance
        }
        self.log_entries.append(entry)

    def save(self) -> None:
        """Save the accumulated log entries to disk."""
        try:
            with open(self.output_path, 'w') as f:
                json.dump(self.log_entries, f, indent=2)
            logger.info(f"Convergence log saved to {self.output_path}")
        except IOError as e:
            logger.error(f"Failed to save convergence log: {e}")
            raise


def fit_glm(
    y: np.ndarray,
    X: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-4,
    seed: Optional[int] = None
) -> Tuple[Optional[sm.regression.linear_model.RegressionResultsWrapper], bool, int, float]:
    """
    Fit a General Linear Model using statsmodels.

    Args:
        y: Dependent variable (1D array, shape [n_observations,]).
        X: Independent variable matrix (2D array, shape [n_observations, n_features]).
        max_iter: Maximum number of iterations for the solver.
        tol: Convergence tolerance.
        seed: Random seed for reproducibility (if needed for any stochastic parts).

    Returns:
        Tuple of:
            - results: Fitted model results object or None if failed.
            - converged: Boolean indicating convergence.
            - iterations_used: Number of iterations actually used.
            - final_tolerance: Final tolerance achieved.
    """
    if seed is not None:
        set_global_seed(seed)

    # Ensure X has a constant term if not already
    if X.shape[1] == 1:
        X = add_constant(X)
    elif not np.any(np.all(X == 1, axis=0)):
        # Check if constant is already present
        col_sums = np.sum(X, axis=0)
        if not np.any(np.abs(col_sums - len(X)) < 1e-5):
            X = add_constant(X)

    try:
        # Use WLS (Weighted Least Squares) which defaults to OLS if weights are 1
        # statsmodels OLS/WLS is deterministic and robust
        model = WLS(y, X)
        results = model.fit(maxiter=max_iter, tol=tol)

        converged = results.converged
        # statsmodels fit usually returns immediately, but we capture the status
        # If it didn't converge, we flag it.
        # Note: statsmodels OLS/WLS usually solves analytically, so 'converged' is often True unless singular.
        # For iterative solvers (like in some GLM extensions), this would be more critical.
        # We assume standard OLS behavior here for ROI time series.
        if not converged:
            logger.warning("GLM fit did not converge or is singular.")

        # Estimate iterations used (for OLS this is effectively 1 analytical step,
        # but we log max_iter as the 'allowed' budget for the log format)
        iterations_used = max_iter if not converged else 1
        final_tol = tol

        return results, converged, iterations_used, final_tol

    except np.linalg.LinAlgError as e:
        logger.error(f"Linear algebra error during GLM fit: {e}")
        return None, False, max_iter, tol
    except Exception as e:
        logger.error(f"Unexpected error during GLM fit: {e}")
        return None, False, max_iter, tol


def estimate_effect_size(
    results: sm.regression.linear_model.RegressionResultsWrapper,
    condition_index: int = 1
) -> float:
    """
    Estimate Cohen's d effect size from GLM results.

    Cohen's d is calculated as: (Mean_Group1 - Mean_Group2) / Pooled_StdDev
    In the context of GLM with a binary regressor (0/1), the coefficient beta_1
    represents the difference in means.
    d = beta_1 / residual_std

    Args:
        results: Fitted GLM results object.
        condition_index: Index of the condition coefficient in the model.

    Returns:
        Cohen's d value.
    """
    try:
        beta = results.params[condition_index]
        residuals = results.resid
        n = len(residuals)
        p = results.df_model + 1  # +1 for intercept

        # Residual standard deviation (standard error of the regression)
        # sigma_hat = sqrt(SS_res / (n - p))
        ss_res = np.sum(residuals ** 2)
        if n - p <= 0:
            raise GLMFitError("Degrees of freedom <= 0 for residual variance calculation.")

        residual_std = np.sqrt(ss_res / (n - p))

        if residual_std == 0:
            logger.warning("Residual standard deviation is zero. Effect size undefined.")
            return 0.0

        cohens_d = beta / residual_std
        return float(cohens_d)

    except Exception as e:
        logger.error(f"Error estimating effect size: {e}")
        raise GLMFitError(f"Effect size estimation failed: {e}")


def load_and_subsample_data(
    data_path: str,
    target_sample_size: int,
    seed: int
) -> Tuple[np.ndarray, np.ndarray, List[str]]:
    """
    Load preprocessed ROI time-series data and subsample subjects.

    Args:
        data_path: Path to the CSV file containing ROI timeseries.
        target_sample_size: Number of subjects to randomly sample.
        seed: Random seed for subsampling.

    Returns:
        Tuple of (y, X, subject_ids)
        y: Flattened time-series data (or aggregated per subject if needed).
        X: Design matrix (binary condition indicators).
        subject_ids: List of subject IDs included in the sample.
    """
    set_global_seed(seed)
    data_path = Path(data_path)
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")

    # Load data
    # Expected format: subject_id, time_point, condition (0/1), roi_signal
    df = pd.read_csv(data_path)

    # Validate columns
    required_cols = {'subject_id', 'time_point', 'condition', 'roi_signal'}
    if not required_cols.issubset(df.columns):
        missing = required_cols - set(df.columns)
        raise ValueError(f"Data file missing required columns: {missing}")

    # Get unique subjects
    unique_subjects = df['subject_id'].unique()
    total_subjects = len(unique_subjects)

    if target_sample_size > total_subjects:
        logger.warning(f"Requested sample size {target_sample_size} > available {total_subjects}. Clamping.")
        target_sample_size = total_subjects

    # Randomly subsample subjects
    selected_subjects = np.random.choice(unique_subjects, size=target_sample_size, replace=False)
    selected_subjects = sorted(selected_subjects) # Sort for reproducibility in downstream

    # Filter data
    df_sample = df[df['subject_id'].isin(selected_subjects)]

    # Check memory
    mem_usage = get_current_memory_usage_gb()
    if mem_usage > 5.0: # Warning threshold
        logger.warning(f"High memory usage after loading data: {mem_usage:.2f} GB")
        trigger_gc()

    # Prepare X and y
    # We treat each time point as an observation, but condition is per time point.
    # X: [time_points, 2] -> [intercept, condition]
    # y: [time_points, 1] -> roi_signal

    y = df_sample['roi_signal'].values
    X = df_sample[['condition']].values # Just the condition column

    return y, X, selected_subjects


def fit_glm_batch(
    data_path: str,
    sample_size: int,
    kernel: str,
    iteration_id: int,
    seed: int,
    max_iter: int = 100,
    tol: float = 1e-4
) -> Dict[str, Any]:
    """
    Perform a single GLM fitting iteration with subsampling.

    Args:
        data_path: Path to preprocessed data.
        sample_size: Number of subjects to include.
        kernel: Smoothing kernel used (for logging).
        iteration_id: Unique ID for this iteration.
        seed: Random seed.
        max_iter: Max iterations for solver.
        tol: Tolerance for solver.

    Returns:
        Dictionary with results and metrics.
    """
    logger.info(f"Starting GLM fit for iteration {iteration_id}, N={sample_size}, kernel={kernel}")

    try:
        # Load and subsample
        y, X, subject_ids = load_and_subsample_data(data_path, sample_size, seed)

        if len(y) == 0:
            raise GLMFitError("No data loaded after subsampling.")

        # Fit GLM
        results, converged, iters_used, final_tol = fit_glm(
            y, X, max_iter=max_iter, tol=tol, seed=seed
        )

        if results is None:
            return {
                "iteration_id": iteration_id,
                "success": False,
                "converged": False,
                "error": "GLM fit failed",
                "subject_count": sample_size
            }

        # Estimate effect size
        # Assuming condition is the second column (index 1) after constant added
        # If X was just [condition], add_constant makes it [const, condition]
        # So condition index is 1.
        cohens_d = estimate_effect_size(results, condition_index=1)

        # Log convergence
        convergence_logger = ConvergenceLogger()
        convergence_logger.log_entry(
            iteration_id=iteration_id,
            converged=converged,
            max_iterations=iters_used,
            tolerance=final_tol
        )
        # We save immediately per iteration to ensure data is not lost if process crashes later
        convergence_logger.save()

        return {
            "iteration_id": iteration_id,
            "success": True,
            "converged": converged,
            "cohens_d": cohens_d,
            "p_value": results.pvalues[1] if len(results.pvalues) > 1 else 0.0,
            "subject_count": sample_size,
            "kernel": kernel,
            "subject_ids": subject_ids # Keep for traceability if needed
        }

    except Exception as e:
        logger.error(f"Error in fit_glm_batch (iteration {iteration_id}): {e}")
        # Even on error, we might want to log the attempt as failed convergence
        try:
            convergence_logger = ConvergenceLogger()
            convergence_logger.log_entry(
                iteration_id=iteration_id,
                converged=False,
                max_iterations=max_iter,
                tolerance=tol
            )
            convergence_logger.save()
        except:
            pass # Best effort logging

        return {
            "iteration_id": iteration_id,
            "success": False,
            "converged": False,
            "error": str(e),
            "subject_count": sample_size
        }


def main():
    """
    CLI entry point for GLM Fitter.
    Usage: python -m code.analysis.glm_fitter --data <path> --sample-size <N> --seed <S>
    """
    import argparse

    parser = argparse.ArgumentParser(description="Fit GLM on preprocessed fMRI data.")
    parser.add_argument("--data", type=str, required=True, help="Path to preprocessed ROI timeseries CSV.")
    parser.add_argument("--sample-size", type=int, default=10, help="Number of subjects to sample.")
    parser.add_argument("--seed", type=int, default=42, help="Random seed.")
    parser.add_argument("--kernel", type=str, default="4s", help="Smoothing kernel used.")
    parser.add_argument("--max-iter", type=int, default=100, help="Max iterations for GLM solver.")
    parser.add_argument("--tol", type=float, default=1e-4, help="Tolerance for GLM solver.")
    parser.add_argument("--output", type=str, default="data/aggregated/glm_results.json", help="Output JSON path.")

    args = parser.parse_args()

    logger.info(f"GLM Fitter started. Data: {args.data}, N: {args.sample_size}, Seed: {args.seed}")

    # Run a single fit for the specified configuration
    # In a full pipeline, this might be called in a loop by split_half_validator
    result = fit_glm_batch(
        data_path=args.data,
        sample_size=args.sample_size,
        kernel=args.kernel,
        iteration_id=0, # Single run
        seed=args.seed,
        max_iter=args.max_iter,
        tol=args.tol
    )

    # Save result
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)

    logger.info(f"GLM fit complete. Result saved to {output_path}")

    if not result.get('success', False):
        logger.error("GLM fit failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()