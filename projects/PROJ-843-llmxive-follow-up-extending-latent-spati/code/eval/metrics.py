"""
Evaluation metrics for the latent spatial memory project.

This module computes:
  * WorldScore  – a simple topological fidelity metric for dense baseline frames.
  * Sparse‑Consistency Score – reprojection‑error based consistency for sparse warps.
  * Fréchet Inception Distance (FID) between dense and sparse frame distributions.
  * Unified Geometric Error – a photometric consistency measure.

The results are written to ``data/results/metrics.json``.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import torch
import torchvision.transforms as T
from torchvision.models import inception_v3

# Local imports
from config import (
    get_raw_dir,
    get_results_dir,
    ensure_directories,
)
from eval.download_dense_baseline import main as download_dense_baseline_main

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------

def _load_npy(path: Path) -> np.ndarray:
    """Load a ``.npy`` file, raising a clear error if it does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Expected file not found: {path}")
    return np.load(path, allow_pickle=True)

# ----------------------------------------------------------------------
# Metric implementations
# ----------------------------------------------------------------------

def calculate_world_score(dense_frames: np.ndarray) -> float:
    """
    Compute a simple topological fidelity score for dense frames.

    For demonstration purposes we define WorldScore as the mean
    L2 distance between consecutive frames, normalised by the
    maximum possible pixel value (255).  This yields a value in
    ``[0, 1]`` where lower is better (more consistent world).
    """
    if dense_frames.ndim != 4:
        raise ValueError("Dense frames should have shape (N, H, W, C).")
    diffs = np.diff(dense_frames.astype(np.float32), axis=0)
    l2 = np.linalg.norm(diffs.reshape(diffs.shape[0], -1), axis=1)
    mean_l2 = float(l2.mean())
    max_l2 = np.sqrt(dense_frames.shape[1] * dense_frames.shape[2] * dense_frames.shape[3]) * 255
    return mean_l2 / max_l2

def calculate_sparse_consistency_score(sparse_frames: np.ndarray) -> float:
    """
    Compute a reprojection‑error based consistency score.

    The sparse frames are expected to be 3‑D points projected back
    onto image space (shape: (N, H, W, 2)).  We treat the
    Euclidean distance between each point and the image centre as
    a proxy for reprojection error and return the mean.
    """
    if sparse_frames.ndim != 4 or sparse_frames.shape[-1] != 2:
        raise ValueError(
            "Sparse frames should have shape (N, H, W, 2) representing (x, y) coordinates."
        )
    h, w = sparse_frames.shape[1:3]
    centre = np.array([w / 2.0, h / 2.0])
    dists = np.linalg.norm(sparse_frames - centre, axis=-1)
    return float(dists.mean())

# ----------------------------------------------------------------------
# Inception‑V3 feature extraction for FID
# ----------------------------------------------------------------------

_inception_transform = T.Compose(
    [
        T.ToTensor(),
        T.Resize((299, 299)),
        T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ]
)

def _load_inception_model() -> torch.nn.Module:
    """
    Load a pretrained Inception‑v3 model truncated to the pool3 layer.
    The model is set to evaluation mode and moved to CPU.
    """
    model = inception_v3(pretrained=True, transform_input=False)
    # The pool3 features are available as ``model.fc`` after the
    # average‑pooling layer; we replace the final classifier with an
    # identity to expose the 2048‑dim vector.
    model.fc = torch.nn.Identity()
    model.eval()
    return model

def extract_inception_features(frames: np.ndarray) -> np.ndarray:
    """
    Extract Inception‑v3 pool3 features for a batch of frames.

    Parameters
    ----------
    frames : np.ndarray
        Array of shape (N, H, W, C) with dtype uint8 or float in [0, 255].

    Returns
    -------
    np.ndarray
        Array of shape (N, 2048) containing the extracted features.
    """
    if frames.ndim != 4:
        raise ValueError("Frames must have shape (N, H, W, C).")

    device = torch.device("cpu")
    model = _load_inception_model().to(device)

    features = []
    with torch.no_grad():
        for img in frames:
            # Ensure uint8
            if img.dtype != np.uint8:
                img = np.clip(img, 0, 255).astype(np.uint8)
            pil_img = T.functional.to_pil_image(img)
            tensor = _inception_transform(pil_img).unsqueeze(0).to(device)
            feat = model(tensor)  # shape (1, 2048)
            features.append(feat.squeeze(0).cpu().numpy())
    return np.stack(features, axis=0)

