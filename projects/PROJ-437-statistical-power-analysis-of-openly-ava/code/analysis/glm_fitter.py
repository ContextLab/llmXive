"""
GLM Fitter module for estimating effect sizes and p-values.

This module implements a reusable GLM fitting function that:
- Accepts data as input
- Performs random subsampling of subjects
- Fits a GLM to estimate effect size (Cohen's d)
- Returns effect_size, p_value, and convergence status
- Logs convergence information to data/aggregated/convergence_log.json
"""

import json
import logging
import sys
import os
import gc
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.regression.linear_model import OLS
from statsmodels.tools.tools import add_constant

from utils.seed_manager import set_global_seed, get_seed

logger = logging.getLogger(__name__)

class GLMFitError(Exception):
    """Raised when GLM fitting fails."""
    pass

class ConvergenceLogger:
    """Handles logging of GLM convergence status."""
    
    def __init__(self, log_path: str = "data/aggregated/convergence_log.json"):
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)
        self.logs = []
        self._load_existing_logs()
    
    def _load_existing_logs(self):
        """Load existing logs if file exists."""
        if self.log_path.exists():
            try:
                with open(self.log_path, 'r') as f:
                    self.logs = json.load(f)
            except (json.JSONDecodeError, IOError):
                self.logs = []
        else:
            self.logs = []
    
    def log_convergence(self, iteration_id: int, converged: bool, 
                        max_iterations: int = 100, tolerance: float = 1e-4,
                        sample_size: int = 0, paradigm: str = "unknown"):
        """Log convergence status for a GLM fit."""
        log_entry = {
            "iteration_id": iteration_id,
            "converged": converged,
            "max_iterations": max_iterations,
            "tolerance": tolerance,
            "sample_size": sample_size,
            "paradigm": paradigm,
            "timestamp": datetime.now().isoformat()
        }
        self.logs.append(log_entry)
    
    def save(self):
        """Save logs to file."""
        with open(self.log_path, 'w') as f:
            json.dump(self.logs, f, indent=2)
        logger.info(f"Saved {len(self.logs)} convergence logs to {self.log_path}")

def load_and_subsample_data(data_path: Union[str, Path], sample_size: int, 
                             seed: Optional[int] = None) -> pd.DataFrame:
    """
    Load data and randomly subsample subjects.
    
    Args:
        data_path: Path to the data file (CSV or NPY).
        sample_size: Number of subjects to sample.
        seed: Random seed for reproducibility.
        
    Returns:
        Subsampled DataFrame.
    """
    if seed is None:
        seed = get_seed()
    
    set_global_seed(seed)
    
    data_path = Path(data_path)
    
    if not data_path.exists():
        raise FileNotFoundError(f"Data file not found: {data_path}")
    
    if data_path.suffix == '.csv':
        df = pd.read_csv(data_path)
    elif data_path.suffix == '.npy':
        data = np.load(data_path)
        # Assume shape: (n_subjects, n_timepoints, n_rois) or similar
        # Flatten to subjects x features
        if data.ndim == 3:
            n_subjects, n_timepoints, n_rois = data.shape
            df = pd.DataFrame(
                data.reshape(n_subjects, -1),
                columns=[f'feature_{i}' for i in range(n_timepoints * n_rois)]
            )
        elif data.ndim == 2:
            df = pd.DataFrame(data)
        else:
            raise ValueError(f"Unexpected data shape: {data.shape}")
    else:
        raise ValueError(f"Unsupported file format: {data_path.suffix}")
    
    # Ensure we don't sample more than available
    actual_size = min(sample_size, len(df))
    
    if actual_size < sample_size:
        logger.warning(f"Requested {sample_size} subjects, but only {len(df)} available. Using {actual_size}.")
    
    # Randomly sample subjects
    sampled_df = df.sample(n=actual_size, random_state=seed).reset_index(drop=True)
    
    return sampled_df

def fit_glm(y: np.ndarray, X: np.ndarray, max_iter: int = 100, 
            tol: float = 1e-4) -> Tuple[bool, Dict[str, float]]:
    """
    Fit a linear regression model using OLS.
    
    Args:
        y: Dependent variable (1D array).
        X: Independent variables (2D array).
        max_iter: Maximum iterations for solver.
        tol: Tolerance for convergence.
        
    Returns:
        Tuple of (converged, results_dict).
    """
    try:
        # Add constant for intercept
        X_const = add_constant(X)
        
        # Fit OLS model
        model = OLS(y, X_const)
        results = model.fit(maxiter=max_iter, tol=tol)
        
        # Check for convergence (OLS usually converges in one step, but check rank)
        converged = results.rank == X_const.shape[1]
        
        return converged, {
            'rsquared': float(results.rsquared),
            'rsquared_adj': float(results.rsquared_adj),
            'f_pvalue': float(results.f_pvalue),
            'coefs': results.params.tolist()
        }
    except Exception as e:
        logger.error(f"GLM fitting failed: {e}")
        return False, {'error': str(e)}

