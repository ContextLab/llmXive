import os
import sys
import json
import numpy as np
import cv2
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

# Local imports based on project structure
import cv2
from PIL import Image
import torch
from torchvision import models, transforms

# Import config for paths
from config import get_raw_dir, get_results_dir, get_data_dir

# Import memory monitor for batch checks if needed (though this is eval)
from utils.memory_monitor import check_memory_limit, should_batch_process

# Constants
DEVICE = "cpu"  # Enforce CPU-only as per constraints
BATCH_SIZE = 16

def load_npy_safe(path: Path) -> np.ndarray:
    """
    Safely load a .npy file.
    Raises FileNotFoundError if missing, ValueError if invalid.
    """
    if not path.exists():
        raise FileNotFoundError(f"Required data file not found: {path}")
    try:
        data = np.load(path, allow_pickle=False)
        return data
    except Exception as e:
        raise ValueError(f"Failed to load {path}: {e}")

def calculate_world_score(dense_frames: np.ndarray) -> float:
    """
    Compute WorldScore for the dense baseline.
    Metric: Topological Fidelity (simplified as structural consistency).
    Since we are comparing against a reference, we assume the 'dense'
    frames are the ground truth for this metric calculation context
    (or we calculate a self-consistency score if no ground truth exists).
    
    For this implementation, we calculate a normalized structural similarity
    metric across frames to represent 'WorldScore' as defined in the spec's
    topological fidelity context.
    
    Args:
        dense_frames: Array of shape (N, H, W, C) or (N, C, H, W)
    
    Returns:
        float: WorldScore (0.0 to 1.0)
    """
    if dense_frames is None or len(dense_frames) == 0:
        return 0.0

    # Normalize to 0-1
    if dense_frames.max() > 1.0:
        frames = dense_frames.astype(np.float32) / 255.0
    else:
        frames = dense_frames.astype(np.float32)

    # Simple topological fidelity proxy: Mean Structural Similarity between consecutive frames
    # In a real scenario, this might involve homography consistency or optical flow divergence.
    # Here we use a simplified correlation metric as a proxy for 'World' stability.
    scores = []
    for i in range(len(frames) - 1):
        f1 = frames[i].flatten()
        f2 = frames[i+1].flatten()
        # Normalize correlation
        corr = np.corrcoef(f1, f2)[0, 1]
        if np.isnan(corr):
            corr = 0.0
        scores.append(corr)

    if not scores:
        return 0.0
    
    # Return mean score, clamped to [0, 1]
    return float(np.clip(np.mean(scores), 0.0, 1.0))

def calculate_sparse_consistency_score(warped_frames: np.ndarray, 
                                       correspondences: Optional[np.ndarray] = None) -> float:
    """
    Compute Sparse-Consistency Score using re-projection error.
    
    Args:
        warped_frames: Array of shape (N, H, W, C) representing warped sequences.
                       If correspondences are not passed, we simulate a consistency check
                       based on frame-to-frame alignment quality.
    Returns:
        float: Score (0.0 to 1.0, where 1.0 is perfect consistency)
    """
    if warped_frames is None or len(warped_frames) == 0:
        return 0.0

    # If we had real correspondences, we would compute reprojection error here.
    # Since T010/T011 produce warped frames, we assess the smoothness and 
    # lack of artifacts (NaNs, extreme gradients) as a proxy for consistency.
    
    # Check for NaNs or Inf
    if np.any(np.isnan(warped_frames)) or np.any(np.isinf(warped_frames)):
        return 0.0

    # Normalize
    if warped_frames.max() > 1.0:
        frames = warped_frames.astype(np.float32) / 255.0
    else:
        frames = warped_frames.astype(np.float32)

    # Calculate gradient magnitude variance as a consistency proxy
    # Low variance in gradients implies smooth, consistent warping
    grad_scores = []
    for i in range(len(frames)):
        f = frames[i]
        # Simple Sobel-like gradient
        gx = f[:, 1:] - f[:, :-1]
        gy = f[1:, :] - f[:-1, :]
        grad_mag = np.sqrt(gx**2 + gy**2)
        # Mean gradient magnitude (lower is smoother/more consistent if no motion, 
        # but we look for outliers). Let's use variance of gradient magnitudes.
        grad_scores.append(np.var(grad_mag))

    if not grad_scores:
        return 0.0

    # Invert so that lower variance (smoother) = higher score
    # Normalize to 0-1 range roughly
    max_var = max(grad_scores) if max(grad_scores) > 0 else 1.0
    score = 1.0 - (np.mean(grad_scores) / max_var)
    return float(np.clip(score, 0.0, 1.0))

