import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from scipy.spatial.distance import pdist, squareform
from scipy.stats import entropy
from sklearn.metrics import pairwise_distances
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings

# Suppress specific warnings for cleaner output
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=UserWarning)

# Import config for paths
from config import get_results_dir, get_raw_dir, get_features_dir, get_stratified_dir

# Import memory monitor for logging
from utils.memory_monitor import MemoryMonitor, check_memory_limit, get_current_memory_mb

# Constants
DEFAULT_IMAGE_SIZE = (64, 64)
NUM_BINS = 256
FID_EPSILON = 1e-6
WORLD_SCORE_THRESHOLD = 0.85
SPARSE_CONSISTENCY_THRESHOLD = 0.90

def load_npy_safe(path: Path, required_shape: Optional[Tuple] = None) -> Optional[np.ndarray]:
    """
    Safely load a .npy file with optional shape validation.
    
    Args:
        path: Path to the .npy file
        required_shape: Optional tuple to validate against
        
    Returns:
        Loaded numpy array or None if file missing/corrupted
    """
    if not path.exists():
        print(f"[ERROR] File not found: {path}")
        return None
    
    try:
        data = np.load(path, allow_pickle=True)
        if required_shape and data.shape != required_shape:
            print(f"[WARNING] Shape mismatch: expected {required_shape}, got {data.shape}")
            # Return data anyway but log warning
        return data
    except Exception as e:
        print(f"[ERROR] Failed to load {path}: {e}")
        return None

def calculate_world_score(
    dense_baseline: np.ndarray,
    sparse_warped: np.ndarray,
    threshold: float = WORLD_SCORE_THRESHOLD
) -> Dict[str, Any]:
    """
    Compute WorldScore based on topological fidelity between dense baseline and sparse warped frames.
    
    The metric measures how well the sparse method preserves the topological structure
    of the dense baseline reconstruction.
    
    Args:
        dense_baseline: Dense baseline frames (N, H, W, C)
        sparse_warped: Sparse warped frames (N, H, W, C)
        threshold: Threshold for topological fidelity (default: 0.85)
        
    Returns:
        Dictionary with world_score, topological_fidelity, and pass/fail status
    """
    if dense_baseline is None or sparse_warped is None:
        return {
            "world_score": 0.0,
            "topological_fidelity": 0.0,
            "pass": False,
            "error": "Missing input data"
        }
    
    # Ensure same number of frames
    min_frames = min(len(dense_baseline), len(sparse_warped))
    dense_frames = dense_baseline[:min_frames]
    sparse_frames = sparse_warped[:min_frames]
    
    # Flatten frames for topological analysis
    dense_flat = dense_frames.reshape(min_frames, -1)
    sparse_flat = sparse_frames.reshape(min_frames, -1)
    
    # Compute pairwise distances for topological structure
    dense_dist = squareform(pdist(dense_flat, metric='euclidean'))
    sparse_dist = squareform(pdist(sparse_flat, metric='euclidean'))
    
    # Normalize distances
    dense_dist_norm = dense_dist / (np.max(dense_dist) + 1e-8)
    sparse_dist_norm = sparse_dist / (np.max(sparse_dist) + 1e-8)
    
    # Compute topological fidelity as correlation of distance matrices
    # Flatten and compute correlation
    dense_vec = dense_dist_norm.flatten()
    sparse_vec = sparse_dist_norm.flatten()
    
    # Pearson correlation for topological preservation
    correlation = np.corrcoef(dense_vec, sparse_vec)[0, 1]
    if np.isnan(correlation):
        correlation = 0.0
    
    # WorldScore is a combination of correlation and structural similarity
    # Using a simple weighted combination for now
    structural_similarity = 1.0 - np.mean(np.abs(dense_dist_norm - sparse_dist_norm))
    
    world_score = 0.6 * correlation + 0.4 * structural_similarity
    topological_fidelity = correlation
    
    return {
        "world_score": float(world_score),
        "topological_fidelity": float(topological_fidelity),
        "structural_similarity": float(structural_similarity),
        "pass": bool(world_score >= threshold),
        "threshold": threshold,
        "num_frames_analyzed": min_frames
    }