def calculate_fid(features1: np.ndarray, features2: np.ndarray) -> float:
    """
    Compute the Fréchet Inception Distance between two feature distributions.

    Parameters
    ----------
    features1, features2 : np.ndarray
        Arrays of shape (N, D) where D is the feature dimension (2048).

    Returns
    -------
    float
        The FID value (lower is better).
    """
    mu1 = np.mean(features1, axis=0)
    mu2 = np.mean(features2, axis=0)
    sigma1 = np.cov(features1, rowvar=False)
    sigma2 = np.cov(features2, rowvar=False)

    diff = mu1 - mu2
    covmean, _ = torch.linalg.sqrtm(
        torch.from_numpy(sigma1) @ torch.from_numpy(sigma2), disp=False
    )
    if torch.is_complex(covmean):
        covmean = covmean.real
    covmean = covmean.numpy()

    fid = diff @ diff + np.trace(sigma1 + sigma2 - 2 * covmean)
    return float(fid)

# ----------------------------------------------------------------------
# Unified Geometric Error (photometric consistency)
# ----------------------------------------------------------------------

def compute_unified_geometric_error(dense_frames: np.ndarray, sparse_frames: np.ndarray) -> float:
    """
    Compute a simple photometric consistency error between dense and sparse
    reconstructions.  We resize the sparse frames to the dense resolution,
    convert both to grayscale, and compute the mean absolute difference.
    """
    if dense_frames.shape != sparse_frames.shape:
        # Resize sparse to dense shape using nearest neighbour for speed
        import cv2

        N, H, W, C = dense_frames.shape
        resized = []
        for i in range(N):
            resized.append(
                cv2.resize(sparse_frames[i], (W, H), interpolation=cv2.INTER_NEAREST)
            )
        sparse_resized = np.stack(resized, axis=0)
    else:
        sparse_resized = sparse_frames

    # Convert to grayscale
    dense_gray = np.mean(dense_frames.astype(np.float32), axis=-1)
    sparse_gray = np.mean(sparse_resized.astype(np.float32), axis=-1)
    mae = np.mean(np.abs(dense_gray - sparse_gray))
    return float(mae)

# ----------------------------------------------------------------------
# Main orchestration
# ----------------------------------------------------------------------

def main() -> None:
    """
    Entry point for the ``metrics`` evaluation step.

    - Ensures required directories exist.
    - Downloads the dense baseline if it is missing.
    - Loads dense baseline frames and sparse warped frames.
    - Computes all metrics.
    - Writes a JSON file with the results to ``data/results/metrics.json``.
    """
    raw_dir = get_raw_dir()
    results_dir = get_results_dir()
    ensure_directories([raw_dir, results_dir])

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    # ------------------------------------------------------------------
    # Acquire dense baseline if absent
    # ------------------------------------------------------------------
    if not dense_path.is_file():
        print("[metrics] Dense baseline not found – downloading now...")
        download_dense_baseline_main()
        if not dense_path.is_file():
            raise FileNotFoundError(
                f"Failed to download dense baseline to {dense_path}"
            )

    # ------------------------------------------------------------------
    # Load data
    # ------------------------------------------------------------------
    dense_frames = _load_npy(dense_path)  # shape (N, H, W, C)
    sparse_frames = _load_npy(sparse_path)  # shape (N, H, W, C) or (N, H, W, 2)

    # ------------------------------------------------------------------
    # Compute metrics
    # ------------------------------------------------------------------
    world_score = calculate_world_score(dense_frames)
    sparse_consistency = calculate_sparse_consistency_score(sparse_frames)
    # FID requires feature extraction on both sets
    dense_features = extract_inception_features(dense_frames)
    sparse_features = extract_inception_features(sparse_frames)
    fid_score = calculate_fid(dense_features, sparse_features)
    unified_error = compute_unified_geometric_error(dense_frames, sparse_frames)

    metrics: Dict[str, Any] = {
        "WorldScore": world_score,
        "SparseConsistencyScore": sparse_consistency,
        "FID": fid_score,
        "UnifiedGeometricError": unified_error,
    }

    # ------------------------------------------------------------------
    # Persist results
    # ------------------------------------------------------------------
    output_path = results_dir / "metrics.json"
    with open(output_path, "w") as fp:
        json.dump(metrics, fp, indent=2)
    print(f"[metrics] Metrics written to {output_path}")

if __name__ == "__main__":
    main()
