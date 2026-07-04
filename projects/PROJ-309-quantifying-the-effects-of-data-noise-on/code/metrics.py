import numpy as np
from typing import Tuple, Optional, Dict, Any, List, Union
from scipy.spatial.distance import cdist
from scipy.interpolate import interp1d
import logging
from scipy.optimize import curve_fit
from utils.data_models import MetricResult

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def linear_func(x, a, b):
    """Simple linear function for fitting correlation integral scaling."""
    return a * x + b

def compute_correlation_dimension(trajectory: np.ndarray, 
                                embedding_dim: int = 5, 
                                min_dist: float = 0.01, 
                                max_dist: float = 1.0,
                                n_points: int = 1000) -> Tuple[float, Dict[str, Any]]:
    """
    Compute Correlation Dimension using Grassberger-Procaccia algorithm.
    
    Args:
        trajectory: 2D array of shape (n_samples, n_features)
        embedding_dim: Maximum embedding dimension to test
        min_dist: Minimum distance threshold
        max_dist: Maximum distance threshold
        n_points: Number of distance bins
        
    Returns:
        Tuple of (correlation_dimension, metadata_dict)
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(-1, 1)
        
    n_samples, n_features = trajectory.shape
    logger.info(f"Computing correlation dimension for {n_samples} points in {n_features}D space")
    
    # Create distance bins
    distances = np.logspace(np.log10(min_dist), np.log10(max_dist), n_points)
    
    correlation_integrals = []
    
    for d in range(1, embedding_dim + 1):
        # For simplicity, we use the original trajectory as the embedded space
        # In a full implementation, we would create time-delay embeddings
        if d > n_features:
            break
            
        # Compute pairwise distances
        dist_matrix = cdist(trajectory[:, :d], trajectory[:, :d], metric='euclidean')
        
        # Compute correlation integral C(r) for each distance bin
        C_r = []
        for r in distances:
            count = np.sum(dist_matrix < r) - n_samples  # Exclude self-distances
            C_r.append(count / (n_samples * (n_samples - 1)))
        
        correlation_integrals.append(C_r)
    
    # Fit scaling region to estimate dimension
    dimensions = []
    for i, C_r in enumerate(correlation_integrals):
        C_r = np.array(C_r)
        valid_mask = (C_r > 0) & (C_r < 1)
        if np.sum(valid_mask) < 5:
            continue
            
        log_r = np.log(distances[valid_mask])
        log_C = np.log(C_r[valid_mask])
        
        try:
            # Fit linear function in log-log space
            popt, _ = curve_fit(linear_func, log_r, log_C)
            dim = popt[0]  # Slope is the correlation dimension
            if dim > 0:
                dimensions.append(dim)
        except:
            continue
    
    if not dimensions:
        logger.warning("Could not compute correlation dimension")
        return 0.0, {"error": "No valid dimensions found"}
        
    avg_dim = np.mean(dimensions)
    return avg_dim, {"dimensions": dimensions, "embedding_max": embedding_dim}

def compute_lyapunov_exponent_rosenstein(trajectory: np.ndarray,
                                       embedding_dim: int = 10,
                                       time_delay: int = 10,
                                       min_neighbors: int = 10,
                                       max_time: int = 50) -> Tuple[float, Dict[str, Any]]:
    """
    Compute Largest Lyapunov Exponent using Rosenstein's algorithm.
    
    Args:
        trajectory: 2D array of shape (n_samples, n_features)
        embedding_dim: Embedding dimension for phase space reconstruction
        time_delay: Time delay for embedding
        min_neighbors: Minimum number of neighbors required
        max_time: Maximum time steps for divergence calculation
        
    Returns:
        Tuple of (lyapunov_exponent, metadata_dict)
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(-1, 1)
        
    n_samples = trajectory.shape[0]
    logger.info(f"Computing Lyapunov exponent for {n_samples} points")
    
    # Create time-delay embedding
    if time_delay * embedding_dim >= n_samples:
        logger.warning("Time delay and embedding dimension too large for data length")
        return 0.0, {"error": "Insufficient data for embedding"}
        
    embedded = np.zeros((n_samples - time_delay * embedding_dim, embedding_dim))
    for i in range(embedding_dim):
        embedded[:, i] = trajectory[i * time_delay : n_samples - (embedding_dim - i - 1) * time_delay].flatten()
    
    n_embedded = embedded.shape[0]
    if n_embedded < min_neighbors * 2:
        logger.warning("Not enough embedded points")
        return 0.0, {"error": "Insufficient embedded points"}
        
    # Find nearest neighbors for each point
    distances = cdist(embedded, embedded, metric='euclidean')
    np.fill_diagonal(distances, np.inf)
    
    # Select neighbors that are temporally separated by at least time_delay
    nearest_neighbors = []
    for i in range(n_embedded):
        # Find neighbors that are far enough in time
        valid_indices = np.where(np.abs(np.arange(n_embedded) - i) > time_delay)[0]
        if len(valid_indices) == 0:
            continue
            
        neighbor_distances = distances[i, valid_indices]
        neighbor_indices = valid_indices[np.argsort(neighbor_distances)[:min_neighbors]]
        
        if len(neighbor_indices) >= min_neighbors:
            nearest_neighbors.append(neighbor_indices)
    
    if not nearest_neighbors:
        logger.warning("No valid neighbors found")
        return 0.0, {"error": "No valid neighbors"}
        
    # Calculate divergence over time
    divergence = []
    times = np.arange(max_time)
    
    for i, neighbors in enumerate(nearest_neighbors):
        if len(neighbors) == 0:
            continue
            
        # Calculate distance evolution
        for t in times:
            if i + t >= n_embedded:
                break
                
            total_dist = 0
            count = 0
            for j in neighbors:
                if j + t >= n_embedded:
                    continue
                    
                dist = np.linalg.norm(embedded[i + t] - embedded[j + t])
                if dist > 0:
                    total_dist += np.log(dist)
                    count += 1
            
            if count > 0:
                divergence.append(total_dist / count)
            else:
                divergence.append(np.nan)
    
    divergence = np.array(divergence)
    if np.all(np.isnan(divergence)):
        return 0.0, {"error": "No valid divergence data"}
        
    # Average over all initial points
    avg_divergence = np.nanmean(divergence, axis=0)
    
    # Fit linear region to estimate Lyapunov exponent
    valid_mask = ~np.isnan(avg_divergence)
    if np.sum(valid_mask) < 5:
        return 0.0, {"error": "Insufficient valid divergence points"}
        
    try:
        # Fit in the linear region (typically first few time steps)
        fit_range = min(20, len(avg_divergence))
        popt, _ = curve_fit(linear_func, times[:fit_range][valid_mask[:fit_range]], 
                          avg_divergence[:fit_range][valid_mask[:fit_range]])
        lyap_exp = popt[0]
    except:
        lyap_exp = 0.0
        
    return lyap_exp, {"divergence": avg_divergence, "times": times[:len(avg_divergence)]}

