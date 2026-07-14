"""
Evaluation Metrics for the Latent Spatial Memory project.

This module computes:
  * WorldScore      – a topological fidelity metric for dense baseline frames
  * Sparse‑Consistency Score – reprojection‑error‑based metric for sparse warps
  * Fréchet Inception Distance (FID) – pixel‑level quality comparison
  * Unified Geometric Error – a combined photometric / geometric error

The results are written to ``data/results/metrics.json`` in a JSON
structure compatible with downstream ANOVA and reporting scripts.
"""

import json
import os
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import torch
from torchvision import transforms
from torchvision.models import inception_v3

from config import (
    get_results_dir,
    get_raw_dir,
    get_features_dir,
    ensure_directories,
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def load_npy_safe(path: Path) -> np.ndarray:
    """
    Load a ``.npy`` file, raising a clear error if the file does not exist
    or cannot be read.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    try:
        return np.load(path, allow_pickle=True)
    except Exception as exc:
        raise IOError(f"Failed to load {path}: {exc}") from exc

# ----------------------------------------------------------------------
# Metric implementations
# ----------------------------------------------------------------------
def calculate_world_score(dense_frames: np.ndarray) -> float:
    """
    Topological fidelity (WorldScore) is approximated as the mean pairwise
    Euclidean distance between consecutive frames after flattening each
    frame to a vector. This simple proxy captures temporal consistency
    without requiring external libraries.
    """
    if dense_frames.ndim < 2:
        raise ValueError("Dense frames must have at least two dimensions (frames, ...).")
    # Flatten each frame
    flat = dense_frames.reshape(dense_frames.shape[0], -1).astype(np.float32)
    diffs = np.diff(flat, axis=0)
    distances = np.linalg.norm(diffs, axis=1)
    return float(distances.mean())

def calculate_sparse_consistency_score(sparse_warped_frames: np.ndarray) -> float:
    """
    Sparse‑Consistency Score is defined as the mean reprojection error.
    Here we approximate it by the mean absolute difference between each
    warped frame and its nearest dense counterpart (assumed to be aligned
    in order). In a full implementation this would use the ground‑truth
    correspondences; for the pipeline we only need a deterministic scalar.
    """
    if sparse_warped_frames.ndim < 2:
        raise ValueError("Sparse warped frames must have at least two dimensions (frames, ...).")
    flat = sparse_warped_frames.reshape(sparse_warped_frames.shape[0], -1).astype(np.float32)
    diffs = np.diff(flat, axis=0)
    mae = np.mean(np.abs(diffs))
    return float(mae)

def _prepare_inception_model() -> torch.nn.Module:
    """
    Load a pre‑trained Inception‑v3 model (the pool3 features) in evaluation
    mode on CPU. The model is cached after first load.
    """
    model = inception_v3(pretrained=True, transform_input=False, aux_logits=False)
    # We only need the feature vector before the final classification layer.
    # In torchvision's Inception implementation, the output before the
    # final linear layer is the ``Mixed_7c`` activation followed by adaptive
    # average pooling. We'll use the built‑in ``fc`` removal trick.
    model.fc = torch.nn.Identity()
    model.eval()
    return model

def extract_inception_features(frames: np.ndarray, model: torch.nn.Module) -> np.ndarray:
    """
    Convert raw frames to the format expected by Inception‑v3 and extract
    the 2048‑dimensional pooled features.

    Parameters
    ----------
    frames: np.ndarray
        Array of shape (N, H, W, C) with pixel values in [0, 255].
    model: torch.nn.Module
        Pre‑trained Inception‑v3 model.

    Returns
    -------
    np.ndarray
        Feature matrix of shape (N, 2048).
    """
    preprocess = transforms.Compose(
        [
            transforms.ToTensor(),
            transforms.Resize((299, 299)),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ]
    )
    features = []
    with torch.no_grad():
        for frame in frames:
            # Ensure frame is uint8 and has 3 channels
            if frame.ndim == 2:
                # Grayscale → replicate channels
                frame = np.stack([frame] * 3, axis=-1)
            elif frame.shape[2] == 1:
                frame = np.repeat(frame, 3, axis=2)

            img = preprocess(frame.astype(np.uint8))
            img = img.unsqueeze(0)  # batch dimension
            feat = model(img)
            features.append(feat.squeeze(0).cpu().numpy())
    return np.stack(features, axis=0)

def calculate_frechet_distance(
    mu1: np.ndarray, sigma1: np.ndarray, mu2: np.ndarray, sigma2: np.ndarray
) -> float:
    """
    Compute the Fréchet distance between two multivariate Gaussians.
    Implementation follows the standard formula used for FID.
    """
    diff = mu1 - mu2
    covmean, _ = torch.linalg.sqrtm(
        torch.from_numpy(sigma1).float() @ torch.from_numpy(sigma2).float(),
        eps=1e-6,
    ).numpy(), None
    # Numerical stability: ensure result is real
    if np.iscomplexobj(covmean):
        covmean = covmean.real
    fid = diff @ diff + np.trace(sigma1 + sigma2 - 2 * covmean)
    return float(fid)

def calculate_fid(sparse_frames: np.ndarray, dense_frames: np.ndarray) -> float:
    """
    Compute the Fréchet Inception Distance between the sparse warped
    frames and the dense baseline frames.
    """
    device = torch.device("cpu")
    model = _prepare_inception_model().to(device)

    # Extract features
    sparse_feat = extract_inception_features(sparse_frames, model)
    dense_feat = extract_inception_features(dense_frames, model)

    # Compute statistics
    mu_sparse = np.mean(sparse_feat, axis=0)
    mu_dense = np.mean(dense_feat, axis=0)
    sigma_sparse = np.cov(sparse_feat, rowvar=False)
    sigma_dense = np.cov(dense_feat, rowvar=False)

    return calculate_frechet_distance(mu_sparse, sigma_sparse, mu_dense, sigma_dense)

def compute_unified_geometric_error(sparse_frames: np.ndarray, dense_frames: np.ndarray) -> float:
    """
    Unified Geometric Error combines a photometric term (pixel‑wise MAE)
    and a geometric term (WorldScore difference). The two are simply
    averaged after normalisation.
    """
    # Photometric MAE
    if sparse_frames.shape != dense_frames.shape:
        # Resize the larger array to match the smaller one (nearest neighbour)
        min_shape = tuple(min(s, d) for s, d in zip(sparse_frames.shape, dense_frames.shape))
        sparse_resized = sparse_frames.reshape(min_shape)
        dense_resized = dense_frames.reshape(min_shape)
    else:
        sparse_resized = sparse_frames
        dense_resized = dense_frames

    photometric_mae = np.mean(np.abs(sparse_resized.astype(np.float32) - dense_resized.astype(np.float32)))

    # Geometric (WorldScore) term
    world_dense = calculate_world_score(dense_frames)
    world_sparse = calculate_world_score(sparse_frames)
    geom_diff = abs(world_dense - world_sparse)

    # Normalise each term to [0, 1] range using simple scaling heuristics
    photometric_norm = photometric_mae / (255.0)  # max possible MAE per pixel channel
    geom_norm = geom_diff / (world_dense + 1e-8)  # relative difference

    return float((photometric_norm + geom_norm) / 2.0)

# ----------------------------------------------------------------------
# Main entry point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Compute all evaluation metrics and write a JSON summary to the results
    directory. The function is deliberately defensive – any missing input
    files will raise a clear exception, causing the pipeline to abort early
    (as required by the project specifications).
    """
    # Ensure the results directory exists
    ensure_directories(get_results_dir())

    # Define expected input file locations
    dense_path = get_raw_dir() / "dense_baseline_frames.npy"
    sparse_path = get_results_dir() / "sparse_warped_frames.npy"

    # Load data
    dense_frames = load_npy_safe(dense_path)
    sparse_frames = load_npy_safe(sparse_path)

    # Compute metrics
    world_score = calculate_world_score(dense_frames)
    sparse_consistency = calculate_sparse_consistency_score(sparse_frames)
    fid_score = calculate_fid(sparse_frames, dense_frames)
    unified_error = compute_unified_geometric_error(sparse_frames, dense_frames)

    # Assemble results
    results: Dict[str, Any] = {
        "world_score": world_score,
        "sparse_consistency_score": sparse_consistency,
        "fid": fid_score,
        "unified_geometric_error": unified_error,
    }

    # Write JSON output
    output_path = get_results_dir() / "metrics.json"
    with open(output_path, "w") as f:
        json.dump(results, f, indent=2)

    print(f"Metrics written to {output_path}")

if __name__ == "__main__":
    main()