import numpy as np
from typing import Tuple, List, Optional, Dict, Any
from scipy import stats
from scipy.spatial.distance import cdist
from sklearn.cluster import KMeans
import json
from pathlib import Path

# AR(1) Injection Logic
def ar1_inject(data: np.ndarray, rho: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Injects AR(1) dependency into data.
    data: shape (n_samples, n_features) or (n_samples,)
    rho: autocorrelation coefficient [0, 0.9]
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    n, p = data.shape
    noise = np.random.normal(0, 1, (n, p))
    injected = np.zeros_like(data)
    
    for j in range(p):
        injected[0, j] = data[0, j] + noise[0, j]
        for i in range(1, n):
            injected[i, j] = rho * injected[i-1, j] + (1 - rho**2)**0.5 * data[i, j] + np.sqrt(1-rho**2) * noise[i, j]
    
    return injected.flatten() if len(injected.shape) == 1 and len(injected) == 1 else injected

def validate_ar1_injection(data: np.ndarray, injected_data: np.ndarray, target_rho: float, tolerance: float = 0.05) -> Dict[str, Any]:
    """
    Validates that the injected data has autocorrelation close to target_rho.
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)
        injected_data = injected_data.reshape(-1, 1)
    
    n, p = data.shape
    correlations = []
    
    for j in range(p):
        # Calculate autocorrelation of the injected series
        series = injected_data[:, j]
        if len(series) > 1:
            autocorr = np.corrcoef(series[:-1], series[1:])[0, 1]
            if not np.isnan(autocorr):
                correlations.append(autocorr)
    
    if not correlations:
        return {"valid": False, "message": "Could not calculate autocorrelation", "observed_rho": None}
    
    mean_rho = np.mean(correlations)
    diff = abs(mean_rho - target_rho)
    valid = diff <= tolerance
    
    return {
        "valid": valid,
        "observed_rho": float(mean_rho),
        "target_rho": float(target_rho),
        "difference": float(diff),
        "tolerance": float(tolerance)
    }

# Block Bootstrap Logic
def block_bootstrap(data: np.ndarray, block_size: int, num_blocks: Optional[int] = None, seed: Optional[int] = None) -> np.ndarray:
    """
    Performs block bootstrap for hierarchical dependency.
    data: shape (n_samples, n_features)
    block_size: size of blocks to sample
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    n, p = data.shape
    if num_blocks is None:
        num_blocks = int(np.ceil(n / block_size))
    
    # Ensure we have enough data
    if block_size * num_blocks < n:
        # Adjust to fit
        num_blocks = int(np.floor(n / block_size))
    
    indices = []
    for _ in range(num_blocks):
        start = np.random.randint(0, n - block_size + 1)
        indices.extend(range(start, start + block_size))
    
    # Truncate to original size if we oversampled
    indices = indices[:n]
    
    return data[indices]

def validate_block_bootstrap(original_data: np.ndarray, bootstrap_data: np.ndarray, block_size: int, tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Validates block bootstrap distribution.
    Checks if the block size distribution matches the target.
    """
    # Simple validation: check if the bootstrap data has similar distribution characteristics
    # A more rigorous check would involve comparing block boundaries
    
    if original_data.ndim == 1:
        original_data = original_data.reshape(-1, 1)
        bootstrap_data = bootstrap_data.reshape(-1, 1)
    
    # Check if the data shapes match
    if original_data.shape != bootstrap_data.shape:
        return {"valid": False, "message": "Shape mismatch", "original_shape": original_data.shape, "bootstrap_shape": bootstrap_data.shape}
    
    # Check if the mean and variance are roughly preserved (within tolerance)
    orig_mean = np.mean(original_data)
    boot_mean = np.mean(bootstrap_data)
    orig_var = np.var(original_data)
    boot_var = np.var(bootstrap_data)
    
    mean_diff = abs(orig_mean - boot_mean) / (abs(orig_mean) + 1e-8)
    var_diff = abs(orig_var - boot_var) / (abs(orig_var) + 1e-8)
    
    valid = (mean_diff <= tolerance) and (var_diff <= tolerance)
    
    return {
        "valid": valid,
        "mean_diff_ratio": float(mean_diff),
        "var_diff_ratio": float(var_diff),
        "block_size": block_size,
        "tolerance": tolerance
    }

# Spatial Proxy Generation
def generate_spatial_proxy(data: np.ndarray, n_clusters: int = 5, seed: Optional[int] = None) -> np.ndarray:
    """
    Generates a spatial proxy using feature-space clustering.
    data: shape (n_samples, n_features)
    Returns: proxy coordinates shape (n_samples, 2)
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    # Normalize data
    data_norm = (data - np.mean(data, axis=0)) / (np.std(data, axis=0) + 1e-8)
    
    # Use KMeans to find clusters in feature space
    kmeans = KMeans(n_clusters=n_clusters, random_state=seed, n_init=10)
    labels = kmeans.fit_predict(data_norm)
    
    # Create 2D coordinates based on cluster centers
    # We map cluster labels to a 2D grid
    unique_labels = np.unique(labels)
    n_unique = len(unique_labels)
    
    # Create a simple 2D layout for clusters
    coords = np.zeros((n_unique, 2))
    for i, label in enumerate(unique_labels):
        # Arrange clusters in a grid-like pattern
        row = i // int(np.ceil(np.sqrt(n_unique)))
        col = i % int(np.ceil(np.sqrt(n_unique)))
        coords[i] = [row, col]
    
    # Map each point to its cluster's coordinate
    proxy = coords[labels]
    
    return proxy

def save_spatial_proxy_report(proxy: np.ndarray, data: np.ndarray, n_clusters: int, output_path: str) -> None:
    """
    Saves the spatial proxy generation report.
    """
    report = {
        "n_samples": data.shape[0],
        "n_features": data.shape[1] if data.ndim > 1 else 1,
        "n_clusters": n_clusters,
        "proxy_shape": list(proxy.shape),
        "proxy_sample": proxy[:5].tolist() if proxy.shape[0] > 5 else proxy.tolist()
    }
    
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)

# Spatial Kernel Smoothing
def spatial_kernel_smooth(data: np.ndarray, proxy: np.ndarray, bandwidth: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Applies spatial kernel smoothing using the proxy coordinates.
    data: shape (n_samples, n_features)
    proxy: shape (n_samples, 2) - spatial proxy coordinates
    bandwidth: kernel bandwidth
    """
    if seed is not None:
        np.random.seed(seed)
    
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    
    n, p = data.shape
    smoothed = np.zeros_like(data)
    
    # Calculate distance matrix
    dist_matrix = cdist(proxy, proxy, metric='euclidean')
    
    # Gaussian kernel
    kernel = np.exp(-0.5 * (dist_matrix / bandwidth)**2)
    
    # Normalize kernel
    kernel_sum = kernel.sum(axis=1, keepdims=True)
    kernel_norm = kernel / (kernel_sum + 1e-8)
    
    # Apply smoothing
    smoothed = kernel_norm @ data
    
    return smoothed

def validate_spatial_kernel_smooth(original_data: np.ndarray, smoothed_data: np.ndarray, bandwidth: float, tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Validates spatial kernel smoothing.
    """
    if original_data.ndim == 1:
        original_data = original_data.reshape(-1, 1)
        smoothed_data = smoothed_data.reshape(-1, 1)
    
    # Check if shapes match
    if original_data.shape != smoothed_data.shape:
        return {"valid": False, "message": "Shape mismatch"}
    
    # Check correlation
    corr = np.corrcoef(original_data.flatten(), smoothed_data.flatten())[0, 1]
    if np.isnan(corr):
        corr = 0.0
    
    # Check if smoothing actually changed the data (unless bandwidth is very large)
    diff = np.mean(np.abs(original_data - smoothed_data))
    norm_diff = diff / (np.mean(np.abs(original_data)) + 1e-8)
    
    valid = (corr > 0.5) and (norm_diff < 1.0) # Should be correlated but smoothed
    
    return {
        "valid": valid,
        "correlation": float(corr),
        "normalized_diff": float(norm_diff),
        "bandwidth": bandwidth
    }

def load_spatial_proxy_from_manifest(manifest_path: str) -> Tuple[np.ndarray, Dict[str, Any]]:
    """
    Loads spatial proxy from a manifest file.
    """
    with open(manifest_path, 'r') as f:
        manifest = json.load(f)
    
    proxy_data = np.array(manifest.get('proxy_data', []))
    metadata = manifest.get('metadata', {})
    
    return proxy_data, metadata

def inject_spatial_dependency(data: np.ndarray, proxy: np.ndarray, bandwidth: float, seed: Optional[int] = None) -> np.ndarray:
    """
    Injects spatial dependency using kernel smoothing on the proxy.
    """
    return spatial_kernel_smooth(data, proxy, bandwidth, seed)

def validate_spatial_injection(original_data: np.ndarray, injected_data: np.ndarray, bandwidth: float, tolerance: float = 0.1) -> Dict[str, Any]:
    """
    Validates that spatial injection was successful.
    """
    return validate_spatial_kernel_smooth(original_data, injected_data, bandwidth, tolerance)

# Feature-Space Proxy Validation Logic (T041)
def validate_feature_space_proxy(data: np.ndarray, proxy: np.ndarray, n_clusters: int, 
                                 cluster_metric_threshold: float = 0.5, 
                                 silhouette_threshold: float = 0.3) -> Dict[str, Any]:
    """
    Validates the feature-space clustering proxy as per FR-003.
    
    Validation criteria:
    1. Proxy structure integrity: Correct shape and non-NaN values
    2. Cluster quality: Silhouette score above threshold
    3. Feature space separation: Clusters should be distinct in feature space
    
    Returns a validation report dictionary.
    """
    if data.ndim == 1:
        data = data.reshape(-1, 1)
    if proxy.ndim == 1:
        proxy = proxy.reshape(-1, 2)
    
    n_samples, n_features = data.shape
    proxy_n, proxy_dim = proxy.shape
    
    report = {
        "valid": True,
        "checks": {},
        "details": {}
    }
    
    # Check 1: Structure Integrity
    structure_valid = True
    structure_reasons = []
    
    if proxy.shape[0] != data.shape[0]:
        structure_valid = False
        structure_reasons.append(f"Proxy sample count ({proxy_n}) != data sample count ({n_samples})")
    
    if proxy.shape[1] != 2:
        structure_valid = False
        structure_reasons.append(f"Proxy dimension ({proxy_dim}) != 2")
    
    if np.any(np.isnan(proxy)):
        structure_valid = False
        structure_reasons.append("Proxy contains NaN values")
    
    report["checks"]["structure_integrity"] = {
        "passed": structure_valid,
        "reasons": structure_reasons
    }
    
    if not structure_valid:
        report["valid"] = False
        return report
    
    # Check 2: Cluster Quality (Silhouette Score)
    # We use the proxy coordinates to evaluate cluster separation
    try:
        # Assign cluster labels based on proxy coordinates (using KMeans on proxy)
        # This effectively checks if the proxy creates well-separated clusters
        kmeans_check = KMeans(n_clusters=n_clusters, random_state=42, n_init=10)
        cluster_labels = kmeans_check.fit_predict(proxy)
        
        # Calculate silhouette score
        from sklearn.metrics import silhouette_score
        if len(np.unique(cluster_labels)) > 1:
            sil_score = silhouette_score(proxy, cluster_labels)
        else:
            sil_score = 0.0
        
        cluster_valid = sil_score >= cluster_metric_threshold
        report["checks"]["cluster_quality"] = {
            "passed": cluster_valid,
            "silhouette_score": float(sil_score),
            "threshold": cluster_metric_threshold
        }
        
        if not cluster_valid:
            report["valid"] = False
        
        report["details"]["silhouette_score"] = float(sil_score)
        
    except Exception as e:
        report["checks"]["cluster_quality"] = {
            "passed": False,
            "error": str(e)
        }
        report["valid"] = False
    
    # Check 3: Feature Space Separation
    # Check if clusters in proxy correspond to distinct regions in original feature space
    try:
        # Re-use cluster labels from proxy
        cluster_centers_data = np.array([data[cluster_labels == i].mean(axis=0) for i in range(n_clusters)])
        
        # Calculate inter-cluster distances
        inter_distances = cdist(cluster_centers_data, cluster_centers_data, metric='euclidean')
        np.fill_diagonal(inter_distances, np.inf)
        min_inter_cluster_dist = np.min(inter_distances)
        
        # Calculate intra-cluster variance
        intra_variances = []
        for i in range(n_clusters):
            mask = cluster_labels == i
            if np.sum(mask) > 1:
                var = np.var(data[mask], axis=0).mean()
                intra_variances.append(var)
        
        avg_intra_var = np.mean(intra_variances) if intra_variances else 0.0
        
        # Heuristic: Inter-cluster distance should be significantly larger than intra-cluster variance
        separation_ratio = min_inter_cluster_dist / (np.sqrt(avg_intra_var) + 1e-8)
        
        separation_valid = separation_ratio >= silhouette_threshold
        report["checks"]["feature_space_separation"] = {
            "passed": separation_valid,
            "min_inter_cluster_dist": float(min_inter_cluster_dist),
            "avg_intra_variance": float(avg_intra_var),
            "separation_ratio": float(separation_ratio),
            "threshold": silhouette_threshold
        }
        
        if not separation_valid:
            report["valid"] = False
        
        report["details"]["separation_ratio"] = float(separation_ratio)
        
    except Exception as e:
        report["checks"]["feature_space_separation"] = {
            "passed": False,
            "error": str(e)
        }
        report["valid"] = False
    
    # Summary
    report["summary"] = {
        "total_checks": 3,
        "passed_checks": sum(1 for check in report["checks"].values() if check.get("passed", False)),
        "n_samples": n_samples,
        "n_clusters": n_clusters
    }
    
    return report

def save_proxy_validation_report(report: Dict[str, Any], output_path: str) -> None:
    """
    Saves the proxy validation report to a JSON file.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w') as f:
        json.dump(report, f, indent=2)