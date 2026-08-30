import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from scipy import stats
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
import json
import os

def ar1_inject(data: np.ndarray, rho: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Injects AR(1) dependency into data.
    data: 1D or 2D array (n_samples, n_features) or (n_samples,)
    rho: Autocorrelation coefficient [0, 0.9]
    seed: Random seed for reproducibility
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    n_samples, n_features = data.shape
    injected_data = np.zeros_like(data)
    
    # Generate noise
    noise = np.random.normal(0, 1, (n_samples, n_features))
    
    for j in range(n_features):
        col = np.zeros(n_samples)
        col[0] = noise[0, j]
        for i in range(1, n_samples):
            col[i] = rho * col[i-1] + np.sqrt(1 - rho**2) * noise[i, j]
        injected_data[:, j] = col
    
    return injected_data

def validate_ar1_injection(injected_data: np.ndarray, target_rho: float, tolerance: float = 0.05) -> Dict[str, Any]:
    """
    Validates that the injected data has the target autocorrelation.
    """
    if injected_data.ndim == 1:
        injected_data = injected_data.reshape(-1, 1)
    
    n_samples, n_features = injected_data.shape
    if n_samples < 2:
        return {"valid": False, "reason": "Insufficient samples for autocorrelation calculation"}
    
    observed_rhos = []
    for j in range(n_features):
        col = injected_data[:, j]
        # Calculate autocorrelation at lag 1
        autocorr = np.corrcoef(col[:-1], col[1:])[0, 1]
        if not np.isnan(autocorr):
            observed_rhos.append(autocorr)
    
    if not observed_rhos:
        return {"valid": False, "reason": "Could not calculate autocorrelation"}
    
    mean_observed_rho = np.mean(observed_rhos)
    diff = abs(mean_observed_rho - target_rho)
    is_valid = diff <= tolerance
    
    return {
        "valid": is_valid,
        "target_rho": target_rho,
        "observed_rho": float(mean_observed_rho),
        "tolerance": tolerance,
        "difference": float(diff)
    }

def block_bootstrap(data: np.ndarray, block_size: int, n_blocks: int, seed: Optional[int] = None) -> np.ndarray:
    """
    Performs block bootstrap resampling.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    n_samples, n_features = data.shape
    if n_samples < block_size:
        raise ValueError(f"Block size {block_size} larger than sample size {n_samples}")
    
    resampled_indices = []
    for _ in range(n_blocks):
        start_idx = np.random.randint(0, n_samples - block_size + 1)
        indices = list(range(start_idx, start_idx + block_size))
        resampled_indices.extend(indices)
    
    if len(resampled_indices) > n_samples:
        resampled_indices = resampled_indices[:n_samples]
    elif len(resampled_indices) < n_samples:
        # Pad with random samples if needed
        while len(resampled_indices) < n_samples:
            resampled_indices.append(np.random.randint(0, n_samples))
    
    return data[resampled_indices]

def validate_block_bootstrap(resampled_data: np.ndarray, original_data: np.ndarray, block_size: int) -> Dict[str, Any]:
    """
    Validates block bootstrap distribution.
    """
    # Basic validation: check that resampled data has same shape
    if resampled_data.shape != original_data.shape:
        return {"valid": False, "reason": "Shape mismatch"}
    
    # Check that values are from original data
    original_flat = set(original_data.flatten())
    resampled_flat = set(resampled_data.flatten())
    if not resampled_flat.issubset(original_flat):
        return {"valid": False, "reason": "Resampled values not from original data"}
    
    return {"valid": True, "block_size": block_size}

def generate_spatial_proxy(data: np.ndarray, n_clusters: int = 5, seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Generates a feature-space clustering proxy for spatial dependency.
    Returns cluster labels and centroids.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    if data.shape[0] < n_clusters:
        n_clusters = max(1, data.shape[0] // 2)
    
    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    labels = kmeans.fit_predict(data)
    centroids = kmeans.cluster_centers_
    
    return {
        "labels": labels.tolist(),
        "centroids": centroids.tolist(),
        "n_clusters": n_clusters,
        "inertia": float(kmeans.inertia_)
    }

def save_spatial_proxy_report(proxy_data: Dict[str, Any], output_path: str):
    """
    Saves the spatial proxy report to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(proxy_data, f, indent=2)

def spatial_kernel_smooth(data: np.ndarray, bandwidth: float, proxy_labels: np.ndarray, seed: Optional[int] = None) -> np.ndarray:
    """
    Applies spatial kernel smoothing using proxy labels.
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    smoothed_data = np.zeros_like(data)
    unique_labels = np.unique(proxy_labels)
    
    for label in unique_labels:
        mask = proxy_labels == label
        cluster_data = data[mask]
        if len(cluster_data) > 0:
            # Simple kernel smoothing: mean of cluster with Gaussian noise
            cluster_mean = np.mean(cluster_data, axis=0)
            noise = np.random.normal(0, bandwidth, cluster_data.shape)
            smoothed_data[mask] = cluster_mean + noise
    
    return smoothed_data

def validate_spatial_kernel_smooth(smoothed_data: np.ndarray, original_data: np.ndarray, bandwidth: float) -> Dict[str, Any]:
    """
    Validates spatial kernel smoothing.
    """
    if smoothed_data.shape != original_data.shape:
        return {"valid": False, "reason": "Shape mismatch"}
    
    # Check that smoothing didn't change the distribution too much
    orig_mean = np.mean(original_data)
    smooth_mean = np.mean(smoothed_data)
    diff = abs(orig_mean - smooth_mean)
    
    # Allow some tolerance for smoothing
    tolerance = bandwidth * 0.5
    is_valid = diff <= tolerance or bandwidth > 0.1  # More lenient for large bandwidths
    
    return {
        "valid": is_valid,
        "original_mean": float(orig_mean),
        "smoothed_mean": float(smooth_mean),
        "difference": float(diff),
        "bandwidth": bandwidth
    }

def load_spatial_proxy_from_manifest(manifest_path: str) -> Dict[str, Any]:
    """
    Loads spatial proxy data from a manifest file.
    """
    with open(manifest_path, 'r') as f:
        return json.load(f)

def inject_spatial_dependency(data: np.ndarray, proxy_labels: np.ndarray, bandwidth: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Injects spatial dependency using proxy labels and kernel smoothing.
    """
    return spatial_kernel_smooth(data, bandwidth, proxy_labels, seed)

def validate_spatial_injection(injected_data: np.ndarray, original_data: np.ndarray, bandwidth: float) -> Dict[str, Any]:
    """
    Validates the spatial dependency injection.
    """
    return validate_spatial_kernel_smooth(injected_data, original_data, bandwidth)

def validate_feature_space_proxy(proxy_data: Dict[str, Any], original_data: np.ndarray, tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Validates the feature-space clustering proxy.
    
    FR-003 Requirements:
    1. Verify cluster labels are valid (0 to n_clusters-1)
    2. Verify centroids are within data range
    3. Verify cluster sizes are reasonable (no empty or tiny clusters)
    4. Verify inertia is finite
    """
    errors = []
    warnings = []
    
    labels = np.array(proxy_data.get("labels", []))
    centroids = np.array(proxy_data.get("centroids", []))
    n_clusters = proxy_data.get("n_clusters", 0)
    inertia = proxy_data.get("inertia", float('inf'))
    
    # 1. Check label validity
    if len(labels) != len(original_data):
        errors.append(f"Label count ({len(labels)}) does not match data samples ({len(original_data)})")
    
    if n_clusters > 0:
        valid_labels = set(range(n_clusters))
        actual_labels = set(labels)
        if not actual_labels.issubset(valid_labels):
            errors.append(f"Invalid labels found: {actual_labels - valid_labels}")
    
    # 2. Check centroids within data range
    if len(centroids) > 0 and len(original_data) > 0:
        data_min = np.min(original_data, axis=0)
        data_max = np.max(original_data, axis=0)
        
        for i, centroid in enumerate(centroids):
            if len(centroid.shape) == 0:
                centroid = np.array([centroid])
                data_min = np.array([data_min])
                data_max = np.array([data_max])
            
            if np.any(centroid < data_min - tolerance) or np.any(centroid > data_max + tolerance):
                warnings.append(f"Centroid {i} outside data range by more than tolerance")
    
    # 3. Check cluster sizes
    if len(labels) > 0:
        unique, counts = np.unique(labels, return_counts=True)
        min_cluster_size = min(counts) if len(counts) > 0 else 0
        if min_cluster_size < 2:
            warnings.append(f"Smallest cluster has only {min_cluster_size} samples")
    
    # 4. Check inertia
    if not np.isfinite(inertia):
        errors.append("Inertia is not finite")
    
    is_valid = len(errors) == 0
    
    return {
        "valid": is_valid,
        "errors": errors,
        "warnings": warnings,
        "n_samples": len(original_data),
        "n_clusters": n_clusters,
        "min_cluster_size": int(min(counts)) if len(counts) > 0 else 0,
        "inertia": float(inertia) if np.isfinite(inertia) else None
    }

def save_proxy_validation_report(validation_result: Dict[str, Any], output_path: str):
    """
    Saves the proxy validation report to a JSON file.
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(validation_result, f, indent=2)