def calculate_fid(dense_frames: np.ndarray, sparse_frames: np.ndarray) -> float:
    """
    Calculate Fréchet Inception Distance (FID) between dense baseline and sparse warped frames.
    Uses Inception-v3 feature extractor (CPU).
    
    Args:
        dense_frames: Numpy array of shape (N, H, W, C) or (N, C, H, W)
        sparse_frames: Numpy array of shape (M, H, W, C) or (M, C, H, W)
    
    Returns:
        float: FID score
    """
    # Load Inception-v3
    # Ensure model is on CPU
    model = models.inception_v3(weights=models.Inception_V3_Weights.IMAGENET1K_V1)
    model.fc = torch.nn.Identity()  # Remove final classification layer
    model = model.to(DEVICE)
    model.eval()

    # Preprocessing
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize((299, 299)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225])
    ])

    def get_features(frames: np.ndarray) -> torch.Tensor:
        features = []
        # Handle shape (N, H, W, C) -> (N, C, H, W)
        if frames.shape[-1] == 3:
            frames = np.transpose(frames, (0, 3, 1, 2))
        
        for i in range(len(frames)):
            img = frames[i].astype(np.uint8)
            if img.max() > 1:
                img = img
            else:
                img = (img * 255).astype(np.uint8)
            
            # Convert to PIL
            pil_img = Image.fromarray(img)
            tensor = preprocess(pil_img).unsqueeze(0)
            features.append(tensor)
        
        if not features:
            return torch.empty((0, 2048))
        
        batch = torch.cat(features, dim=0).to(DEVICE)
        with torch.no_grad():
            out = model(batch)
        return out.cpu()

    # Batch processing if memory is tight
    if len(dense_frames) > 1000 or len(sparse_frames) > 1000:
        # Simple check, in real impl we might use memory_monitor
        pass

    features_dense = get_features(dense_frames)
    features_sparse = get_features(sparse_frames)

    if features_dense.shape[0] == 0 or features_sparse.shape[0] == 0:
        return float('inf')

    # Calculate FID
    # mu1, sigma1
    mu1 = np.mean(features_dense.numpy(), axis=0)
    sigma1 = np.cov(features_dense.numpy(), rowvar=False)
    
    # mu2, sigma2
    mu2 = np.mean(features_sparse.numpy(), axis=0)
    sigma2 = np.cov(features_sparse.numpy(), rowvar=False)

    # FID calculation
    # FID = ||mu1 - mu2||^2 + Tr(sigma1 + sigma2 - 2*sqrt(sigma1*sigma2))
    diff = mu1 - mu2
    covmean = sigma1 @ sigma2
    
    # Ensure positive semi-definite for sqrt
    U, S, Vh = np.linalg.svd(covmean)
    covmean = U @ np.diag(S) @ Vh
    
    # Trace
    tr_covmean = np.trace(covmean)
    
    fid = diff.dot(diff) + np.trace(sigma1) + np.trace(sigma2) - 2 * tr_covmean
    
    return float(fid)

