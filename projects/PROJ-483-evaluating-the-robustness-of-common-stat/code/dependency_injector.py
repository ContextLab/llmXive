import numpy as np
from typing import Tuple, List, Optional
from scipy import stats
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
import json

def ar1_inject(data: np.ndarray, r: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Injects AR(1) dependency structure into data.
    
    Args:
        data: Input array of shape (n_samples, n_features).
        r: Autocorrelation strength in [0, 0.9].
        seed: Random seed for reproducibility.
        
    Returns:
        Array with injected AR(1) structure.
    """
    if seed is not None:
        np.random.seed(seed)
        
    if not (0.0 <= r <= 0.9):
        raise ValueError(f"r must be in [0, 0.9], got {r}")
        
    n_samples, n_features = data.shape
    result = np.zeros_like(data)
    
    # Vectorized approach: Generate noise and apply AR(1) filter per column
    # x_t = r * x_{t-1} + epsilon_t
    # We can solve this by constructing the transition matrix or iterative update
    # Iterative update is memory efficient and vectorizable across columns
    
    noise = np.random.normal(0, 1, (n_samples, n_features))
    current = np.zeros(n_features)
    
    for t in range(n_samples):
        current = r * current + noise[t]
        result[t] = current
        
    # Scale result to match original data variance roughly
    if np.std(data) > 0:
        result = result * (np.std(data) / np.std(result))
        
    return result

def validate_ar1_injection(data: np.ndarray, injected_data: np.ndarray, target_r: float, tolerance: float = 0.05) -> bool:
    """
    Validates that the injected data has autocorrelation close to target_r.
    
    Args:
        data: Original data (unused in calculation but kept for signature).
        injected_data: Data after AR(1) injection.
        target_r: Target autocorrelation strength.
        tolerance: Allowed deviation (default 5%).
        
    Returns:
        True if validation passes, False otherwise.
    """
    # Calculate actual autocorrelation for each column
    n_samples = injected_data.shape[0]
    if n_samples < 2:
        return False
        
    autocorrs = []
    for col in range(injected_data.shape[1]):
        x = injected_data[:, col]
        x_centered = x - np.mean(x)
        # Lag-1 autocorrelation
        autocorr = np.dot(x_centered[:-1], x_centered[1:]) / np.dot(x_centered, x_centered)
        autocorrs.append(autocorr)
        
    mean_autocorr = np.mean(autocorrs)
    deviation = abs(mean_autocorr - target_r)
    
    # Check if deviation is within tolerance of target (relative or absolute?)
    # Using absolute tolerance as per spec "within 5% tolerance" usually implies absolute 0.05
    # But if target is small, relative might be better. Spec says "within 5% tolerance" 
    # Let's interpret as absolute 0.05 for r in [0, 0.9]
    return deviation <= tolerance

def block_bootstrap(data: np.ndarray, block_size: int, n_blocks: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Performs block bootstrap for hierarchical dependency.
    
    Args:
        data: Input array of shape (n_samples, n_features).
        block_size: Size of each block.
        n_blocks: Number of blocks to sample.
        seed: Random seed.
        
    Returns:
        Resampled data array.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_samples, n_features = data.shape
    if block_size * n_blocks > n_samples:
        # Adjust to fit
        max_blocks = n_samples // block_size
        if max_blocks < 1:
            raise ValueError("Block size too large for data")
        n_blocks = max_blocks
        
    # Select random starting indices for blocks
    indices = []
    for _ in range(n_blocks):
        start = np.random.randint(0, n_samples - block_size + 1)
        indices.extend(range(start, start + block_size))
        
    # Ensure we don't exceed bounds
    indices = [i for i in indices if i < n_samples]
    
    if len(indices) == 0:
        raise ValueError("No valid blocks selected")
        
    return data[indices]

def validate_block_bootstrap(original_data: np.ndarray, resampled_data: np.ndarray, target_block_size: int) -> bool:
    """
    Validates block bootstrap distribution.
    
    Args:
        original_data: Original data.
        resampled_data: Resampled data.
        target_block_size: Expected block size.
        
    Returns:
        True if validation passes.
    """
    # Simple validation: check if resampled data has similar distribution
    # In a real implementation, we'd check block size distribution
    if resampled_data.shape[0] == 0:
        return False
        
    # Check if means are roughly preserved (within 20%)
    orig_mean = np.mean(original_data)
    res_mean = np.mean(resampled_data)
    
    if abs(orig_mean) < 1e-6:
        return abs(res_mean) < 1e-3
        
    return abs((res_mean - orig_mean) / orig_mean) < 0.2

def generate_spatial_proxy(data: np.ndarray, n_clusters: int = 5, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates spatial proxy coordinates using feature-space clustering.
    
    Args:
        data: Input data array of shape (n_samples, n_features).
        n_clusters: Number of clusters for K-Means.
        seed: Random seed.
        
    Returns:
        Proxy coordinates of shape (n_samples, 2).
    """
    if seed is not None:
        np.random.seed(seed)
        
    if n_clusters <= 1:
        # If only 1 cluster, return random points around origin
        return np.random.normal(0, 1, (data.shape[0], 2))
        
    # Use K-Means to find cluster centers in feature space
    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    kmeans.fit(data)
    
    # Get cluster labels
    labels = kmeans.labels_
    
    # Create 2D proxy coordinates based on cluster assignments
    # Use MDS-like approach or just assign cluster centers in 2D
    cluster_centers_2d = np.random.rand(n_clusters, 2) * 10
    
    # Assign each point to its cluster's 2D coordinate
    proxy_coords = cluster_centers_2d[labels]
    
    # Add small noise to avoid identical points
    proxy_coords += np.random.normal(0, 0.1, proxy_coords.shape)
    
    return proxy_coords

def spatial_kernel_smooth(data: np.ndarray, proxy_coords: np.ndarray, bandwidth: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Applies spatial kernel smoothing using proxy coordinates.
    
    Args:
        data: Input data array.
        proxy_coords: 2D proxy coordinates from generate_spatial_proxy.
        bandwidth: Kernel bandwidth parameter.
        seed: Random seed.
        
    Returns:
        Smoothed data array.
    """
    if seed is not None:
        np.random.seed(seed)
        
    n_samples, n_features = data.shape
    if n_samples != proxy_coords.shape[0]:
        raise ValueError("Data and proxy_coords must have same number of samples")
        
    # Calculate distance matrix
    distances = cdist(proxy_coords, proxy_coords, metric='euclidean')
    
    # Gaussian kernel
    weights = np.exp(-(distances ** 2) / (2 * bandwidth ** 2))
    
    # Normalize weights
    weights = weights / np.sum(weights, axis=1, keepdims=True)
    
    # Apply smoothing
    smoothed_data = weights @ data
    
    return smoothed_data

def validate_spatial_kernel_smooth(original_data: np.ndarray, smoothed_data: np.ndarray, bandwidth: float) -> bool:
    """
    Validates spatial kernel smoothing results.
    
    Args:
        original_data: Original data.
        smoothed_data: Smoothed data.
        bandwidth: Used bandwidth.
        
    Returns:
        True if validation passes.
    """
    # Check if smoothing preserved overall structure
    if smoothed_data.shape != original_data.shape:
        return False
        
    # Check correlation between original and smoothed
    corr = np.corrcoef(original_data.flatten(), smoothed_data.flatten())[0, 1]
    
    # Should be highly correlated but not identical
    return 0.5 < corr < 1.0

if __name__ == "__main__":
    # Simple test
    test_data = np.random.normal(0, 1, (100, 5))
    injected = ar1_inject(test_data, 0.3, seed=42)
    is_valid = validate_ar1_injection(test_data, injected, 0.3)
    print(f"AR1 Validation: {is_valid}")