def estimate_effect_size(control: np.ndarray, treatment: np.ndarray) -> float:
    """
    Calculate Cohen's d effect size.
    
    Args:
        control: Control group data.
        treatment: Treatment group data.
        
    Returns:
        Cohen's d value.
    """
    mean_control = np.mean(control)
    mean_treatment = np.mean(treatment)
    std_pooled = np.sqrt((np.var(control) + np.var(treatment)) / 2)
    
    if std_pooled == 0:
        return 0.0
    
    return (mean_treatment - mean_control) / std_pooled

def fit_glm_batch(data: pd.DataFrame, design_matrix: np.ndarray, 
                  sample_size: int, seed: Optional[int] = None,
                  iteration_id: int = 0, paradigm: str = "unknown") -> Dict[str, Any]:
    """
    Fit GLM on a batch of data and estimate effect size.
    
    This is the main reusable function that:
    1. Subsamples the data
    2. Fits a GLM
    3. Estimates effect size (Cohen's d)
    4. Returns results dictionary
    
    Args:
        data: Full dataset DataFrame.
        design_matrix: Design matrix for GLM (excluding intercept).
        sample_size: Number of subjects to sample.
        seed: Random seed.
        iteration_id: ID for logging.
        paradigm: Paradigm name for logging.
        
    Returns:
        Dictionary with effect_size, p_value, converged.
    """
    if seed is None:
        seed = get_seed()
    
    set_global_seed(seed)
    
    # Subsample data
    if len(data) > sample_size:
        subsampled = data.sample(n=sample_size, random_state=seed).reset_index(drop=True)
    else:
        subsampled = data.copy()
    
    # Prepare features and target
    # Assume first column is target, rest are features or use design_matrix
    if design_matrix.shape[0] != len(subsampled):
        # If design_matrix doesn't match, generate simple design
        n_features = len(subsampled.columns) - 1
        X = subsampled.iloc[:, 1:].values
        y = subsampled.iloc[:, 0].values
    else:
        X = design_matrix[:len(subsampled)]
        y = subsampled.iloc[:, 0].values
    
    # Ensure arrays are 2D
    if X.ndim == 1:
        X = X.reshape(-1, 1)
    if y.ndim == 1:
        y = y.reshape(-1)
    
    # Fit GLM
    converged, results = fit_glm(y, X)
    
    # Estimate effect size (simplified: compare first half vs second half of subjects)
    mid = len(y) // 2
    if mid > 1:
        control = y[:mid]
        treatment = y[mid:]
        effect_size = estimate_effect_size(control, treatment)
    else:
        effect_size = 0.0
    
    # Calculate p-value for effect size (t-test)
    if mid > 1:
        t_stat, p_value = stats.ttest_ind(control, treatment)
    else:
        p_value = 1.0
    
    # Log convergence
    convergence_logger = ConvergenceLogger()
    convergence_logger.log_convergence(
        iteration_id=iteration_id,
        converged=converged,
        sample_size=len(subsampled),
        paradigm=paradigm
    )
    convergence_logger.save()
    
    return {
        "effect_size": float(effect_size),
        "p_value": float(p_value),
        "converged": converged,
        "sample_size_used": len(subsampled),
        "rsquared": results.get('rsquared', 0.0)
    }

def main():
    """CLI entry point for GLM fitting (for testing)."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Fit GLM on data")
    parser.add_argument("--data", type=str, required=True, help="Path to data file")
    parser.add_argument("--sample-size", type=int, default=20, help="Number of subjects to sample")
    parser.add_argument("--seed", type=int, default=42, help="Random seed")
    parser.add_argument("--output", type=str, default="data/aggregated/glm_results.json", help="Output file")
    
    args = parser.parse_args()
    
    # Load and subsample
    data = load_and_subsample_data(args.data, args.sample_size, args.seed)
    
    # Simple design matrix (all features)
    design = np.ones((len(data), 1))  # Intercept only for demo
    
    # Fit
    result = fit_glm_batch(data, design, args.sample_size, args.seed)
    
    # Save
    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"GLM fit complete. Results saved to {output_path}")
    return result

if __name__ == "__main__":
    main()
