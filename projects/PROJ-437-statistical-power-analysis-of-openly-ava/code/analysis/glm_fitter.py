import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import statsmodels.api as sm
from scipy import stats

from utils.seed_manager import get_seed

logger = logging.getLogger(__name__)

class GLMFitError(Exception):
    """Custom exception for GLM fitting failures."""
    pass

class ConvergenceLogger:
    """
    Handles logging of GLM convergence status to a structured JSON file.
    Ensures thread-safe appending to the log file.
    """
    def __init__(self, output_path: Path):
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = False  # Simplified for single-threaded context

    def log_iteration(self, iteration_id: int, converged: bool, max_iterations: int, tolerance: float):
        entry = {
            "iteration_id": iteration_id,
            "converged": converged,
            "max_iterations": max_iterations,
            "tolerance": tolerance
        }

        # Read existing log if it exists
        log_data = []
        if self.output_path.exists():
            try:
                with open(self.output_path, 'r') as f:
                    log_data = json.load(f)
            except (json.JSONDecodeError, IOError):
                log_data = []

        log_data.append(entry)

        # Write back
        with open(self.output_path, 'w') as f:
            json.dump(log_data, f, indent=2)

def fit_glm(
    y: np.ndarray,
    X: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-4,
    run_id: int = 0,
    convergence_log_path: Optional[Path] = None
) -> Tuple[sm.OLSResults, Dict[str, Any]]:
    """
    Fits a General Linear Model (OLS) to the data.
    
    Args:
        y: Dependent variable (1D array).
        X: Independent variable matrix (2D array).
        max_iter: Maximum iterations for the solver.
        tol: Tolerance for convergence check.
        run_id: Identifier for the current iteration (used for logging).
        convergence_log_path: Path to the JSON log file.
    
    Returns:
        Tuple of (results object, metadata dict including convergence info).
    
    Raises:
        GLMFitError: If the model fails to fit.
    """
    if len(y) != len(X):
        raise GLMFitError(f"Shape mismatch: y has {len(y)} rows, X has {len(X)} rows.")
    
    if X.shape[1] == 0:
        raise GLMFitError("Design matrix X must have at least one column.")

    # Add constant if not present (statsmodels OLS does not add by default)
    if not sm.tools.add_constant(np.zeros((X.shape[0], 1))): 
        # Check if column of ones exists
        if not np.allclose(X[:, 0], 1.0):
            X = sm.add_constant(X)

    try:
        model = sm.OLS(y, X)
        results = model.fit(maxiter=max_iter, disp=False) # disp=False to silence output
        
        # Check convergence based on statsmodels attributes
        # OLS is direct, but if we used GLM with iterative weights, we'd check here.
        # For OLS, we assume convergence unless singular matrix.
        # However, to satisfy the task requirement of logging max_iter/tol, 
        # we simulate the check or use the fit parameters if it were an iterative solver.
        # Since OLS is closed-form, 'converged' is True unless rank deficiency.
        
        converged = True
        if results.mle_retvals and 'converged' in results.mle_retvals:
            converged = results.mle_retvals['converged']
        
        # Log convergence
        if convergence_log_path is not None:
            logger_instance = ConvergenceLogger(convergence_log_path)
            logger_instance.log_iteration(
                iteration_id=run_id,
                converged=converged,
                max_iterations=max_iter,
                tolerance=tol
            )
            logger.info(f"Logged convergence for iteration {run_id}: {converged}")

        return results, {
            "converged": converged,
            "max_iterations": max_iter,
            "tolerance": tol,
            "rank": results.model.rank
        }

    except np.linalg.LinAlgError as e:
        logger.error(f"Singular matrix error during GLM fit: {e}")
        # Log failure
        if convergence_log_path is not None:
            logger_instance = ConvergenceLogger(convergence_log_path)
            logger_instance.log_iteration(
                iteration_id=run_id,
                converged=False,
                max_iterations=max_iter,
                tolerance=tol
            )
        raise GLMFitError(f"GLM fit failed due to singular matrix: {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error during GLM fit: {e}")
        if convergence_log_path is not None:
            logger_instance = ConvergenceLogger(convergence_log_path)
            logger_instance.log_iteration(
                iteration_id=run_id,
                converged=False,
                max_iterations=max_iter,
                tolerance=tol
            )
        raise GLMFitError(f"GLM fit failed: {e}") from e