def calculate_sparse_consistency_score(
    sparse_warped: np.ndarray,
    reprojection_errors: Optional[np.ndarray] = None,
    threshold: float = SPARSE_CONSISTENCY_THRESHOLD
) -> Dict[str, Any]:
    """
    Compute Sparse-Consistency Score based on reprojection error and internal consistency.
    
    Args:
        sparse_warped: Sparse warped frames (N, H, W, C)
        reprojection_errors: Optional array of reprojection errors from solver
        threshold: Threshold for consistency (default: 0.90)
        
    Returns:
        Dictionary with sparse_consistency_score, mean_reprojection_error, and pass/fail
    """
    if sparse_warped is None:
        return {
            "sparse_consistency_score": 0.0,
            "mean_reprojection_error": 0.0,
            "pass": False,
            "error": "Missing sparse warped frames"
        }
    
    # Calculate internal consistency using frame-to-frame differences
    if len(sparse_warped) > 1:
        frame_diffs = []
        for i in range(len(sparse_warped) - 1):
            diff = np.mean(np.abs(sparse_warped[i+1] - sparse_warped[i]))
            frame_diffs.append(diff)
        
        mean_frame_diff = np.mean(frame_diffs)
        # Normalize to 0-1 range (assuming typical differences are < 50)
        internal_consistency = max(0.0, 1.0 - (mean_frame_diff / 50.0))
    else:
        internal_consistency = 1.0  # Single frame is trivially consistent
    
    # Incorporate reprojection error if available
    if reprojection_errors is not None and len(reprojection_errors) > 0:
        mean_reproj = np.mean(reprojection_errors)
        # Convert reprojection error to a score (lower error = higher score)
        reproj_score = max(0.0, 1.0 - (mean_reproj / 10.0))  # Assume 10px is max error
        sparse_consistency = 0.7 * internal_consistency + 0.3 * reproj_score
        mean_reprojection_error = float(mean_reproj)
    else:
        sparse_consistency = internal_consistency
        mean_reprojection_error = 0.0
    
    return {
        "sparse_consistency_score": float(sparse_consistency),
        "mean_reprojection_error": mean_reprojection_error,
        "internal_consistency": float(internal_consistency),
        "pass": bool(sparse_consistency >= threshold),
        "threshold": threshold,
        "num_frames_analyzed": len(sparse_warped)
    }

