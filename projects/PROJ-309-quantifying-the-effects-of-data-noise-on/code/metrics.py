import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
from scipy.optimize import curve_fit
import logging
import os
import json
from pathlib import Path

from utils.data_models import MetricResult, Trajectory
from config import get_system_params, NoiseType

logger = logging.getLogger(__name__)

def linear_func(x: np.ndarray, m: float, c: float) -> np.ndarray:
    """
    Linear function for fitting the scaling region in Grassberger-Procaccia.
    
    Args:
        x: Independent variable (log of radius)
        m: Slope (correlation dimension estimate)
        c: Intercept
        
    Returns:
        y: Predicted values (log of correlation integral)
    """
    return m * x + c

def compute_correlation_dimension(
    trajectory: np.ndarray,
    min_radius: float = 1e-3,
    max_radius: float = 0.5,
    n_radii: int = 50,
    embedding_dim: int = 5,
    time_delay: int = 1,
    min_points: int = 100
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the Correlation Dimension using the Grassberger-Procaccia algorithm.
    
    The correlation dimension D2 is estimated from the scaling of the correlation
    integral C(r) ~ r^D2 in the limit of small r.
    
    Args:
        trajectory: 2D array of shape (n_points, n_dims) containing the time series.
        min_radius: Minimum radius for correlation integral calculation.
        max_radius: Maximum radius for correlation integral calculation.
        n_radii: Number of radii to test.
        embedding_dim: Embedding dimension for delay-coordinate embedding.
        time_delay: Time delay for delay-coordinate embedding.
        min_points: Minimum number of points required for reliable estimation.
        
    Returns:
      tuple: (correlation_dimension, metadata_dict)
          - correlation_dimension: Estimated D2 value
          - metadata_dict: Contains details about the computation (r values, C(r) values, etc.)
    """
    if trajectory.shape[0] < min_points:
        logger.warning(f"Trajectory has only {trajectory.shape[0]} points, "
                     f"which is below the minimum of {min_points}. "
                     "Results may be unreliable.")
    
    # Delay-coordinate embedding
    n_points = trajectory.shape[0]
    n_dims = trajectory.shape[1]
    
    if embedding_dim * time_delay >= n_points:
        logger.error(f"Embedding dimension {embedding_dim} with time delay {time_delay} "
                   f"requires at least {embedding_dim * time_delay} points, "
                   f"but trajectory has only {n_points}.")
        raise ValueError("Insufficient points for specified embedding parameters.")
    
    # Create embedded vectors
    embedded = np.zeros((n_points - embedding_dim * time_delay, embedding_dim * n_dims))
    for i in range(embedding_dim):
        start_idx = i * time_delay
        end_idx = start_idx + n_points - embedding_dim * time_delay
        embedded[:, i * n_dims:(i + 1) * n_dims] = trajectory[start_idx:end_idx]
    
    n_embedded = embedded.shape[0]
    
    # Generate radii on log scale
    radii = np.logspace(np.log10(min_radius), np.log10(max_radius), n_radii)
    
    # Compute correlation integral for each radius
    correlation_integrals = []
    
    # Precompute pairwise distances (only upper triangle needed, but cdist is easier)
    distances = cdist(embedded, embedded, metric='euclidean')
    
    for r in radii:
        # Count pairs with distance < r (excluding self-pairs and temporal neighbors)
        # Temporal neighbor exclusion: Theiler window
        theiler_window = time_delay * embedding_dim
        mask = np.abs(np.arange(n_embedded)[:, None] - np.arange(n_embedded)[None, :]) > theiler_window
        mask[np.arange(n_embedded), np.arange(n_embedded)] = False  # Exclude self-pairs
        
        count = np.sum((distances < r) & mask)
        C_r = count / (n_embedded * (n_embedded - 1) / 2)
        correlation_integrals.append(C_r)
    
    correlation_integrals = np.array(correlation_integrals)
    
    # Filter out zero values to avoid log(0)
    valid_idx = correlation_integrals > 0
    if np.sum(valid_idx) < 3:
        logger.warning("Too few valid correlation integral values for fitting.")
        return 0.0, {"radii": radii, "C_r": correlation_integrals, "error": "insufficient_data"}
    
    log_r = np.log(radii[valid_idx])
    log_C = np.log(correlation_integrals[valid_idx])
    
    # Fit linear region
    try:
        # Try to fit a line to the scaling region
        popt, _ = curve_fit(linear_func, log_r, log_C, p0=[1.0, 0.0], maxfev=1000)
        slope = popt[0]
        
        # Validate slope is reasonable
        if slope <= 0 or slope > embedding_dim:
            logger.warning(f"Unreasonable slope {slope} for correlation dimension. "
                         "Returning 0.0.")
            return 0.0, {"radii": radii, "C_r": correlation_integrals, "slope": slope}
        
        return slope, {
            "radii": radii,
            "C_r": correlation_integrals,
            "slope": slope,
            "intercept": popt[1],
            "embedding_dim": embedding_dim,
            "time_delay": time_delay
        }
    except Exception as e:
        logger.warning(f"Curve fitting failed for correlation dimension: {e}")
        return 0.0, {"radii": radii, "C_r": correlation_integrals, "error": str(e)}

def compute_lyapunov_exponent_rosenstein(
    trajectory: np.ndarray,
    time_delay: int = 1,
    embedding_dim: int = 3,
    min_separation: int = 10,
    max_iterations: int = 50,
    local_window: int = 10
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the largest Lyapunov exponent using Rosenstein's algorithm.
    
    Rosenstein's method estimates the Lyapunov exponent from the average
    exponential divergence of nearby trajectories in phase space.
    
    Args:
        trajectory: 2D array of shape (n_points, n_dims) containing the time series.
        time_delay: Time delay for delay-coordinate embedding.
        embedding_dim: Embedding dimension for delay-coordinate embedding.
        min_separation: Minimum temporal separation between neighboring points.
        max_iterations: Maximum number of iterations to follow divergence.
        local_window: Size of local neighborhood for finding nearest neighbors.
        
    Returns:
        tuple: (lyapunov_exponent, metadata_dict)
            - lyapunov_exponent: Estimated largest Lyapunov exponent
            - metadata_dict: Contains details about the computation
    """
    n_points = trajectory.shape[0]
    n_dims = trajectory.shape[1]
    
    if embedding_dim * time_delay >= n_points:
        logger.error(f"Embedding dimension {embedding_dim} with time delay {time_delay} "
                   f"requires at least {embedding_dim * time_delay} points, "
                   f"but trajectory has only {n_points}.")
        raise ValueError("Insufficient points for specified embedding parameters.")
    
    # Delay-coordinate embedding
    embedded = np.zeros((n_points - embedding_dim * time_delay, embedding_dim * n_dims))
    for i in range(embedding_dim):
        start_idx = i * time_delay
        end_idx = start_idx + n_points - embedding_dim * time_delay
        embedded[:, i * n_dims:(i + 1) * n_dims] = trajectory[start_idx:end_idx]
    
    n_embedded = embedded.shape[0]
    
    # Find nearest neighbors for each point (excluding temporal neighbors)
    nearest_neighbors = []
    distances = []
    
    for i in range(n_embedded):
        # Temporal neighbors to exclude
        exclude = set(range(max(0, i - min_separation), min(n_embedded, i + min_separation + 1)))
        
        # Compute distances to all other points
        dists = np.linalg.norm(embedded - embedded[i], axis=1)
        dists[i] = np.inf  # Exclude self
        for idx in exclude:
            dists[idx] = np.inf
        
        # Find nearest neighbor
        nearest_idx = np.argmin(dists)
        nearest_neighbors.append(nearest_idx)
        distances.append(dists[nearest_idx])
    
    # Filter out points with no valid neighbors
    valid_indices = [i for i, d in enumerate(distances) if d < np.inf and d > 0]
    
    if len(valid_indices) < 10:
        logger.warning("Too few valid nearest neighbors for Lyapunov exponent estimation.")
        return 0.0, {"error": "insufficient_neighbors"}
    
    # Compute divergence over time
    divergence = []
    time_steps = []
    
    for t in range(max_iterations):
        div_sum = 0
        count = 0
        
        for i in valid_indices:
            j = nearest_neighbors[i]
            
            # Check if both points are still within bounds after t steps
            if i + t < n_embedded and j + t < n_embedded:
                # Compute distance between evolved points
                dist = np.linalg.norm(embedded[i + t] - embedded[j + t])
                if dist > 0:
                    div_sum += np.log(dist)
                    count += 1
        
        if count > 0:
            divergence.append(div_sum / count)
            time_steps.append(t)
    
    if len(divergence) < 5:
        logger.warning("Not enough data points for Lyapunov exponent fitting.")
        return 0.0, {"error": "insufficient_divergence_data"}
    
    # Fit linear region to estimate Lyapunov exponent
    time_steps = np.array(time_steps)
    divergence = np.array(divergence)
    
    try:
        # Fit a line to the initial linear region
        popt, _ = curve_fit(linear_func, time_steps, divergence, p0=[0.5, 0.0], maxfev=1000)
        lyapunov_exp = popt[0]
        
        # Lyapunov exponent should be positive for chaotic systems
        if lyapunov_exp < 0:
            logger.warning(f"Negative Lyapunov exponent {lyapunov_exp} detected. "
                         "This may indicate non-chaotic behavior or estimation error.")
        
        return lyapunov_exp, {
            "time_steps": time_steps,
            "divergence": divergence,
            "lyapunov_exponent": lyapunov_exp,
            "intercept": popt[1],
            "embedding_dim": embedding_dim,
            "time_delay": time_delay
        }
    except Exception as e:
        logger.warning(f"Curve fitting failed for Lyapunov exponent: {e}")
        return 0.0, {"error": str(e)}

def compute_false_nearest_neighbors(
    trajectory: np.ndarray,
    embedding_dim_max: int = 10,
    threshold: float = 10.0,
    time_delay: int = 1
) -> Tuple[List[float], Dict[str, Any]]:
    """
    Compute the False Nearest Neighbors (FNN) rate for embedding dimensions 1 to embedding_dim_max.
    
    FNN analysis helps determine the minimum embedding dimension required to unfold
    the attractor without false neighbors caused by projection effects.
    
    Args:
        trajectory: 2D array of shape (n_points, n_dims) containing the time series.
        embedding_dim_max: Maximum embedding dimension to test.
        threshold: Threshold multiplier for standard deviation to identify false neighbors.
        time_delay: Time delay for delay-coordinate embedding.
        
    Returns:
        tuple: (fnn_rates, metadata_dict)
            - fnn_rates: List of FNN rates for each embedding dimension
            - metadata_dict: Contains details about the computation
    """
    n_points = trajectory.shape[0]
    n_dims = trajectory.shape[1]
    
    fnn_rates = []
    metadata = {
        "embedding_dims": list(range(1, embedding_dim_max + 1)),
        "threshold": threshold,
        "time_delay": time_delay
    }
    
    # Precompute standard deviation of the trajectory
    std_dev = np.std(trajectory)
    
    for d in range(1, embedding_dim_max + 1):
        if d * time_delay >= n_points:
            logger.warning(f"Embedding dimension {d} requires at least {d * time_delay} points, "
                         f"but trajectory has only {n_points}. Skipping.")
            fnn_rates.append(1.0)  # Max FNN rate for invalid dimensions
            continue
        
        # Create embedded vectors for dimension d
        embedded = np.zeros((n_points - d * time_delay, d * n_dims))
        for i in range(d):
            start_idx = i * time_delay
            end_idx = start_idx + n_points - d * time_delay
            embedded[:, i * n_dims:(i + 1) * n_dims] = trajectory[start_idx:end_idx]
        
        n_embedded = embedded.shape[0]
        
        # Find nearest neighbors in d-dimensional space
        distances_d = cdist(embedded, embedded, metric='euclidean')
        
        # Find nearest neighbor for each point (excluding self)
        nearest_indices = []
        for i in range(n_embedded):
            dists = distances_d[i].copy()
            dists[i] = np.inf
            nearest_idx = np.argmin(dists)
            nearest_indices.append(nearest_idx)
        
        # Check for false neighbors in (d+1)-dimensional space
        if d < embedding_dim_max:
            # Create embedded vectors for dimension d+1
            embedded_d1 = np.zeros((n_points - (d + 1) * time_delay, (d + 1) * n_dims))
            for i in range(d + 1):
                start_idx = i * time_delay
                end_idx = start_idx + n_points - (d + 1) * time_delay
                embedded_d1[:, i * n_dims:(i + 1) * n_dims] = trajectory[start_idx:end_idx]
            
            distances_d1 = cdist(embedded_d1, embedded_d1, metric='euclidean')
            
            false_count = 0
            total_count = 0
            
            for i in range(n_embedded):
                if i + time_delay >= n_embedded:
                    continue
                
                j = nearest_indices[i]
                if j + time_delay >= n_embedded:
                    continue
                
                # Distance in d+1 dimensions
                dist_d1 = distances_d1[i + time_delay, j + time_delay]
                dist_d = distances_d[i, j]
                
                # Check if neighbor becomes false in higher dimension
                # Criterion: distance increases significantly
                if dist_d > 0 and dist_d1 / dist_d > threshold * std_dev:
                    false_count += 1
                total_count += 1
            
            if total_count > 0:
                fnn_rate = false_count / total_count
            else:
                fnn_rate = 1.0
        else:
            # For the last dimension, we can't compute FNN rate
            fnn_rate = 0.0
        
        fnn_rates.append(fnn_rate)
    
    metadata["fnn_rates"] = fnn_rates
    return fnn_rates, metadata

def compute_ground_truth_metrics(
    trajectory: Trajectory,
    seed: int,
    system_type: str,
    output_dir: str = "data/processed"
) -> Dict[str, Any]:
    """
    Compute ground truth metrics for a clean trajectory.
    
    This function computes the correlation dimension, Lyapunov exponent,
    and false nearest neighbors for a clean trajectory and saves the results
    to a JSON file.
    
    Args:
        trajectory: Trajectory object containing the clean time series data.
        seed: Random seed used for trajectory generation.
        system_type: Type of system (e.g., 'lorenz', 'rossler').
        output_dir: Directory to save the results.
        
    Returns:
        dict: Dictionary containing the computed metrics and metadata.
    """
    # Convert trajectory to numpy array
    trajectory_data = np.array(trajectory.data)
    
    # Compute metrics
    logger.info(f"Computing correlation dimension for {system_type} seed {seed}")
    d2, d2_meta = compute_correlation_dimension(trajectory_data)
    
    logger.info(f"Computing Lyapunov exponent for {system_type} seed {seed}")
    lyap, lyap_meta = compute_lyapunov_exponent_rosenstein(trajectory_data)
    
    logger.info(f"Computing FNN for {system_type} seed {seed}")
    fnn_rates, fnn_meta = compute_false_nearest_neighbors(trajectory_data)
    
    # Find the minimum embedding dimension where FNN rate drops below 0.01
    min_embedding_dim = len(fnn_rates)
    for i, rate in enumerate(fnn_rates):
        if rate < 0.01:
            min_embedding_dim = i + 1
            break
    
    # Compile results
    results = {
        "seed": seed,
        "system_type": system_type,
        "correlation_dimension": d2,
        "correlation_dimension_metadata": d2_meta,
        "lyapunov_exponent": lyap,
        "lyapunov_exponent_metadata": lyap_meta,
        "fnn_rates": fnn_rates,
        "fnn_metadata": fnn_meta,
        "min_embedding_dim": min_embedding_dim,
        "trajectory_length": trajectory_data.shape[0],
        "trajectory_dimensions": trajectory_data.shape[1]
    }
    
    # Save results to JSON file
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, f"ground_truth_metrics_{seed}.json")
    
    with open(output_file, 'w') as f:
        json.dump(results, f, indent=2)
    
    logger.info(f"Ground truth metrics saved to {output_file}")
    
    return results

