import numpy as np
from typing import Tuple, Optional, Dict, Any, List
import logging
from scipy.spatial.distance import cdist
from scipy.stats import linregress
from code.config import FNN_THRESHOLD_FACTOR

logger = logging.getLogger(__name__)

def embed_trajectory(data: np.ndarray, delay: int = 1, dim: int = 2) -> np.ndarray:
    """
    Create a delay-coordinate embedding of a 1D time series.
    
    Args:
        data: 1D array of time series data
        delay: Time delay for embedding
        dim: Embedding dimension
        
    Returns:
        2D array of shape (N, dim) where N = len(data) - (dim-1)*delay
    """
    if data.ndim != 1:
        raise ValueError("Input data must be 1D")
        
    n_points = len(data)
    n_embedded = n_points - (dim - 1) * delay
    
    if n_embedded <= 0:
        raise ValueError(f"Cannot embed: data length {n_points} too small for dim={dim}, delay={delay}")
        
    embedded = np.zeros((n_embedded, dim), dtype=np.float64)
    
    for i in range(dim):
        start_idx = i * delay
        end_idx = start_idx + n_embedded
        embedded[:, i] = data[start_idx:end_idx]
        
    return embedded

def compute_false_nearest_neighbors(
    data: np.ndarray, 
    dim: int = 2, 
    delay: int = 1, 
    threshold_factor: float = 10.0
) -> Tuple[float, int]:
    """
    Compute the False Nearest Neighbors (FNN) rate for a given embedding dimension.
    
    This implements the standard FNN algorithm to detect when an embedding dimension
    is sufficient to unfold the attractor. Points that are neighbors in dimension 'dim'
    but not in dimension 'dim+1' are considered "false" neighbors.
    
    Args:
        data: 1D array of time series data
        dim: Current embedding dimension to test
        delay: Time delay for embedding
        threshold_factor: Factor multiplied by std dev to determine threshold
        
    Returns:
        Tuple of (fnn_rate, num_false_neighbors)
        fnn_rate is the fraction of points that are false neighbors (0.0 to 1.0)
    """
    if data.ndim != 1:
        raise ValueError("Input data must be 1D")
        
    # Compute standard deviation for threshold
    std_dev = np.std(data)
    if std_dev == 0:
        logger.warning("Data has zero standard deviation; FNN threshold will be 0")
        threshold = 0.0
    else:
        threshold = threshold_factor * std_dev
        
    logger.debug(f"FNN: dim={dim}, delay={delay}, threshold={threshold:.4f}")
    
    # Create embeddings for current dimension
    embedded_dim = embed_trajectory(data, delay=delay, dim=dim)
    n_points = embedded_dim.shape[0]
    
    if n_points < 2:
        logger.warning("Not enough points for FNN computation")
        return 1.0, n_points  # All points are false neighbors if we can't compare
        
    # Create embeddings for dimension+1
    embedded_dim_plus_1 = embed_trajectory(data, delay=delay, dim=dim + 1)
    
    # Compute distances to nearest neighbors in dim space
    # We use a simple approach: for each point, find its nearest neighbor
    # excluding itself and points within the Theiler window (temporal neighbors)
    theiler_window = delay * 2  # Standard choice: 2*delay
    
    fnn_count = 0
    valid_count = 0
    
    for i in range(n_points):
        # Find nearest neighbor in dim space
        distances = np.linalg.norm(embedded_dim - embedded_dim[i], axis=1)
        distances[i] = np.inf  # Exclude self
        
        # Exclude temporal neighbors (Theiler window)
        for j in range(max(0, i - theiler_window), min(n_points, i + theiler_window + 1)):
            if j != i:
                distances[j] = np.inf
                
        nearest_idx = np.argmin(distances)
        nearest_dist = distances[nearest_idx]
        
        if nearest_dist == np.inf:
            continue  # No valid neighbor found
            
        valid_count += 1
        
        # Check if this neighbor remains close in dim+1 space
        dist_dim_plus_1 = np.linalg.norm(
            embedded_dim_plus_1[i] - embedded_dim_plus_1[nearest_idx]
        )
        
        # Compute the increase in distance
        distance_increase = np.sqrt(dist_dim_plus_1**2 - nearest_dist**2)
        
        # If the distance increase exceeds threshold, it's a false neighbor
        if distance_increase > threshold:
            fnn_count += 1
            
    if valid_count == 0:
        logger.warning("No valid neighbors found for FNN computation")
        return 1.0, n_points
        
    fnn_rate = fnn_count / valid_count
    logger.debug(f"FNN: dim={dim}, rate={fnn_rate:.4f}, false_count={fnn_count}/{valid_count}")
    
    return fnn_rate, fnn_count

