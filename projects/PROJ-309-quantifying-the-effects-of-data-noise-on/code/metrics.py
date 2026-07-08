"""
metrics.py - Implementation of phase space reconstruction metrics.

This module provides functions to compute:
1. Correlation Dimension (Grassberger-Procaccia algorithm)
2. Largest Lyapunov Exponent (Rosenstein's algorithm)
3. False Nearest Neighbors (FNN)

These metrics are used to characterize the dynamical properties of time-series data
and assess the quality of phase space reconstruction under noise.
"""

import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
import logging

# Configure logging
logger = logging.getLogger(__name__)


def linear_func(x: np.ndarray, m: float, b: float) -> np.ndarray:
    """
    Simple linear function for curve fitting.

    Args:
        x: Input array.
        m: Slope.
        b: Intercept.

    Returns:
        Linear prediction: m*x + b
    """
    return m * x + b


def compute_correlation_dimension(
    trajectory: np.ndarray,
    embedding_dim: int = 5,
    max_radius: Optional[float] = None,
    min_radius: Optional[float] = None,
    radius_steps: int = 50
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the Correlation Dimension using the Grassberger-Procaccia algorithm.

    The correlation dimension D2 estimates the fractal dimension of the attractor
    by analyzing how the correlation integral C(r) scales with radius r.
    C(r) ~ r^D2

    Args:
        trajectory: 2D array of shape (N, d) representing the trajectory in phase space.
        embedding_dim: Maximum embedding dimension to test (default: 5).
        max_radius: Maximum radius to consider (fraction of data std). If None, auto-calculated.
        min_radius: Minimum radius to consider (fraction of data std). If None, auto-calculated.
        radius_steps: Number of radius values to test (default: 50).

    Returns:
        Tuple containing:
            - correlation_dimension (float): The estimated correlation dimension.
            - metadata (dict): Diagnostic information including log-log slope and range used.
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(-1, 1)

    N, d = trajectory.shape
    logger.info(f"Computing Correlation Dimension for trajectory of shape {trajectory.shape}")

    # Auto-calculate radius bounds if not provided
    data_std = np.std(trajectory)
    if max_radius is None:
        max_radius = 0.5 * data_std
    if min_radius is None:
        min_radius = 0.01 * data_std

    radii = np.logspace(np.log10(min_radius), np.log10(max_radius), radius_steps)
    log_radii = np.log(radii)
    correlation_integrals = []

    # Compute correlation integral for each radius
    # Optimization: Use KDTree or cdist for distance matrix
    # For moderate N, cdist is efficient enough
    dist_matrix = cdist(trajectory, trajectory)

    for r in radii:
        # Count pairs within distance r (excluding self-pairs and lagged points)
        # Lagged points: points within time delay tau are not independent
        # Here we use a simple lag of 1 for robustness, though optimal tau depends on data
        lag = 1
        count = 0
        total_pairs = 0

        for i in range(N):
            for j in range(i + 1, N):
                if j - i <= lag:
                    continue
                if dist_matrix[i, j] < r:
                    count += 1
                total_pairs += 1

        C_r = count / total_pairs if total_pairs > 0 else 0
        correlation_integrals.append(C_r)

    correlation_integrals = np.array(correlation_integrals)

    # Filter out zero values to avoid log(0)
    valid_mask = correlation_integrals > 0
    if np.sum(valid_mask) < 2:
        logger.warning("Too few valid pairs for correlation dimension estimation.")
        return -1.0, {"error": "Insufficient data for reliable estimation"}

    valid_radii = log_radii[valid_mask]
    valid_C = np.log(correlation_integrals[valid_mask])

    # Fit linear model to log-log plot
    try:
        popt, _ = curve_fit(linear_func, valid_radii, valid_C, p0=[1.0, 0.0])
        slope = popt[0]
        # The correlation dimension is the slope
        dim = slope
    except Exception as e:
        logger.warning(f"Curve fitting failed for correlation dimension: {e}")
        dim = -1.0

    metadata = {
        "slope": slope if 'slope' in locals() else dim,
        "radius_range": (min_radius, max_radius),
        "num_points": N,
        "embedding_dim_tested": embedding_dim
    }

    logger.info(f"Correlation Dimension estimated: {dim:.4f}")
    return dim, metadata


def compute_lyapunov_exponent_rosenstein(
    trajectory: np.ndarray,
    embedding_dim: int = 5,
    time_delay: int = 10,
    min_separation: int = 10,
    max_time: Optional[int] = None
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the Largest Lyapunov Exponent using Rosenstein's algorithm.

    Rosenstein's method tracks the evolution of nearest neighbors in the phase space.
    The average logarithmic divergence of these trajectories over time gives the
    largest Lyapunov exponent.

    Args:
        trajectory: 2D array of shape (N, d) representing the trajectory.
        embedding_dim: Embedding dimension for phase space reconstruction (default: 5).
        time_delay: Time delay for embedding (default: 10).
        min_separation: Minimum temporal separation for nearest neighbor search (default: 10).
        max_time: Maximum time steps to track divergence (default: N // 2).

    Returns:
        Tuple containing:
            - lyapunov_exponent (float): The estimated largest Lyapunov exponent.
            - metadata (dict): Diagnostic information including divergence curve.
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(-1, 1)

    N, d = trajectory.shape
    logger.info(f"Computing Lyapunov Exponent (Rosenstein) for trajectory of shape {trajectory.shape}")

    if max_time is None:
        max_time = N // 2

    # Reconstruct phase space if necessary (though trajectory is assumed to be embedded)
    # For this implementation, we assume trajectory is already in the correct dimension
    # If embedding is needed, it would be done here using delay embedding

    # Find nearest neighbors for each point (excluding temporal neighbors)
    dist_matrix = cdist(trajectory, trajectory)

    # Initialize divergence array
    divergence = np.zeros(max_time)
    neighbor_count = 0

    for i in range(N - max_time - min_separation):
        # Find nearest neighbor excluding temporal neighbors
        # Mask out temporal neighbors
        mask = np.ones(N, dtype=bool)
        mask[max(0, i - min_separation):min(N, i + min_separation + 1)] = False
        mask[i] = False

        if not np.any(mask):
            continue

        distances = dist_matrix[i, mask]
        nearest_idx = np.argmin(distances)
        # Get original index
        original_indices = np.where(mask)[0]
        j = original_indices[nearest_idx]

        # Track divergence over time
        for k in range(max_time):
            if i + k >= N or j + k >= N:
                break
            dist_k = dist_matrix[i + k, j + k]
            if dist_k > 0:
                divergence[k] += np.log(dist_k)
                neighbor_count += 1

    if neighbor_count == 0:
        logger.warning("No valid neighbors found for Lyapunov exponent estimation.")
        return -1.0, {"error": "No valid neighbors"}

    divergence /= neighbor_count

    # Fit linear slope to the initial part of the divergence curve
    # Typically the first 10-20% of max_time
    fit_range = max(5, int(max_time * 0.2))
    x_fit = np.arange(fit_range)
    y_fit = divergence[:fit_range]

    try:
        popt, _ = curve_fit(linear_func, x_fit, y_fit, p0=[0.1, 0.0])
        lyap_exp = popt[0]
    except Exception as e:
        logger.warning(f"Curve fitting failed for Lyapunov exponent: {e}")
        lyap_exp = -1.0

    metadata = {
        "divergence_curve": divergence[:max_time].tolist(),
        "fit_range": fit_range,
        "num_neighbors": neighbor_count
    }

    logger.info(f"Largest Lyapunov Exponent estimated: {lyap_exp:.4f}")
    return lyap_exp, metadata


def compute_false_nearest_neighbors(
    trajectory: np.ndarray,
    embedding_dim_max: int = 10,
    threshold: float = 10.0
) -> Tuple[List[float], Dict[str, Any]]:
    """
    Compute the False Nearest Neighbors (FNN) rate for increasing embedding dimensions.

    FNN analysis helps determine the minimum embedding dimension required to
    unfold the attractor without false neighbors caused by projection.

    Args:
        trajectory: 1D or 2D array representing the time series.
        embedding_dim_max: Maximum embedding dimension to test (default: 10).
        threshold: Threshold multiplier for standard deviation to identify false neighbors (default: 10).

    Returns:
        Tuple containing:
            - fnn_rates (list): FNN rate for each embedding dimension from 1 to embedding_dim_max.
            - metadata (dict): Diagnostic information.
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(-1, 1)

    N, d = trajectory.shape
    logger.info(f"Computing False Nearest Neighbors for trajectory of shape {trajectory.shape}")

    # If input is 1D time series, we need to perform delay embedding
    # For simplicity, assume trajectory is already a 1D time series and we embed it
    if d == 1:
        time_series = trajectory.flatten()
    else:
        # If already embedded, we still need to test higher dimensions
        # This case is less common for FNN which is usually for 1D series
        time_series = trajectory[:, 0] if d > 0 else trajectory.flatten()

    fnn_rates = []
    data_std = np.std(time_series)
    threshold_val = threshold * data_std

    for m in range(1, embedding_dim_max + 1):
        # Construct embedding for dimension m
        # Embedding: [x(t), x(t+1), ..., x(t+m-1)]
        # We need at least m points
        if N < m + 1:
            fnn_rates.append(1.0)
            continue

        # Create embedded vectors
        embedded = np.array([
            time_series[i:i+m] for i in range(N - m + 1)
        ])

        # For each point, find its nearest neighbor in m-dimensional space
        # Check if it remains a neighbor in (m+1)-dimensional space
        # And if the distance increase is significant

        fnn_count = 0
        total_pairs = 0

        dist_matrix_m = cdist(embedded, embedded)

        # For each point, find nearest neighbor (excluding self and close temporal points)
        for i in range(len(embedded) - 1):
            # Find nearest neighbor
            # Mask self and close temporal neighbors
            mask = np.ones(len(embedded), dtype=bool)
            # Temporal proximity: exclude points within m steps
            start = max(0, i - m)
            end = min(len(embedded), i + m + 1)
            mask[start:end] = False
            mask[i] = False

            if not np.any(mask):
                continue

            distances = dist_matrix_m[i, mask]
            nearest_idx = np.argmin(distances)
            original_indices = np.where(mask)[0]
            j = original_indices[nearest_idx]

            # Now check in (m+1) dimension if they are still neighbors
            # We need to construct (m+1) embedding for points i and j
            if i + m >= len(time_series) or j + m >= len(time_series):
                continue

            vec_m_i = embedded[i]
            vec_m_j = embedded[j]

            # Extend to m+1 dimension
            vec_mp1_i = np.append(vec_m_i, time_series[i + m])
            vec_mp1_j = np.append(vec_m_j, time_series[j + m])

            dist_m = np.linalg.norm(vec_m_i - vec_m_j)
            dist_mp1 = np.linalg.norm(vec_mp1_i - vec_mp1_j)

            # Check if the distance increased significantly
            if dist_m > 0:
                ratio = (dist_mp1 - dist_m) / dist_m
                if ratio > threshold_val:
                    fnn_count += 1

            total_pairs += 1

        fnn_rate = fnn_count / total_pairs if total_pairs > 0 else 1.0
        fnn_rates.append(fnn_rate)

    metadata = {
        "embedding_dims_tested": list(range(1, embedding_dim_max + 1)),
        "threshold": threshold,
        "data_length": N
    }

    logger.info(f"FNN computation complete. Rates: {fnn_rates}")
    return fnn_rates, metadata


def compute_ground_truth_metrics(
    trajectory: np.ndarray,
    seed: int,
    system_type: str
) -> Dict[str, Any]:
    """
    Compute all ground truth metrics for a clean trajectory.

    This function orchestrates the computation of Correlation Dimension,
    Lyapunov Exponent, and FNN for a given clean trajectory.

    Args:
        trajectory: 2D array of shape (N, d) representing the clean trajectory.
        seed: Random seed used for generation (for metadata).
        system_type: Type of system (e.g., 'lorenz', 'rossler').

    Returns:
        Dictionary containing all computed metrics and metadata.
    """
    logger.info(f"Computing ground truth metrics for {system_type} system (seed={seed})")

    # Compute Correlation Dimension
    corr_dim, corr_meta = compute_correlation_dimension(trajectory)

    # Compute Lyapunov Exponent
    lyap_exp, lyap_meta = compute_lyapunov_exponent_rosenstein(trajectory)

    # Compute FNN
    fnn_rates, fnn_meta = compute_false_nearest_neighbors(trajectory)

    result = {
        "system_type": system_type,
        "seed": seed,
        "correlation_dimension": corr_dim,
        "correlation_dimension_metadata": corr_meta,
        "lyapunov_exponent": lyap_exp,
        "lyapunov_exponent_metadata": lyap_meta,
        "fnn_rates": fnn_rates,
        "fnn_metadata": fnn_meta
    }

    logger.info(f"Ground truth metrics computed: D2={corr_dim:.4f}, LE={lyap_exp:.4f}")
    return result


def run_ground_truth_computation(
    trajectory: np.ndarray,
    seed: int,
    system_type: str,
    output_path: Optional[str] = None
) -> Dict[str, Any]:
    """
    Run ground truth computation and optionally save results to file.

    Args:
        trajectory: Clean trajectory data.
        seed: Generation seed.
        system_type: System identifier.
        output_path: Optional path to save JSON results.

    Returns:
        Dictionary of computed metrics.
    """
    metrics = compute_ground_truth_metrics(trajectory, seed, system_type)

    if output_path:
        import json
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        logger.info(f"Ground truth metrics saved to {output_path}")

    return metrics


def get_metric_computation_functions() -> Dict[str, callable]:
    """
    Return a dictionary of available metric computation functions.

    Returns:
        Dictionary mapping metric names to their computation functions.
    """
    return {
        "correlation_dimension": compute_correlation_dimension,
        "lyapunov_exponent_rosenstein": compute_lyapunov_exponent_rosenstein,
        "false_nearest_neighbors": compute_false_nearest_neighbors,
        "ground_truth": compute_ground_truth_metrics
    }