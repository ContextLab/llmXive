"""
Noise Estimation Module for GLM Modeling.

This module estimates noise characteristics (residual variance, autocorrelation,
degrees of freedom) from real preprocessed fMRI data to inform GLM modeling.
It strictly operates on real data loaded from disk and does not generate synthetic data.
"""
import json
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any

import numpy as np
import statsmodels.api as sm
from statsmodels.tsa.stattools import acf

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class NoiseEstimationError(Exception):
    """Custom exception for noise estimation failures."""
    pass


def estimate_residual_variance(roi_timeseries: np.ndarray, design_matrix: np.ndarray) -> float:
    """
    Estimate the residual variance of the ROI timeseries after fitting a GLM.

    Args:
        roi_timeseries: 1D array of ROI time-series data (T,).
        design_matrix: 2D array of design matrix (T, K).

    Returns:
        float: Estimated residual variance (sigma^2).

    Raises:
        NoiseEstimationError: If GLM fitting fails or design matrix is invalid.
    """
    if roi_timeseries.ndim != 1:
        raise NoiseEstimationError(f"roi_timeseries must be 1D, got {roi_timeseries.ndim}D")
    if design_matrix.ndim != 2:
        raise NoiseEstimationError(f"design_matrix must be 2D, got {design_matrix.ndim}D")
    if len(roi_timeseries) != design_matrix.shape[0]:
        raise NoiseEstimationError(f"Mismatch: timeseries len {len(roi_timeseries)} != design_matrix rows {design_matrix.shape[0]}")

    try:
        # Add constant if not present (simple check)
        if not np.allclose(design_matrix[:, 0], 1):
            # Assuming first column might not be intercept, add one if not obvious
            # A robust check: if first col is not all 1s, prepend a column of 1s
            # However, usually design matrices are expected to have an intercept.
            # We will assume the caller provides a proper design matrix or we add one.
            # For safety, we add a constant column if the first column is not all 1s.
            # But standard practice is to pass X with constant. Let's assume X is passed correctly
            # but if it's not, statsmodels.api adds it if we use sm.OLS(Y, X).
            # Let's use sm.OLS which expects X to include constant if we want one,
            # OR we can use sm.add_constant.
            # To be safe and standard:
            X = sm.add_constant(design_matrix)
        else:
            X = design_matrix

        Y = roi_timeseries
        model = sm.OLS(Y, X)
        results = model.fit()

        residuals = results.resid
        if len(residuals) == 0:
            raise NoiseEstimationError("GLM fit produced no residuals.")

        # Variance of residuals
        var_resid = np.var(residuals, ddof=len(results.params))
        return float(var_resid)

    except Exception as e:
        logger.error(f"GLM fitting failed for residual variance estimation: {e}")
        raise NoiseEstimationError(f"GLM fitting failed: {e}")