def compute_false_nearest_neighbors(trajectory: np.ndarray,
                                   embedding_dim: int = 2,
                                   threshold: float = 10.0,
                                   time_delay: int = 10) -> Tuple[float, Dict[str, Any]]:
    """
    Compute False Nearest Neighbors (FNN) rate.
    
    This function determines the minimum embedding dimension required to
    unfold the attractor by identifying neighbors that appear close in
    lower dimensions but are far apart in higher dimensions.
    
    Args:
        trajectory: 2D array of shape (n_samples, n_features)
        embedding_dim: The embedding dimension to test (default=2 as per task)
        threshold: Threshold multiplier for standard deviation (default=10× std)
        time_delay: Time delay for embedding (default=10)
        
    Returns:
        Tuple of (fnn_rate, metadata_dict)
        
    Note:
        The threshold is set to 10× the standard deviation of the trajectory
        as specified in the task requirements.
    """
    if trajectory.ndim == 1:
        trajectory = trajectory.reshape(-1, 1)
        
    n_samples = trajectory.shape[0]
    logger.info(f"Computing FNN for embedding dimension {embedding_dim}")
    
    # Calculate standard deviation of the trajectory for threshold
    std_dev = np.std(trajectory)
    threshold_value = threshold * std_dev
    
    # Create time-delay embedding for current dimension
    if time_delay * embedding_dim >= n_samples:
        logger.warning("Time delay and embedding dimension too large for data length")
        return 1.0, {"error": "Insufficient data for embedding", "threshold_used": threshold_value}
    
    # Build embedded trajectory
    embedded = np.zeros((n_samples - time_delay * embedding_dim, embedding_dim))
    for i in range(embedding_dim):
        start_idx = i * time_delay
        end_idx = n_samples - (embedding_dim - i) * time_delay
        embedded[:, i] = trajectory[start_idx:end_idx].flatten()
    
    n_embedded = embedded.shape[0]
    if n_embedded < 2:
        return 1.0, {"error": "Not enough embedded points", "threshold_used": threshold_value}
    
    # Compute pairwise distances in current embedding
    distances_current = cdist(embedded, embedded, metric='euclidean')
    
    # Find nearest neighbors (excluding self and temporally close points)
    nearest_neighbor_dist = np.zeros(n_embedded)
    nearest_neighbor_idx = np.zeros(n_embedded, dtype=int)
    
    for i in range(n_embedded):
        # Exclude self and points too close in time
        valid_mask = np.ones(n_embedded, dtype=bool)
        valid_mask[i] = False
        valid_mask[max(0, i - time_delay):min(n_embedded, i + time_delay + 1)] = False
        
        if not np.any(valid_mask):
            nearest_neighbor_dist[i] = np.inf
            nearest_neighbor_idx[i] = -1
            continue
            
        dists = distances_current[i, valid_mask]
        min_idx = np.argmin(dists)
        actual_idx = np.where(valid_mask)[0][min_idx]
        
        nearest_neighbor_dist[i] = dists[min_idx]
        nearest_neighbor_idx[i] = actual_idx
    
    # Now test in embedding dimension + 1 to find false neighbors
    if time_delay * (embedding_dim + 1) >= n_samples:
        # Cannot test higher dimension, assume all are false neighbors
        fnn_count = n_embedded
        logger.warning(f"Cannot test dimension {embedding_dim + 1}, assuming all neighbors are false")
    else:
        # Create embedding for dimension + 1
        embedded_plus = np.zeros((n_samples - time_delay * (embedding_dim + 1), embedding_dim + 1))
        for i in range(embedding_dim + 1):
            start_idx = i * time_delay
            end_idx = n_samples - (embedding_dim + 1 - i) * time_delay
            embedded_plus[:, i] = trajectory[start_idx:end_idx].flatten()
        
        # Only consider points that exist in both embeddings
        min_len = min(n_embedded, embedded_plus.shape[0])
        embedded_current = embedded[:min_len]
        embedded_next = embedded_plus[:min_len]
        
        # Compute distances in higher dimension for the same neighbor pairs
        false_neighbor_count = 0
        
        for i in range(min_len):
            j = int(nearest_neighbor_idx[i])
            if j < 0 or j >= min_len:
                continue
                
            # Distance in current dimension
            d_current = nearest_neighbor_dist[i]
            if d_current == np.inf:
                continue
                
            # Distance in higher dimension
            d_next = np.linalg.norm(embedded_next[i] - embedded_next[j])
            
            # Check if neighbor is false in higher dimension
            # A neighbor is false if the distance increases significantly
            if d_next > threshold_value:
                false_neighbor_count += 1
    
        fnn_count = false_neighbor_count
    
    fnn_rate = fnn_count / n_embedded if n_embedded > 0 else 1.0
    
    metadata = {
        "embedding_dim": embedding_dim,
        "threshold": threshold,
        "threshold_value": threshold_value,
        "time_delay": time_delay,
        "false_neighbors": int(fnn_count),
        "total_neighbors": int(n_embedded),
        "fnn_rate": fnn_rate
    }
    
    logger.info(f"FNN rate: {fnn_rate:.4f} ({fnn_count}/{n_embedded})")
    return fnn_rate, metadata