def compute_correlation_dimension(
    data: np.ndarray,
    dim_max: int = 10,
    delay: int = 1,
    min_points: int = 100
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the correlation dimension using the Grassberger-Procaccia algorithm.
    
    Args:
        data: 1D array of time series data
        dim_max: Maximum embedding dimension to test
        delay: Time delay for embedding
        min_points: Minimum number of points required
        
    Returns:
        Tuple of (correlation_dimension, metadata_dict)
    """
    if data.ndim != 1:
        raise ValueError("Input data must be 1D")
        
    n_points = len(data)
    if n_points < min_points:
        raise ValueError(f"Insufficient data points: {n_points} < {min_points}")
        
    logger.info(f"Computing correlation dimension for {n_points} points")
    
    # Embed trajectory
    embedded = embed_trajectory(data, delay=delay, dim=dim_max)
    
    # Compute pairwise distances
    distances = cdist(embedded, embedded, metric='euclidean')
    
    # For each embedding dimension, compute correlation sum
    log_r = []
    log_c = []
    
    for d in range(2, dim_max + 1):
        # Use first d dimensions
        embedded_d = embedded[:, :d]
        distances_d = cdist(embedded_d, embedded_d, metric='euclidean')
        
        # Compute correlation sum for various radii
        # Use a range of radii from small to large
        max_dist = np.max(distances_d)
        radii = np.logspace(np.log10(max_dist * 1e-3), np.log10(max_dist * 0.5), 20)
        
        c_values = []
        r_values = []
        
        for r in radii:
            # Count pairs with distance < r
            count = np.sum(distances_d < r)
            # Exclude self-pairs and temporal neighbors
            n = embedded_d.shape[0]
            theiler_window = delay * 2
            n_excluded = n * (2 * theiler_window + 1)  # Approximate
            n_pairs = n * (n - 1) / 2 - n_excluded / 2
            
            if n_pairs > 0:
                c = count / n_pairs
                if c > 0:
                    c_values.append(c)
                    r_values.append(r)
        
        if len(c_values) >= 3:
            # Fit linear region
            log_r.extend(np.log(r_values))
            log_c.extend(np.log(c_values))
    
    if len(log_r) < 3:
        logger.warning("Insufficient data for correlation dimension estimation")
        return -1.0, {"error": "insufficient_data"}
        
    # Fit line to log-log plot
    log_r = np.array(log_r)
    log_c = np.array(log_c)
    
    # Select linear region (middle 50% of data)
    idx_start = len(log_r) // 4
    idx_end = 3 * len(log_r) // 4
    
    slope, intercept, r_value, p_value, std_err = linregress(
        log_r[idx_start:idx_end], 
        log_c[idx_start:idx_end]
    )
    
    logger.info(f"Correlation dimension: {slope:.4f} (R²={r_value**2:.4f})")
    
    metadata = {
        "slope": slope,
        "intercept": intercept,
        "r_squared": r_value**2,
        "p_value": p_value,
        "std_error": std_err,
        "n_points": n_points,
        "embedding_dim_max": dim_max,
        "delay": delay
    }
    
    return slope, metadata

def compute_lyapunov_exponent_rosenstein(
    data: np.ndarray,
    dim: int = 5,
    delay: int = 1,
    min_separation: int = 10,
    max_time: int = 100
) -> Tuple[float, Dict[str, Any]]:
    """
    Compute the largest Lyapunov exponent using Rosenstein's algorithm.
    
    Args:
        data: 1D array of time series data
        dim: Embedding dimension
        delay: Time delay for embedding
        min_separation: Minimum temporal separation for neighbor search
        max_time: Maximum evolution time for divergence measurement
        
    Returns:
        Tuple of (lyapunov_exponent, metadata_dict)
    """
    if data.ndim != 1:
        raise ValueError("Input data must be 1D")
        
    n_points = len(data)
    if n_points < 100:
        raise ValueError("Insufficient data points for Lyapunov exponent")
        
    logger.info("Computing largest Lyapunov exponent (Rosenstein)")
    
    # Embed trajectory
    embedded = embed_trajectory(data, delay=delay, dim=dim)
    
    # Find nearest neighbors for each point
    distances = cdist(embedded, embedded, metric='euclidean')
    
    # For each point, find nearest neighbor that is temporally separated
    neighbors = []
    initial_distances = []
    
    for i in range(n_points - dim * delay):
        # Find nearest neighbor with sufficient temporal separation
        min_dist = np.inf
        nearest_idx = -1
        
        for j in range(n_points - dim * delay):
            if abs(i - j) > min_separation:
                dist = distances[i, j]
                if dist < min_dist:
                    min_dist = dist
                    nearest_idx = j
                    
        if nearest_idx != -1 and min_dist > 0:
            neighbors.append(nearest_idx)
            initial_distances.append(min_dist)
    
    if len(neighbors) == 0:
        logger.warning("No valid neighbors found for Lyapunov computation")
        return -1.0, {"error": "no_neighbors"}
        
    # Compute divergence over time
    divergence = []
    time_steps = list(range(max_time))
    
    for t in time_steps:
        avg_divergence = 0
        count = 0
        
        for i, neighbor in enumerate(neighbors):
            j = i + t
            k = neighbor + t
            
            if j < embedded.shape[0] and k < embedded.shape[0]:
                dist = np.linalg.norm(embedded[j] - embedded[k])
                if dist > 0:
                    avg_divergence += np.log(dist / initial_distances[i])
                    count += 1
                    
        if count > 0:
            divergence.append(avg_divergence / count)
    
    if len(divergence) < 3:
        logger.warning("Insufficient divergence data points")
        return -1.0, {"error": "insufficient_divergence"}
        
    # Fit linear region to find Lyapunov exponent
    # Use first 1/3 of the time series for linear fit
    fit_end = max(3, len(divergence) // 3)
    
    slope, intercept, r_value, p_value, std_err = linregress(
        time_steps[:fit_end],
        divergence[:fit_end]
    )
    
    logger.info(f"Largest Lyapunov exponent: {slope:.6f} (R²={r_value**2:.4f})")
    
    metadata = {
        "exponent": slope,
        "r_squared": r_value**2,
        "p_value": p_value,
        "std_error": std_err,
        "n_neighbors": len(neighbors),
        "embedding_dim": dim,
        "delay": delay
    }
    
    return slope, metadata

def compute_all_metrics(
    data: np.ndarray,
    fnn_dim: int = 2,
    fnn_threshold: float = 10.0
) -> Dict[str, Any]:
    """
    Compute all metrics for a given time series.
    
    Args:
        data: 1D array of time series data
        fnn_dim: Embedding dimension for FNN computation
        fnn_threshold: Threshold factor for FNN (default 10.0)
        
    Returns:
        Dictionary containing all computed metrics
    """
    results = {}
    
    # Compute FNN
    fnn_rate, fnn_count = compute_false_nearest_neighbors(
        data, 
        dim=fnn_dim, 
        threshold_factor=fnn_threshold
    )
    results['fnn'] = {
        'rate': fnn_rate,
        'count': fnn_count,
        'embedding_dim': fnn_dim
    }
    
    # Compute Correlation Dimension
    try:
        corr_dim, corr_meta = compute_correlation_dimension(data)
        results['correlation_dimension'] = {
            'value': corr_dim,
            'metadata': corr_meta
        }
    except Exception as e:
        logger.warning(f"Correlation dimension computation failed: {e}")
        results['correlation_dimension'] = {'value': None, 'error': str(e)}
        
    # Compute Lyapunov Exponent
    try:
        lyap_exp, lyap_meta = compute_lyapunov_exponent_rosenstein(data)
        results['lyapunov_exponent'] = {
            'value': lyap_exp,
            'metadata': lyap_meta
        }
    except Exception as e:
        logger.warning(f"Lyapunov exponent computation failed: {e}")
        results['lyapunov_exponent'] = {'value': None, 'error': str(e)}
        
    return results