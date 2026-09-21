"""
GLM Fitter for fMRI Power Analysis.

Fits a General Linear Model (GLM) on real preprocessed ROI time-series data
and estimates effect sizes (Cohen's d) for task-related activation.
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

import numpy as np
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import OLSInfluence

# Import from existing project modules
from models.simulation_config import SimulationConfig
from utils.seed_manager import set_global_seed
from utils.memory_monitor import check_memory_threshold, trigger_gc
from simulation.noise_estimator import estimate_residual_variance

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)


class GLMFitError(Exception):
    """Raised when GLM fitting fails due to convergence issues or singular matrices."""
    pass


def _create_design_matrix(
    task_onsets: np.ndarray,
    tr: float,
    duration: float,
    hrf_model: str = "glover"
) -> np.ndarray:
    """
    Create a simple design matrix with task regressor and constant.

    Args:
        task_onsets: Array of task onset times in seconds.
        tr: Repetition time in seconds.
        duration: Total scan duration in seconds.
        hrf_model: HRF model type (placeholder for future convolution).

    Returns:
        Design matrix (N_timepoints x 2) with task regressor and constant.
    """
    n_timepoints = int(np.ceil(duration / tr))
    time_vector = np.arange(n_timepoints) * tr

    # Create block design (simplified boxcar)
    task_reg = np.zeros(n_timepoints)
    for onset in task_onsets:
        # Assume task duration is 20s or until next onset/scan end
        end = min(onset + 20, duration)
        mask = (time_vector >= onset) & (time_vector < end)
        task_reg[mask] = 1.0

    # Normalize task regressor
    if np.std(task_reg) > 0:
        task_reg = task_reg / np.std(task_reg)

    # Add constant term
    design = np.column_stack([task_reg, np.ones(n_timepoints)])

    return design


def fit_glm(
    y: np.ndarray,
    design_matrix: np.ndarray,
    noise_cov: Optional[np.ndarray] = None
) -> Tuple[Dict[str, Any], Dict[str, float]]:
    """
    Fit OLS GLM and return results.

    Args:
        y: Dependent variable (ROI time-series, 1D).
        design_matrix: Independent variables (N x K).
        noise_cov: Optional noise covariance matrix (for FGLS, not implemented yet).

    Returns:
        Tuple of (model_results, effect_size_dict).
        effect_size_dict contains 'cohen_d' for the task regressor.
    """
    if len(y) != design_matrix.shape[0]:
        raise ValueError(f"Length of y ({len(y)}) does not match design matrix rows ({design_matrix.shape[0]})")

    if np.any(np.isnan(y)) or np.any(np.isnan(design_matrix)):
        raise ValueError("Input data contains NaN values. Preprocess data before fitting.")

    try:
        model = sm.OLS(y, design_matrix)
        results = model.fit()
    except np.linalg.LinAlgError as e:
        raise GLMFitError(f"GLM fitting failed due to singular matrix: {e}")
    except Exception as e:
        raise GLMFitError(f"GLM fitting failed: {e}")

    # Extract task regressor coefficient (first column is task, second is constant)
    # Assuming design matrix is [task_reg, constant]
    task_idx = 0
    beta_task = results.params[task_idx]
    se_task = results.bse[task_idx]

    # Calculate Cohen's d: beta / sigma_residual
    sigma_residual = np.sqrt(results.mse_resid)
    if sigma_residual == 0:
        sigma_residual = 1e-10  # Prevent division by zero

    cohen_d = beta_task / sigma_residual

    effect_size_dict = {
        "cohen_d": float(cohen_d),
        "beta_task": float(beta_task),
        "se_task": float(se_task),
        "t_stat": float(results.tvalues[task_idx]),
        "p_value": float(results.pvalues[task_idx]),
        "r_squared": float(results.rsquared),
        "adj_r_squared": float(results.rsquared_adj),
        "n_observations": int(results.nobs),
        "residual_std": float(sigma_residual)
    }

    return results.to_dict(), effect_size_dict


def estimate_effect_size(
    roi_timeseries: np.ndarray,
    task_onsets: np.ndarray,
    tr: float,
    duration: float,
    config: Optional[SimulationConfig] = None
) -> Dict[str, float]:
    """
    Main entry point to fit GLM and estimate effect size for a single ROI.

    Args:
        roi_timeseries: 1D array of preprocessed ROI time-series.
        task_onsets: Array of task onset times in seconds.
        tr: Repetition time in seconds.
        duration: Total scan duration in seconds.
        config: Optional SimulationConfig for seed setting.

    Returns:
        Dictionary containing effect size metrics (Cohen's d, beta, p-value, etc.).
    """
    if config is not None:
        set_global_seed(config.random_seed)

    # Memory check
    check_memory_threshold(roi_timeseries, threshold_gb=4.0)

    # Create design matrix
    design_matrix = _create_design_matrix(task_onsets, tr, duration)

    # Fit GLM
    try:
        _, effect_sizes = fit_glm(roi_timeseries, design_matrix)
    except GLMFitError as e:
        logger.error(f"GLM fit failed: {e}")
        raise

    # Check memory after fitting
    trigger_gc()

    return effect_sizes


def fit_glm_batch(
    roi_data: Dict[str, np.ndarray],
    task_onsets: np.ndarray,
    tr: float,
    duration: float,
    config: Optional[SimulationConfig] = None
) -> Dict[str, Dict[str, float]]:
    """
    Fit GLM for multiple ROIs.

    Args:
        roi_data: Dictionary mapping ROI names to 1D time-series arrays.
        task_onsets: Array of task onset times.
        tr: Repetition time.
        duration: Scan duration.
        config: Optional config for seed setting.

    Returns:
        Dictionary mapping ROI names to effect size dictionaries.
    """
    results = {}
    for roi_name, timeseries in roi_data.items():
        try:
            results[roi_name] = estimate_effect_size(
                roi_timeseries=timeseries,
                task_onsets=task_onsets,
                tr=tr,
                duration=duration,
                config=config
            )
        except Exception as e:
            logger.warning(f"Failed to fit GLM for ROI {roi_name}: {e}")
            results[roi_name] = {
                "cohen_d": np.nan,
                "beta_task": np.nan,
                "se_task": np.nan,
                "t_stat": np.nan,
                "p_value": np.nan,
                "r_squared": np.nan,
                "adj_r_squared": np.nan,
                "n_observations": 0,
                "residual_std": np.nan,
                "error": str(e)
            }
    return results


def main():
    """
    CLI entry point for GLM fitting.

    Expects preprocessed ROI data in data/derived/roi_timeseries.npy
    and task information in data/derived/task_info.json.
    """
    import json

    # Default paths
    roi_data_path = Path("data/derived/roi_timeseries.npy")
    task_info_path = Path("data/derived/task_info.json")
    output_path = Path("data/derived/glm_results.json")

    if not roi_data_path.exists():
        logger.error(f"ROI data not found: {roi_data_path}")
        sys.exit(1)

    if not task_info_path.exists():
        logger.error(f"Task info not found: {task_info_path}")
        sys.exit(1)

    # Load data
    logger.info(f"Loading ROI data from {roi_data_path}")
    roi_data = np.load(roi_data_path, allow_pickle=True).item()

    logger.info(f"Loading task info from {task_info_path}")
    with open(task_info_path, "r") as f:
        task_info = json.load(f)

    task_onsets = np.array(task_info["onsets"])
    tr = float(task_info["tr"])
    duration = float(task_info["duration"])

    # Fit GLM
    logger.info("Fitting GLM...")
    results = fit_glm_batch(
        roi_data=roi_data,
        task_onsets=task_onsets,
        tr=tr,
        duration=duration
    )

    # Save results
    logger.info(f"Saving results to {output_path}")
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    logger.info("GLM fitting completed successfully.")
    print(f"Results saved to {output_path}")


if __name__ == "__main__":
    main()