def run_ground_truth_computation(
    clean_trajectories_dir: str = "data/raw",
    output_dir: str = "data/processed"
) -> List[Dict[str, Any]]:
    """
    Run ground truth metric computation for all clean trajectories.
    
    Args:
        clean_trajectories_dir: Directory containing clean trajectory CSV files.
        output_dir: Directory to save the results.
        
    Returns:
        list: List of dictionaries containing the computed metrics for each trajectory.
    """
    # Find all clean trajectory files
    trajectory_files = []
    for file in os.listdir(clean_trajectories_dir):
        if file.startswith("clean_") and file.endswith(".csv"):
            trajectory_files.append(os.path.join(clean_trajectories_dir, file))
    
    if not trajectory_files:
        logger.warning(f"No clean trajectory files found in {clean_trajectories_dir}")
        return []
    
    results = []
    
    for trajectory_file in trajectory_files:
        # Extract seed and system type from filename
        filename = os.path.basename(trajectory_file)
        # Expected format: {system_type}_clean_{seed}.csv
        parts = filename.replace(".csv", "").split("_")
        if len(parts) >= 3:
            system_type = parts[0]
            seed = int(parts[-1])
        else:
            logger.warning(f"Cannot parse filename {filename}, skipping")
            continue
        
        # Load trajectory data
        try:
            data = np.loadtxt(trajectory_file, delimiter=',', skiprows=1)
            trajectory = Trajectory(
                data=data,
                system_type=system_type,
                seed=seed,
                t0=0.0,
                t1=data.shape[0] * 0.01,  # Assuming dt=0.01
                dt=0.01
            )
            
            # Compute metrics
            result = compute_ground_truth_metrics(trajectory, seed, system_type, output_dir)
            results.append(result)
            
        except Exception as e:
            logger.error(f"Error processing {trajectory_file}: {e}")
            continue
    
    return results

def get_metric_computation_functions() -> Dict[str, callable]:
    """
    Get a dictionary of metric computation functions.
    
    Returns:
        dict: Dictionary mapping metric names to their computation functions.
    """
    return {
        "correlation_dimension": compute_correlation_dimension,
        "lyapunov_exponent_rosenstein": compute_lyapunov_exponent_rosenstein,
        "false_nearest_neighbors": compute_false_nearest_neighbors,
        "ground_truth_metrics": compute_ground_truth_metrics
    }