def compute_ground_truth_metrics(trajectory: np.ndarray,
                                system_type: str = "lorenz",
                                seed: int = 42) -> Dict[str, MetricResult]:
    """
    Compute all ground truth metrics for a clean trajectory.
    
    Args:
        trajectory: 2D array of shape (n_samples, n_features)
        system_type: Type of system (lorenz, rossler)
        seed: Random seed for reproducibility
        
    Returns:
        Dictionary of metric names to MetricResult objects
    """
    results = {}
    
    # Correlation Dimension
    try:
        corr_dim, corr_meta = compute_correlation_dimension(trajectory)
        results["correlation_dimension"] = MetricResult(
            value=corr_dim,
            metadata=corr_meta,
            system_type=system_type,
            seed=seed
        )
    except Exception as e:
        logger.error(f"Failed to compute correlation dimension: {e}")
        results["correlation_dimension"] = MetricResult(
            value=0.0,
            metadata={"error": str(e)},
            system_type=system_type,
            seed=seed
        )
    
    # Lyapunov Exponent
    try:
        lyap_exp, lyap_meta = compute_lyapunov_exponent_rosenstein(trajectory)
        results["lyapunov_exponent"] = MetricResult(
            value=lyap_exp,
            metadata=lyap_meta,
            system_type=system_type,
            seed=seed
        )
    except Exception as e:
        logger.error(f"Failed to compute Lyapunov exponent: {e}")
        results["lyapunov_exponent"] = MetricResult(
            value=0.0,
            metadata={"error": str(e)},
            system_type=system_type,
            seed=seed
        )
    
    # False Nearest Neighbors (at embedding=2)
    try:
        fnn_rate, fnn_meta = compute_false_nearest_neighbors(trajectory, embedding_dim=2)
        results["false_nearest_neighbors"] = MetricResult(
            value=fnn_rate,
            metadata=fnn_meta,
            system_type=system_type,
            seed=seed
        )
    except Exception as e:
        logger.error(f"Failed to compute FNN: {e}")
        results["false_nearest_neighbors"] = MetricResult(
            value=1.0,
            metadata={"error": str(e)},
            system_type=system_type,
            seed=seed
        )
    
    return results

def run_ground_truth_computation(trajectory: np.ndarray,
                                system_type: str = "lorenz",
                                seed: int = 42) -> Dict[str, Any]:
    """
    Run all ground truth computations and return formatted results.
    
    Args:
        trajectory: 2D array of shape (n_samples, n_features)
        system_type: Type of system
        seed: Random seed
        
    Returns:
        Dictionary with all computed metrics
    """
    results = compute_ground_truth_metrics(trajectory, system_type, seed)
    
    formatted = {
        "system_type": system_type,
        "seed": seed,
        "metrics": {}
    }
    
    for metric_name, result in results.items():
        formatted["metrics"][metric_name] = {
            "value": float(result.value),
            "metadata": result.metadata
        }
    
    return formatted

def get_metric_computation_functions() -> Dict[str, callable]:
    """Return dictionary of available metric computation functions."""
    return {
        "correlation_dimension": compute_correlation_dimension,
        "lyapunov_exponent": compute_lyapunov_exponent_rosenstein,
        "false_nearest_neighbors": compute_false_nearest_neighbors,
        "ground_truth": compute_ground_truth_metrics
    }