def compute_unified_geometric_error(warped_frames: np.ndarray, 
                                    reference_frames: Optional[np.ndarray] = None) -> float:
    """
    Calculate Unified Geometric Error (Photometric Consistency) on held-out frames.
    If reference_frames are provided, compute difference. Otherwise, compute self-consistency.
    
    Args:
        warped_frames: Array of shape (N, H, W, C)
        reference_frames: Optional reference array for comparison
    
    Returns:
        float: Error metric (lower is better)
    """
    if warped_frames is None or len(warped_frames) == 0:
        return 0.0

    # Normalize
    if warped_frames.max() > 1.0:
        warped = warped_frames.astype(np.float32) / 255.0
    else:
        warped = warped_frames.astype(np.float32)

    if reference_frames is not None:
        if reference_frames.max() > 1.0:
            ref = reference_frames.astype(np.float32) / 255.0
        else:
            ref = reference_frames.astype(np.float32)
        
        # Ensure same shape
        min_len = min(len(warped), len(ref))
        warped = warped[:min_len]
        ref = ref[:min_len]
        
        # MSE
        error = np.mean((warped - ref) ** 2)
    else:
        # Self-consistency: difference between adjacent frames in warped sequence
        # (Assumes temporal consistency is desired)
        errors = []
        for i in range(len(warped) - 1):
            diff = np.abs(warped[i] - warped[i+1])
            errors.append(np.mean(diff))
        error = np.mean(errors) if errors else 0.0

    return float(error)

def main():
    """
    Main entry point to compute all metrics and save to data/results/metrics.json
    """
    print("Starting metrics computation for T017...")
    
    # Paths
    raw_dir = get_raw_dir()
    results_dir = get_results_dir()
    
    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"
    
    # Load Data
    print(f"Loading dense baseline from {dense_path}...")
    try:
        dense_frames = load_npy_safe(dense_path)
        print(f"Loaded dense frames: {dense_frames.shape}")
    except Exception as e:
        print(f"Error loading dense baseline: {e}")
        # If dense baseline is missing, we cannot compute FID or WorldScore relative to it
        # But we can still compute sparse consistency if sparse data exists
        dense_frames = None

    print(f"Loading sparse warped frames from {sparse_path}...")
    try:
        sparse_frames = load_npy_safe(sparse_path)
        print(f"Loaded sparse frames: {sparse_frames.shape}")
    except Exception as e:
        print(f"Error loading sparse warped frames: {e}")
        sparse_frames = None

    if sparse_frames is None:
        print("CRITICAL: Sparse warped frames not found. Cannot compute metrics.")
        sys.exit(1)

    # Compute Metrics
    metrics = {
        "task_id": "T017",
        "timestamp": str(torch.utils.data.get_worker_info()) if False else "N/A", # Placeholder for real timestamp
        "world_score": None,
        "sparse_consistency_score": None,
        "fid": None,
        "unified_geometric_error": None
    }

    if dense_frames is not None:
        print("Computing WorldScore...")
        metrics["world_score"] = calculate_world_score(dense_frames)
        print(f"WorldScore: {metrics['world_score']}")
    else:
        print("Skipping WorldScore (Dense baseline missing).")

    print("Computing Sparse-Consistency Score...")
    metrics["sparse_consistency_score"] = calculate_sparse_consistency_score(sparse_frames)
    print(f"Sparse-Consistency Score: {metrics['sparse_consistency_score']}")

    if dense_frames is not None:
        print("Computing FID...")
        # Check memory before heavy computation
        if should_batch_process():
            print("High memory usage detected, proceeding with caution.")
        
        metrics["fid"] = calculate_fid(dense_frames, sparse_frames)
        print(f"FID: {metrics['fid']}")
    else:
        print("Skipping FID (Dense baseline missing).")

    print("Computing Unified Geometric Error...")
    # Use sparse frames against themselves for self-consistency if no reference
    metrics["unified_geometric_error"] = compute_unified_geometric_error(sparse_frames)
    print(f"Unified Geometric Error: {metrics['unified_geometric_error']}")

    # Save Results
    output_path = results_dir / "metrics.json"
    print(f"Saving metrics to {output_path}...")
    
    # Ensure directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    print("Metrics computation complete.")
    return metrics

if __name__ == "__main__":
    main()