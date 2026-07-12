import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
import logging
import json
import os
from pathlib import Path

# Import data models used for return types
try:
    from utils.data_models import MetricResult
except ImportError:
    # Fallback for direct execution if package structure not fully resolved
    from dataclasses import dataclass
    from typing import List, Optional, Dict, Any
    @dataclass
    class MetricResult:
        metric_name: str
        value: float
        std: float = 0.0
        parameters: Dict[str, Any] = None
        def to_dict(self):
            return {
                "metric_name": self.metric_name,
                "value": self.value,
                "std": self.std,
                "parameters": self.parameters or {}
            }

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def linear_func(x, m, c):
    """Linear function for curve fitting."""
    return m * x + c

def compute_correlation_dimension(
    trajectory: np.ndarray,
    embedding_dim: int = 5,
    max_radius: Optional[float] = None,
    min_points: int = 1000,
    time_delay: int = 1
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Compute the Correlation Dimension using the Grassberger-Procaccia algorithm.

    Args:
        trajectory: 2D numpy array of shape (N, D) representing the time series.
        embedding_dim: Maximum embedding dimension to search.
        max_radius: Maximum radius for correlation integral. If None, uses 10% of max distance.
        min_points: Minimum number of points required for valid computation.
        time_delay: Time delay for embedding (default 1).

    Returns:
        Tuple of (correlation_dimension, std_dev, parameters_dict)
    """
    if trajectory.shape[0] < min_points:
        logger.warning(f"Trajectory has {trajectory.shape[0]} points, less than min_points={min_points}. Result may be unreliable.")
    
    N, D = trajectory.shape
    
    # Perform time-delay embedding
    if time_delay > 0:
        # Create embedded vectors
        max_lag = embedding_dim * time_delay
        if N <= max_lag:
            raise ValueError(f"Trajectory length {N} is too short for embedding dimension {embedding_dim} and delay {time_delay}")
        
        embedded = np.zeros((N - max_lag, embedding_dim))
        for i in range(embedding_dim):
            embedded[:, i] = trajectory[time_delay * i : N - max_lag + time_delay * i]
    else:
        embedded = trajectory[:N - embedding_dim + 1]
        embedding_dim = 1

    n_embedded = embedded.shape[0]
    
    # Calculate all pairwise distances
    distances = cdist(embedded, embedded, metric='euclidean')
    
    # Upper triangle (excluding diagonal)
    upper_tri = distances[np.triu_indices(n_embedded, k=1)]
    total_pairs = len(upper_tri)
    
    if max_radius is None:
        max_radius = np.percentile(upper_tri, 10)
    
    # Define radii for correlation integral calculation
    radii = np.linspace(max_radius * 0.01, max_radius, 50)
    log_radii = np.log(radii)
    
    correlation_integrals = []
    
    for r in radii:
        # Count pairs with distance < r
        count = np.sum(upper_tri < r)
        C_r = count / total_pairs
        if C_r > 0:
            correlation_integrals.append(np.log(C_r))
        else:
            correlation_integrals.append(np.log(1e-10)) # Avoid log(0)
    
    correlation_integrals = np.array(correlation_integrals)
    
    # Fit linear region to estimate dimension
    # Typically the middle 50% of the scaling region
    valid_indices = np.where((correlation_integrals > -10) & (log_radii > log_radii.min() + 0.1))[0]
    
    if len(valid_indices) < 5:
        logger.warning("Not enough valid points for linear fit in correlation dimension calculation.")
        return 0.0, 0.0, {"error": "insufficient_data"}
    
    x_fit = log_radii[valid_indices]
    y_fit = correlation_integrals[valid_indices]
    
    try:
        popt, pcov = curve_fit(linear_func, x_fit, y_fit, p0=[1.0, 0.0])
        slope, intercept = popt
        perr = np.sqrt(np.diag(pcov))
        std_dev = perr[0]
    except Exception as e:
        logger.warning(f"Curve fitting failed: {e}. Returning slope from simple linear regression.")
        # Fallback to simple linear regression
        slope = np.polyfit(x_fit, y_fit, 1)[0]
        std_dev = 0.0
    
    return slope, std_dev, {"embedding_dim": embedding_dim, "time_delay": time_delay, "radii_range": (radii.min(), radii.max())}

def compute_lyapunov_exponent_rosenstein(
    trajectory: np.ndarray,
    max_time: int = 100,
    min_separation: int = 10,
    time_delay: int = 1,
    embedding_dim: int = 5
) -> Tuple[float, float, Dict[str, Any]]:
    """
    Compute the Largest Lyapunov Exponent using Rosenstein's algorithm.

    Args:
        trajectory: 2D numpy array of shape (N, D).
        max_time: Maximum time steps for divergence tracking.
        min_separation: Minimum separation between neighbors in phase space.
        time_delay: Time delay for embedding.
        embedding_dim: Embedding dimension.

    Returns:
        Tuple of (lyapunov_exponent, std_dev, parameters_dict)
    """
    N, D = trajectory.shape
    
    # Embed the trajectory
    if time_delay > 0:
        max_lag = embedding_dim * time_delay
        if N <= max_lag:
            raise ValueError(f"Trajectory length {N} is too short for embedding.")
        
        embedded = np.zeros((N - max_lag, embedding_dim))
        for i in range(embedding_dim):
            embedded[:, i] = trajectory[time_delay * i : N - max_lag + time_delay * i]
    else:
        embedded = trajectory[:N - embedding_dim + 1]
        embedding_dim = 1

    n_embedded = embedded.shape[0]
    
    # Find nearest neighbors for each point
    # Exclude points too close in time (min_separation)
    distances = cdist(embedded, embedded, metric='euclidean')
    
    # Set self-distances to infinity
    np.fill_diagonal(distances, np.inf)
    
    # Set temporal neighbors to infinity
    for i in range(n_embedded):
        start = max(0, i - min_separation)
        end = min(n_embedded, i + min_separation)
        distances[i, start:end] = np.inf
    
    # Find nearest neighbor index for each point
    nn_indices = np.argmin(distances, axis=1)
    nn_distances = np.min(distances, axis=1)
    
    # Filter out points with no valid neighbors
    valid_mask = nn_distances < np.inf
    if np.sum(valid_mask) == 0:
        logger.warning("No valid neighbors found for Lyapunov exponent calculation.")
        return 0.0, 0.0, {"error": "no_neighbors"}
    
    # Track divergence over time
    divergence = []
    times = []
    
    for k in range(max_time):
        if k >= n_embedded:
            break
        
        # Calculate average log divergence at time k
        log_div = []
        for i in range(n_embedded - k):
            if valid_mask[i]:
                j = nn_indices[i]
                # Ensure j + k is within bounds
                if j + k < n_embedded:
                    dist = np.linalg.norm(embedded[i+k] - embedded[j+k])
                    if dist > 0:
                        log_div.append(np.log(dist))
        
        if log_div:
            avg_log_div = np.mean(log_div)
            divergence.append(avg_log_div)
            times.append(k)
    
    if len(divergence) < 5:
        logger.warning("Not enough points for Lyapunov exponent calculation.")
        return 0.0, 0.0, {"error": "insufficient_data"}
    
    # Fit linear region to estimate Lyapunov exponent
    times = np.array(times)
    divergence = np.array(divergence)
    
    # Typically use the first 10-20% of the time series for linear fit
    fit_range = min(len(divergence) // 5, 20)
    if fit_range < 5:
        fit_range = len(divergence) // 2
    
    x_fit = times[:fit_range]
    y_fit = divergence[:fit_range]
    
    try:
        popt, pcov = curve_fit(linear_func, x_fit, y_fit, p0=[1.0, 0.0])
        slope, intercept = popt
        perr = np.sqrt(np.diag(pcov))
        std_dev = perr[0]
    except Exception as e:
        logger.warning(f"Curve fitting failed for Lyapunov: {e}.")
        slope = np.polyfit(x_fit, y_fit, 1)[0]
        std_dev = 0.0
    
    return slope, std_dev, {"max_time": max_time, "embedding_dim": embedding_dim, "time_delay": time_delay}

def compute_false_nearest_neighbors(
    trajectory: np.ndarray,
    embedding_dim_max: int = 10,
    threshold: float = 10.0,
    time_delay: int = 1
) -> Tuple[List[float], Dict[str, Any]]:
    """
    Compute the False Nearest Neighbors (FNN) rate for increasing embedding dimensions.

    Args:
        trajectory: 2D numpy array of shape (N, D).
        embedding_dim_max: Maximum embedding dimension to test.
        threshold: Threshold multiplier for standard deviation (default 10).
        time_delay: Time delay for embedding.

    Returns:
        Tuple of (list of FNN rates for each dimension, parameters_dict)
    """
    N, D = trajectory.shape
    
    # Calculate standard deviation of the time series for threshold
    std_val = np.std(trajectory)
    if std_val == 0:
        std_val = 1.0 # Avoid division by zero
    
    threshold_val = threshold * std_val
    
    fnn_rates = []
    
    for m in range(1, embedding_dim_max + 1):
        # Create embedded vectors
        max_lag = m * time_delay
        if N <= max_lag:
            fnn_rates.append(1.0) # All points are false neighbors if too short
            continue
        
        embedded = np.zeros((N - max_lag, m))
        for i in range(m):
            embedded[:, i] = trajectory[time_delay * i : N - max_lag + time_delay * i]
        
        # Find nearest neighbors in m-dimensional space
        distances = cdist(embedded, embedded, metric='euclidean')
        np.fill_diagonal(distances, np.inf)
        
        nn_indices = np.argmin(distances, axis=1)
        nn_distances = np.min(distances, axis=1)
        
        # Count false neighbors
        false_count = 0
        total_count = 0
        
        for i in range(len(embedded)):
            j = nn_indices[i]
            if nn_distances[i] < np.inf:
                total_count += 1
                
                # Check if neighbor is false in (m+1) dimension (simulated by checking distance in current space vs expected)
                # Actually, FNN checks if the distance in m+1 dimension is significantly larger than in m
                # Since we are iterating m, we check if the neighbor in m-dim is still a neighbor in (m+1)-dim
                # But here we compute FNN for a specific m by checking if the distance increase is too large
                # Standard approach: if ||x_{i+m} - x_{j+m}|| / ||x_i - x_j|| > threshold
                
                # We need to check the distance in the (m+1)-th component
                if m < embedding_dim_max:
                    # We can't easily check m+1 without recomputing, so we use a simpler heuristic:
                    # If the distance to the nearest neighbor is large relative to the threshold, it's likely false
                    # But the standard FNN algorithm checks the distance ratio between m and m+1
                    pass
                
                # Correct approach: check if the distance in the (m+1)-th dimension is too large
                # We'll do this by checking the distance in the current embedding vs the next point
                # Actually, let's implement the standard FNN check:
                # A point x_i and its nearest neighbor x_j are false neighbors in dimension m if:
                # ||x_{i+m} - x_{j+m}|| / ||x_i - x_j|| > threshold
                
                # We have embedded vectors of dimension m. We need to check the (m+1)-th component.
                # Since we are at dimension m, we can't check m+1 without recomputing.
                # Instead, we check if the distance in the current embedding is small, but the next component
                # (which we don't have yet) would make them far apart.
                
                # Alternative: We compute FNN for dimension m by checking if the distance in the (m+1)-th dimension
                # (which is the m-th index in 0-based indexing for the next step) is too large.
                # This is a bit circular. Let's use the standard method:
                # For each point i, find its nearest neighbor j in m-dimensional space.
                # Then check the distance in the (m+1)-th dimension (i.e., the m-th component of the next point in the time series).
                # But we don't have m+1 embedding. So we check the distance in the current embedding vs the distance in the next point's embedding.
                
                # Simpler: We check if the distance between i and j in m-dim is small, but the distance between i+1 and j+1 in m-dim is large.
                # This is not exactly FNN but a proxy.
                
                # Let's implement the standard FNN properly:
                # We need to check the distance in the (m+1)-th dimension.
                # Since we are at dimension m, we can't do that directly.
                # Instead, we check the distance in the current embedding vs the distance in the next point's embedding.
                
                # Actually, the standard FNN algorithm checks:
                # R(i, j, m) = ||x_{i+m} - x_{j+m}|| / ||x_i - x_j||
                # If R > threshold, then the neighbor is false.
                
                # We have embedded vectors of dimension m. We can compute the distance in the m-th component (which is the last one).
                # But we need the (m+1)-th component, which is not available in the current embedding.
                
                # So we need to compute the embedding for dimension m+1 to check FNN for dimension m.
                # This is inefficient. Instead, we can compute FNN for dimension m by checking the distance in the m-th component
                # relative to the distance in the (m-1)-th component.
                
                # Let's use a different approach:
                # We check if the distance in the current embedding (m-dim) is small, but the distance in the next point's embedding (also m-dim) is large.
                # This is not standard FNN, but it's a proxy.
                
                # Correct implementation:
                # We need to check the distance in the (m+1)-th dimension.
                # Since we don't have it, we skip this check and use a simpler method:
                # If the distance to the nearest neighbor is greater than threshold, count as false.
                
                # Actually, let's do it properly:
                # We compute the embedding for dimension m+1 and check the distance in the (m+1)-th component.
                # This requires recomputing the embedding for each m, which is expensive.
                
                # For efficiency, we'll compute the embedding for dimension m+1 and check the FNN for dimension m.
                if m + 1 <= embedding_dim_max:
                    max_lag_next = (m + 1) * time_delay
                    if N > max_lag_next:
                        embedded_next = np.zeros((N - max_lag_next, m + 1))
                        for k in range(m + 1):
                            embedded_next[:, k] = trajectory[time_delay * k : N - max_lag_next + time_delay * k]
                        
                        # Get the (m+1)-th component (index m)
                        # Check the distance in the (m+1)-th component
                        dist_m_plus_1 = np.abs(embedded_next[i, m] - embedded_next[j, m])
                        dist_m = np.linalg.norm(embedded[i] - embedded[j])
                        
                        if dist_m > 0 and dist_m_plus_1 / dist_m > threshold_val:
                            false_count += 1
                    else:
                        # Not enough points for m+1 embedding
                        false_count += 1
                else:
                    # Can't check m+1, so we can't determine FNN
                    # Assume not false for the last dimension
                    pass
        
        if total_count > 0:
            fnn_rate = false_count / total_count
        else:
            fnn_rate = 1.0
        
        fnn_rates.append(fnn_rate)
    
    return fnn_rates, {"embedding_dim_max": embedding_dim_max, "threshold": threshold, "time_delay": time_delay}

def compute_ground_truth_metrics(
    trajectory: np.ndarray,
    seed: int,
    output_dir: str = "data/processed"
) -> Dict[str, Any]:
    """
    Compute ground truth metrics (Correlation Dimension, Lyapunov Exponent, FNN) for a clean trajectory.

    Args:
        trajectory: 2D numpy array of shape (N, D).
        seed: Random seed used for generation (for metadata).
        output_dir: Directory to save the results.

    Returns:
        Dictionary containing the computed metrics.
    """
    logger.info(f"Computing ground truth metrics for seed {seed}...")
    
    # Compute Correlation Dimension
    cd, cd_std, cd_params = compute_correlation_dimension(trajectory)
    logger.info(f"Correlation Dimension: {cd:.4f} +/- {cd_std:.4f}")
    
    # Compute Lyapunov Exponent
    lyap, lyap_std, lyap_params = compute_lyapunov_exponent_rosenstein(trajectory)
    logger.info(f"Lyapunov Exponent: {lyap:.4f} +/- {lyap_std:.4f}")
    
    # Compute FNN
    fnn_rates, fnn_params = compute_false_nearest_neighbors(trajectory)
    logger.info(f"FNN rates: {fnn_rates}")
    
    # Determine optimal embedding dimension (where FNN rate drops below 5%)
    optimal_dim = 1
    for i, rate in enumerate(fnn_rates):
        if rate < 0.05:
            optimal_dim = i + 1
            break
    
    logger.info(f"Optimal embedding dimension: {optimal_dim}")
    
    results = {
        "seed": seed,
        "correlation_dimension": {
            "value": cd,
            "std": cd_std,
            "parameters": cd_params
        },
        "lyapunov_exponent": {
            "value": lyap,
            "std": lyap_std,
            "parameters": lyap_params
        },
        "false_nearest_neighbors": {
            "rates": fnn_rates,
            "optimal_embedding_dim": optimal_dim,
            "parameters": fnn_params
        }
    }
    
    # Save results
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"ground_truth_metrics_{seed}.json")
    
    with open(output_path, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Ground truth metrics saved to {output_path}")
    
    return results

def run_ground_truth_computation(
    trajectory_data: Dict[str, Any],
    output_dir: str = "data/processed"
) -> List[Dict[str, Any]]:
    """
    Run ground truth computation for a list of trajectories.

    Args:
        trajectory_data: List of dictionaries containing 'trajectory' (np.ndarray) and 'seed' (int).
        output_dir: Directory to save results.

    Returns:
        List of metric results dictionaries.
    """
    all_results = []
    
    for item in trajectory_data:
        trajectory = item['trajectory']
        seed = item['seed']
        
        results = compute_ground_truth_metrics(trajectory, seed, output_dir)
        all_results.append(results)
    
    return all_results

def get_metric_computation_functions() -> Dict[str, callable]:
    """
    Return a dictionary of metric computation functions.

    Returns:
        Dictionary mapping metric names to computation functions.
    """
    return {
        "correlation_dimension": compute_correlation_dimension,
        "lyapunov_exponent": compute_lyapunov_exponent_rosenstein,
        "false_nearest_neighbors": compute_false_nearest_neighbors,
        "ground_truth_metrics": compute_ground_truth_metrics
    }