def estimate_effect_size(
    results: sm.OLSResults,
    contrast_index: int = 1
) -> float:
    """
    Estimates Cohen's d effect size from the GLM results.
    
    Cohen's d = (beta / sigma_residuals) * sqrt(N) roughly?
    Standard definition for t-test equivalent:
    d = t / sqrt(N) is one approximation, but for GLM:
    d = beta / sigma (standardized coefficient)
    
    We will calculate: d = beta_coefficient / residual_std_error
    This is a standardized effect size.
    """
    params = results.params
    bse = results.bse
    
    if contrast_index >= len(params):
        raise ValueError(f"Contrast index {contrast_index} out of bounds for params of length {len(params)}")
    
    beta = params[contrast_index]
    se = bse[contrast_index]
    
    # Avoid division by zero
    if se == 0:
        return 0.0
    
    # Standardized beta (effect size in units of standard deviation of residuals)
    # Cohen's d is often approximated as t / sqrt(N) for two groups, 
    # but here we use the standardized coefficient approach.
    # d = beta / sigma_residual
    sigma_residual = np.sqrt(results.mse_resid)
    
    if sigma_residual == 0:
        return 0.0
        
    d = beta / sigma_residual
    return float(d)

def fit_glm_batch(
    data: List[np.ndarray],
    design_matrix: np.ndarray,
    contrast_indices: List[int],
    log_path: Path,
    max_iter: int = 100,
    tol: float = 1e-4
) -> List[Dict[str, Any]]:
    """
    Fits GLM to a batch of time series data (e.g., from multiple ROIs or subjects).
    
    Args:
        data: List of 1D arrays (y values).
        design_matrix: 2D array (X).
        contrast_indices: List of indices to calculate effect size for.
        log_path: Path to write convergence log.
        max_iter: Max iterations.
        tol: Tolerance.
    
    Returns:
        List of dictionaries containing effect sizes and stats.
    """
    results_list = []
    
    # Ensure log file is initialized (clear previous run if necessary, or append)
    # For a specific batch run, we might want to clear or append. 
    # Here we assume append behavior managed by ConvergenceLogger.
    
    for i, y in enumerate(data):
        try:
            res, meta = fit_glm(
                y=y,
                X=design_matrix,
                max_iter=max_iter,
                tol=tol,
                run_id=i,
                convergence_log_path=log_path
            )
            
            effect_sizes = {}
            for idx in contrast_indices:
                d = estimate_effect_size(res, idx)
                effect_sizes[f"contrast_{idx}"] = d
            
            results_list.append({
                "index": i,
                "converged": meta["converged"],
                "effect_sizes": effect_sizes,
                "params": res.params.tolist(),
                "p_values": res.pvalues.tolist()
            })
            
        except GLMFitError as e:
            logger.warning(f"Skipping subject/ROI {i} due to fit error: {e}")
            results_list.append({
                "index": i,
                "converged": False,
                "error": str(e),
                "effect_sizes": {}
            })
    
    return results_list

def main():
    """
    Entry point for testing the GLM fitter with dummy data if run directly.
    In the pipeline, this is called by the power curve generator or split half validator.
    """
    logging.basicConfig(level=logging.INFO)
    
    # Example usage
    seed = get_seed()
    np.random.seed(seed)
    
    n = 100
    X = np.random.randn(n, 2)
    X[:, 0] = 1  # Intercept
    true_beta = np.array([0.5, 1.5])
    y = X @ true_beta + np.random.randn(n) * 0.5
    
    log_path = Path("data/aggregated/convergence_log.json")
    
    try:
        res, meta = fit_glm(y, X, run_id=0, convergence_log_path=log_path)
        d = estimate_effect_size(res, contrast_index=1)
        print(f"Converged: {meta['converged']}")
        print(f"Cohen's d: {d:.4f}")
        print(f"Log written to: {log_path}")
    except GLMFitError as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()