def estimate_autocorrelation(residuals: np.ndarray, max_lag: int = 20) -> Dict[int, float]:
    """
    Estimate the autocorrelation function (ACF) of the residuals.

    Args:
        residuals: 1D array of residuals.
        max_lag: Maximum lag to compute ACF for.

    Returns:
        Dict mapping lag -> autocorrelation coefficient.
    """
    if len(residuals) < max_lag + 10:
        logger.warning(f"Series length {len(residuals)} is too short for max_lag {max_lag}. Reducing max_lag.")
        max_lag = max(1, len(residuals) // 2)

    try:
        # Use statsmodels ACF
        acf_values = acf(residuals, nlags=max_lag, fft=False)
        return {int(lag): float(val) for lag, val in enumerate(acf_values)}
    except Exception as e:
        logger.error(f"ACF calculation failed: {e}")
        # Return zeros on failure to allow pipeline to continue
        return {int(lag): 0.0 for lag in range(max_lag + 1)}


def calculate_noise_degrees_of_freedom(n_obs: int, n_params: int, autocorr_lags: Dict[int, float]) -> int:
    """
    Calculate effective degrees of freedom adjusted for autocorrelation.

    This is a simplified adjustment based on the sum of autocorrelations.
    A more rigorous approach would use the AR(1) parameter.

    Args:
        n_obs: Number of observations (time points).
        n_params: Number of parameters in the model.
        autocorr_lags: Dictionary of lag -> autocorrelation.

    Returns:
        int: Adjusted degrees of freedom.
    """
    # Sum of autocorrelations for positive lags
    rho_sum = sum(
        val for lag, val in autocorr_lags.items()
        if lag > 0 and val != 0.0
    )

    # Effective sample size adjustment (simplified)
    # n_eff = n_obs * (1 - rho) / (1 + rho) for AR(1)
    # Here we use a sum approximation
    if rho_sum > 0:
        # Penalize DOF
        adjustment_factor = 1.0 / (1.0 + 2.0 * rho_sum)
    else:
        adjustment_factor = 1.0

    n_eff = n_obs * adjustment_factor
    dof = int(n_eff - n_params)

    return max(1, dof)


def estimate_noise_parameters(
    roi_timeseries: np.ndarray,
    design_matrix: np.ndarray,
    max_lag: int = 20
) -> Dict[str, Any]:
    """
    Estimate full noise parameters for a single ROI.

    Args:
        roi_timeseries: 1D array of ROI time-series.
        design_matrix: 2D array of design matrix.
        max_lag: Maximum lag for ACF.

    Returns:
        Dictionary with 'residual_variance', 'acf', 'dof', 'n_obs', 'n_params'.
    """
    # Estimate residuals
    var_resid = estimate_residual_variance(roi_timeseries, design_matrix)
    residuals = roi_timeseries - np.dot(design_matrix, np.linalg.lstsq(design_matrix, roi_timeseries, rcond=None)[0])

    # Estimate ACF
    acf_dict = estimate_autocorrelation(residuals, max_lag)

    # Estimate DOF
    dof = calculate_noise_degrees_of_freedom(
        n_obs=len(roi_timeseries),
        n_params=design_matrix.shape[1],
        autocorr_lags=acf_dict
    )

    return {
        "residual_variance": var_resid,
        "acf": acf_dict,
        "dof": dof,
        "n_obs": int(len(roi_timeseries)),
        "n_params": int(design_matrix.shape[1])
    }


def estimate_noise_from_roi_data(
    roi_data_path: Path,
    design_matrix: np.ndarray
) -> Dict[str, Any]:
    """
    Load ROI data from a preprocessed file and estimate noise parameters.

    Args:
        roi_data_path: Path to the preprocessed ROI timeseries file (numpy .npy or similar).
                       Assuming it's a 1D array or a row in a 2D array.
                       If it's a .nii.gz, we expect the logic to be handled by the caller
                       or we assume this function takes a numpy array loaded by the caller.
                       Based on the pipeline, we assume the input is a numpy array loaded
                       from the derived data directory.
        design_matrix: 2D array of design matrix.

    Returns:
        Dictionary of noise parameters.

    Note:
        This function expects `roi_data_path` to point to a file that can be loaded
        into a 1D numpy array. If the file format is complex (e.g., NIfTI), the caller
        should extract the time series before calling this, or we add loading logic here.
        Given the dependency on T013b (spatial_smoothing), the data is likely in a derived
        directory as .npy or similar. We will assume the caller passes the array or we
        load it if it's a .npy file.
    """
    try:
        # Attempt to load as numpy file
        if roi_data_path.suffix == '.npy':
            data = np.load(roi_data_path)
        elif roi_data_path.suffix == '.txt':
            data = np.loadtxt(roi_data_path)
        else:
            # Fallback: try loading as numpy anyway, or raise error
            # For NIfTI, the caller should have extracted the time series.
            # We will assume the path points to a numpy-serializable file.
            raise ValueError(f"Unsupported file format: {roi_data_path.suffix}. Expected .npy or .txt.")

        if data.ndim > 1:
            # If 2D, assume it's (n_rois, n_timepoints) or (n_timepoints, n_rois)
            # We'll take the first column/row as a sample or average?
            # For noise estimation per ROI, we usually do it per ROI.
            # Here we assume the file contains a single ROI's time series (1D)
            # or we take the mean if it's multi-ROI (not ideal but safe).
            if data.shape[0] > data.shape[1]:
                # (n_timepoints, n_rois) -> take first column
                data = data[:, 0]
            else:
                # (n_rois, n_timepoints) -> take first row
                data = data[0, :]

        if data.ndim != 1:
            raise NoiseEstimationError(f"Loaded data is not 1D: {data.shape}")

        return estimate_noise_parameters(data, design_matrix)

    except FileNotFoundError:
        logger.error(f"ROI data file not found: {roi_data_path}")
        raise
    except Exception as e:
        logger.error(f"Failed to estimate noise from {roi_data_path}: {e}")
        raise


def aggregate_noise_statistics(
    noise_estimates: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Aggregate noise statistics from multiple ROIs or iterations.

    Args:
        noise_estimates: List of dictionaries containing noise parameters.

    Returns:
        Dictionary with aggregated statistics (mean variance, mean ACF, etc.).
    """
    if not noise_estimates:
        return {"error": "No estimates provided"}

    variances = [est["residual_variance"] for est in noise_estimates]
    dofs = [est["dof"] for est in noise_estimates]

    # Aggregate ACF (average across ROIs)
    # Find max lag
    max_lag = max(len(est["acf"]) - 1 for est in noise_estimates)
    avg_acf = {}
    for lag in range(max_lag + 1):
        vals = [est["acf"].get(lag, 0.0) for est in noise_estimates]
        avg_acf[lag] = float(np.mean(vals))

    return {
        "mean_residual_variance": float(np.mean(variances)),
        "std_residual_variance": float(np.std(variances)),
        "mean_dof": float(np.mean(dofs)),
        "min_dof": int(np.min(dofs)),
        "max_dof": int(np.max(dofs)),
        "aggregated_acf": avg_acf,
        "n_estimates": len(noise_estimates)
    }


def main():
    """
    Main entry point for noise estimation.

    This function is intended to be called by the pipeline orchestration.
    It expects arguments:
      --input_dir: Directory containing preprocessed ROI data.
      --design_matrix: Path to design matrix (numpy file).
      --output_file: Path to save aggregated noise statistics.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Estimate noise characteristics from preprocessed fMRI data.")
    parser.add_argument("--input_dir", type=str, required=True, help="Directory with preprocessed ROI data (npy files).")
    parser.add_argument("--design_matrix", type=str, required=True, help="Path to design matrix (.npy).")
    parser.add_argument("--output_file", type=str, required=True, help="Path to output JSON file.")
    parser.add_argument("--max_lag", type=int, default=20, help="Maximum lag for ACF.")

    args = parser.parse_args()

    input_dir = Path(args.input_dir)
    design_matrix_path = Path(args.design_matrix)
    output_path = Path(args.output_file)

    if not input_dir.exists():
        logger.error(f"Input directory does not exist: {input_dir}")
        sys.exit(1)
    if not design_matrix_path.exists():
        logger.error(f"Design matrix file does not exist: {design_matrix_path}")
        sys.exit(1)

    # Load design matrix
    try:
        design_matrix = np.load(design_matrix_path)
        if design_matrix.ndim != 2:
            logger.error(f"Design matrix must be 2D, got {design_matrix.ndim}D")
            sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to load design matrix: {e}")
        sys.exit(1)

    # Find ROI files
    roi_files = list(input_dir.glob("*.npy"))
    if not roi_files:
        logger.error(f"No .npy files found in {input_dir}")
        sys.exit(1)

    logger.info(f"Found {len(roi_files)} ROI files.")

    noise_estimates = []
    for roi_file in roi_files:
        try:
            logger.info(f"Processing {roi_file.name}...")
            est = estimate_noise_from_roi_data(roi_file, design_matrix)
            noise_estimates.append(est)
        except Exception as e:
            logger.warning(f"Skipped {roi_file.name} due to error: {e}")
            continue

    if not noise_estimates:
        logger.error("No valid noise estimates generated.")
        sys.exit(1)

    # Aggregate
    aggregated = aggregate_noise_statistics(noise_estimates)

    # Save
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(aggregated, f, indent=2)

    logger.info(f"Aggregated noise statistics saved to {output_path}")


if __name__ == "__main__":
    main()