def calculate_activation_statistics(
    features: np.ndarray
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate mean and covariance of features for FID computation.
    
    Args:
        features: Feature matrix (N, D)
        
    Returns:
        Tuple of (mean, covariance)
    """
    mu = np.mean(features, axis=0)
    sigma = np.cov(features, rowvar=False)
    return mu, sigma

def linalg_sqrtm(matrix: np.ndarray) -> np.ndarray:
    """
    Compute matrix square root using eigenvalue decomposition.
    
    Args:
        matrix: Input square matrix
        
    Returns:
        Matrix square root
    """
    # Ensure symmetric
    matrix = (matrix + matrix.T) / 2.0
    
    # Eigenvalue decomposition
    eigenvalues, eigenvectors = np.linalg.eigh(matrix)
    
    # Handle negative eigenvalues (numerical errors)
    eigenvalues = np.maximum(eigenvalues, 0)
    
    # Compute square root
    sqrt_eigenvalues = np.sqrt(eigenvalues)
    sqrt_matrix = eigenvectors @ np.diag(sqrt_eigenvalues) @ eigenvectors.T
    
    return sqrt_matrix

def calculate_frechet_distance(
    mu1: np.ndarray,
    sigma1: np.ndarray,
    mu2: np.ndarray,
    sigma2: np.ndarray,
    eps: float = FID_EPSILON
) -> float:
    """
    Compute Fréchet Distance between two multivariate Gaussians.
    
    Args:
        mu1: Mean of first distribution
        sigma1: Covariance of first distribution
        mu2: Mean of second distribution
        sigma2: Covariance of second distribution
        eps: Small epsilon for numerical stability
        
    Returns:
        Fréchet Distance
    """
    # Ensure same dimensionality
    assert mu1.shape == mu2.shape, f"Mean dimensions mismatch: {mu1.shape} vs {mu2.shape}"
    assert sigma1.shape == sigma2.shape, f"Covariance dimensions mismatch: {sigma1.shape} vs {sigma2.shape}"
    
    # Compute squared difference of means
    diff = mu1 - mu2
    mean_sq = np.dot(diff, diff)
    
    # Compute trace of product of covariance matrices
    cov_mean = sigma1 + sigma2
    
    # Compute sqrt of product of covariances
    # Using eigenvalue decomposition for numerical stability
    try:
        sqrt_prod = linalg_sqrtm(sigma1 @ sigma2)
    except:
        # Fallback: use identity if decomposition fails
        sqrt_prod = np.zeros_like(sigma1)
    
    trace_term = np.trace(cov_mean - 2 * sqrt_prod)
    
    # FID = ||mu1 - mu2||^2 + Tr(Sigma1 + Sigma2 - 2*sqrt(Sigma1*Sigma2))
    fid = mean_sq + trace_term
    
    return max(0.0, fid)  # FID should be non-negative

def extract_inception_features(
    frames: np.ndarray,
    batch_size: int = 32
) -> np.ndarray:
    """
    Extract features from frames using a lightweight feature extractor.
    
    Since we're on CPU and cannot use full Inception-v3, we use a simplified
    approach based on color histograms and edge features that approximates
    the distribution characteristics.
    
    Args:
        frames: Input frames (N, H, W, C)
        batch_size: Batch size for processing
        
    Returns:
        Feature matrix (N, D)
    """
    n_frames = len(frames)
    features = []
    
    for i in range(0, n_frames, batch_size):
        batch = frames[i:i+batch_size]
        batch_features = []
        
        for frame in batch:
            # Convert to float for processing
            frame_float = frame.astype(np.float32) / 255.0
            
            # Extract color histogram features (3 channels)
            hist_features = []
            for c in range(3):
                hist, _ = np.histogram(frame_float[:, :, c], bins=16, range=(0, 1))
                hist_features.append(hist)
            
            # Extract edge features using Sobel
            gray = np.mean(frame_float, axis=2)
            sobel_x = cv2.Sobel((gray * 255).astype(np.uint8), cv2.CV_64F, 1, 0, ksize=3)
            sobel_y = cv2.Sobel((gray * 255).astype(np.uint8), cv2.CV_64F, 0, 1, ksize=3)
            edge_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
            
            # Histogram of edge magnitudes
            edge_hist, _ = np.histogram(edge_magnitude.flatten(), bins=16, range=(0, 255))
            hist_features.append(edge_hist)
            
            # Flatten and normalize
            feature_vec = np.concatenate(hist_features)
            feature_vec = feature_vec / (np.sum(feature_vec) + 1e-8)
            batch_features.append(feature_vec)
        
        features.extend(batch_features)
        
        # Memory check every batch
        if i % (batch_size * 4) == 0:
            current_mem = get_current_memory_mb()
            if check_memory_limit(6.0):  # 6GB limit
                print(f"[WARNING] High memory usage: {current_mem:.0f}MB")
    
    return np.array(features)

def calculate_fid(
    frames1: np.ndarray,
    frames2: np.ndarray,
    batch_size: int = 32
) -> Dict[str, Any]:
    """
    Calculate Fréchet Inception Distance between two sets of frames.
    
    Args:
        frames1: First set of frames (N1, H, W, C)
        frames2: Second set of frames (N2, H, W, C)
        batch_size: Batch size for feature extraction
        
    Returns:
        Dictionary with FID score and statistics
    """
    if frames1 is None or frames2 is None:
        return {
            "fid": float('inf'),
            "error": "Missing input data"
        }
    
    # Ensure same dimensions
    if frames1.shape[1:] != frames2.shape[1:]:
        # Resize to match
        target_shape = frames1.shape[1:]
        frames2_resized = np.zeros_like(frames1)
        for i, frame in enumerate(frames2):
            if i < len(frames2_resized):
                frames2_resized[i] = cv2.resize(frame, (target_shape[1], target_shape[0]))
        frames2 = frames2_resized
    
    # Limit to minimum number of frames
    min_n = min(len(frames1), len(frames2))
    frames1 = frames1[:min_n]
    frames2 = frames2[:min_n]
    
    print(f"Extracting features for {len(frames1)} frames from each set...")
    
    # Extract features
    features1 = extract_inception_features(frames1, batch_size)
    features2 = extract_inception_features(frames2, batch_size)
    
    # Calculate statistics
    mu1, sigma1 = calculate_activation_statistics(features1)
    mu2, sigma2 = calculate_activation_statistics(features2)
    
    # Compute FID
    fid = calculate_frechet_distance(mu1, sigma1, mu2, sigma2)
    
    return {
        "fid": float(fid),
        "num_frames": min_n,
        "feature_dim": features1.shape[1],
        "mean1": float(np.mean(mu1)),
        "mean2": float(np.mean(mu2)),
        "std1": float(np.std(sigma1)),
        "std2": float(np.std(sigma2))
    }

def compute_unified_geometric_error(
    sparse_warped: np.ndarray,
    held_out_frames: Optional[np.ndarray] = None
) -> Dict[str, Any]:
    """
    Compute unified geometric error for internal validation.
    
    Args:
        sparse_warped: Sparse warped frames
        held_out_frames: Optional held-out frames for validation
        
    Returns:
        Dictionary with geometric error metrics
    """
    if sparse_warped is None:
        return {
            "unified_geometric_error": 0.0,
            "photometric_consistency": 0.0,
            "error": "Missing sparse warped frames"
        }
    
    # Calculate photometric consistency (frame-to-frame difference)
    if len(sparse_warped) > 1:
        diffs = []
        for i in range(len(sparse_warped) - 1):
            diff = np.mean(np.abs(sparse_warped[i+1] - sparse_warped[i]))
            diffs.append(diff)
        photometric_consistency = 1.0 - (np.mean(diffs) / 50.0)  # Normalize
        photometric_consistency = max(0.0, min(1.0, photometric_consistency))
    else:
        photometric_consistency = 1.0
    
    # Calculate structural consistency using variance
    if len(sparse_warped) > 1:
        # Flatten all frames and compute variance across time
        flat_frames = sparse_warped.reshape(len(sparse_warped), -1)
        time_variance = np.var(flat_frames, axis=0)
        # Low variance indicates stable reconstruction
        geometric_error = np.mean(time_variance) / (np.max(time_variance) + 1e-8)
        geometric_error = min(1.0, geometric_error)
    else:
        geometric_error = 0.0
    
    # Unified score combines both metrics
    unified_error = 0.5 * geometric_error + 0.5 * (1.0 - photometric_consistency)
    
    return {
        "unified_geometric_error": float(unified_error),
        "photometric_consistency": float(photometric_consistency),
        "geometric_error": float(geometric_error),
        "num_frames": len(sparse_warped)
    }

def main():
    """
    Main entry point for metrics computation.
    
    This script computes:
    1. WorldScore for dense baseline
    2. Sparse-Consistency Score for sparse warped frames
    3. Fréchet Inception Distance (FID) comparing distributions
    4. Unified Geometric Error for internal validation
    
    Outputs results to data/results/metrics.json
    """
    print("Starting metrics computation...")
    
    # Initialize memory monitor
    monitor = MemoryMonitor("metrics_computation")
    monitor.start()
    
    # Define paths
    results_dir = get_results_dir()
    raw_dir = get_raw_dir()
    
    dense_baseline_path = raw_dir / "dense_baseline_frames.npy"
    sparse_warped_path = results_dir / "sparse_warped_frames.npy"
    output_path = results_dir / "metrics.json"
    
    # Ensure results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    # Load dense baseline
    print(f"Loading dense baseline from {dense_baseline_path}...")
    dense_baseline = load_npy_safe(dense_baseline_path)
    if dense_baseline is None:
        print("[ERROR] Dense baseline not found. Cannot compute metrics.")
        monitor.stop()
        sys.exit(1)
    print(f"Dense baseline shape: {dense_baseline.shape}")
    
    # Load sparse warped frames
    print(f"Loading sparse warped frames from {sparse_warped_path}...")
    sparse_warped = load_npy_safe(sparse_warped_path)
    if sparse_warped is None:
        print("[ERROR] Sparse warped frames not found. Cannot compute metrics.")
        monitor.stop()
        sys.exit(1)
    print(f"Sparse warped frames shape: {sparse_warped.shape}")
    
    # Compute metrics
    metrics = {
        "timestamp": str(np.datetime64('now')),
        "data_info": {
            "dense_baseline_shape": list(dense_baseline.shape),
            "sparse_warped_shape": list(sparse_warped.shape)
        }
    }
    
    # 1. WorldScore
    print("Computing WorldScore...")
    world_score_result = calculate_world_score(dense_baseline, sparse_warped)
    metrics["world_score"] = world_score_result
    
    # 2. Sparse-Consistency Score
    print("Computing Sparse-Consistency Score...")
    # We don't have reprojection errors here, so pass None
    sparse_consistency_result = calculate_sparse_consistency_score(sparse_warped)
    metrics["sparse_consistency_score"] = sparse_consistency_result
    
    # 3. Fréchet Inception Distance
    print("Computing Fréchet Inception Distance (FID)...")
    fid_result = calculate_fid(dense_baseline, sparse_warped)
    metrics["frechet_inception_distance"] = fid_result
    
    # 4. Unified Geometric Error
    print("Computing Unified Geometric Error...")
    geometric_error_result = compute_unified_geometric_error(sparse_warped)
    metrics["unified_geometric_error"] = geometric_error_result
    
    # Add summary
    metrics["summary"] = {
        "world_score_pass": world_score_result.get("pass", False),
        "sparse_consistency_pass": sparse_consistency_result.get("pass", False),
        "fid_score": fid_result.get("fid", float('inf')),
        "geometric_error": geometric_error_result.get("unified_geometric_error", 0.0)
    }
    
    # Write results
    print(f"Writing results to {output_path}...")
    try:
        with open(output_path, 'w') as f:
            json.dump(metrics, f, indent=2)
        print(f"Metrics successfully written to {output_path}")
    except Exception as e:
        print(f"[ERROR] Failed to write metrics: {e}")
        monitor.stop()
        sys.exit(1)
    
    # Stop memory monitor
    monitor.stop()
    session_metrics = monitor.get_session_metrics()
    if session_metrics:
        print(f"Peak memory: {session_metrics.get('peak_memory_mb', 0):.2f} MB")
        print(f"Wall time: {session_metrics.get('wall_time_seconds', 0):.2f} seconds")
    
    print("Metrics computation completed successfully.")
    return metrics

if __name__ == "__main__":
    main()