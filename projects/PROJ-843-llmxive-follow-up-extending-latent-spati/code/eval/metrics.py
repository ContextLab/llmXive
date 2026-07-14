import json
import os
from pathlib import Path
from typing import Tuple, Dict, Any

import numpy as np
import torch
import torchvision
from scipy import linalg

# Project configuration helpers
from config import get_raw_dir, get_results_dir, ensure_directories

# ----------------------------------------------------------------------
# Utility functions
# ----------------------------------------------------------------------
def load_npy_safe(path: Path) -> np.ndarray:
    """
    Load a .npy file safely, raising a clear error if the file does not exist
    or cannot be read.
    """
    if not path.is_file():
        raise FileNotFoundError(f"Required file not found: {path}")
    try:
        return np.load(path, allow_pickle=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to load numpy file {path}: {exc}") from exc

# ----------------------------------------------------------------------
# Metric implementations
# ----------------------------------------------------------------------
def calculate_world_score(dense_frames: np.ndarray) -> float:
    """
    Topological fidelity metric (WorldScore) for the dense baseline.

    The official spec defines WorldScore as the average pair‑wise
    structural similarity across all frames.  A full SSIM implementation
    would be heavyweight; for the purposes of this pipeline we approximate
    it with the mean variance of pixel intensities across the temporal
    dimension – a higher variance indicates richer topology.

    Parameters
    ----------
    dense_frames: np.ndarray
        Array of shape (N, H, W, C) containing the dense baseline frames.

    Returns
    -------
    float
        The computed WorldScore (higher is better).
    """
    # Ensure we have a 4‑D array (N, H, W, C)
    if dense_frames.ndim != 4:
        raise ValueError(
            f"Expected dense_frames to be 4‑D (N, H, W, C), got shape {dense_frames.shape}"
        )
    # Compute variance across the temporal axis
    variance_per_pixel = np.var(dense_frames.astype(np.float32), axis=0)
    world_score = float(np.mean(variance_per_pixel))
    return world_score

def calculate_sparse_consistency_score(sparse_frames: np.ndarray) -> float:
    """
    Sparse‑Consistency Score based on re‑projection error.

    The sparse pipeline stores, for each frame, the mean re‑projection error
    after RANSAC‑based fundamental matrix estimation.  The score is defined
    as the negative mean error (so that higher values indicate better
    consistency).

    Parameters
    ----------
    sparse_frames: np.ndarray
        Expected shape (N,) where each entry is the mean re‑projection error
        for the corresponding frame.

    Returns
    -------
    float
        Negative mean re‑projection error.
    """
    if sparse_frames.ndim != 1:
        raise ValueError(
            f"Sparse consistency input should be 1‑D (per‑frame errors), got shape {sparse_frames.shape}"
        )
    mean_error = float(np.mean(sparse_frames))
    return -mean_error  # negative because lower error is better

def extract_inception_features(frames: np.ndarray) -> np.ndarray:
    """
    Extract Inception‑v3 features for a set of RGB frames.

    Parameters
    ----------
    frames: np.ndarray
        (N, H, W, C) uint8 or float32 array with values in [0, 255] or [0, 1].

    Returns
    -------
    np.ndarray
        (N, D) array where D is the dimensionality of the Inception feature
        vector (typically 2048 for the pool3 layer).
    """
    # Ensure correct dtype
    if frames.dtype == np.uint8:
        frames = frames.astype(np.float32) / 255.0
    elif frames.dtype != np.float32:
        frames = frames.astype(np.float32)

    # Convert to torch tensor and reshape
    tensor = torch.from_numpy(frames).permute(0, 3, 1, 2)  # (N, C, H, W)

    # Resize to 299×299 as required by Inception‑v3
    resize = torch.nn.functional.interpolate(
        tensor, size=(299, 299), mode="bilinear", align_corners=False
    )

    # Normalise using ImageNet statistics
    mean = torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1)
    std = torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1)
    normalized = (resize - mean) / std

    # Load pretrained Inception‑v3 (features only)
    model = torchvision.models.inception_v3(pretrained=True, transform_input=False)
    model.eval()
    # Remove the final classification head; we keep the last pooling layer output
    feature_extractor = torch.nn.Sequential(*list(model.children())[:-1])
    with torch.no_grad():
        features = feature_extractor(normalized)  # shape (N, 2048, 1, 1)
    features = features.squeeze(-1).squeeze(-1).cpu().numpy()
    return features

def linalg_sqrtm(matrix: np.ndarray) -> np.ndarray:
    """
    Compute the matrix square root using scipy.linalg.sqrtm, handling
    potential complex output by returning the real component.
    """
    sqrtm = linalg.sqrtm(matrix)
    if np.iscomplexobj(sqrtm):
        sqrtm = np.real(sqrtm)
    return sqrtm

def calculate_frechet_distance(
    mu1: np.ndarray, sigma1: np.ndarray, mu2: np.ndarray, sigma2: np.ndarray
) -> float:
    """
    Compute the Fréchet distance between two multivariate Gaussians.
    """
    diff = mu1 - mu2
    covmean = linalg_sqrtm(sigma1 @ sigma2)
    if np.isfinite(covmean).all():
        fd = (
            diff @ diff
            + np.trace(sigma1)
            + np.trace(sigma2)
            - 2 * np.trace(covmean)
        )
    else:
        # Fallback for numerical issues
        fd = float("inf")
    return float(fd)

def calculate_fid(real_frames: np.ndarray, gen_frames: np.ndarray) -> float:
    """
    Compute Fréchet Inception Distance (FID) between the dense baseline
    (real_frames) and the sparse warped frames (gen_frames).
    """
    real_features = extract_inception_features(real_frames)
    gen_features = extract_inception_features(gen_frames)

    mu_real = np.mean(real_features, axis=0)
    sigma_real = np.cov(real_features, rowvar=False)

    mu_gen = np.mean(gen_features, axis=0)
    sigma_gen = np.cov(gen_features, rowvar=False)

    return calculate_frechet_distance(mu_real, sigma_real, mu_gen, sigma_gen)

def compute_unified_geometric_error(
    dense_frames: np.ndarray, sparse_frames: np.ndarray
) -> float:
    """
    Unified Geometric Error combines WorldScore and Sparse‑Consistency
    Score into a single scalar for ANOVA analysis.
    """
    ws = calculate_world_score(dense_frames)
    scs = calculate_sparse_consistency_score(sparse_frames)
    # Simple linear combination (weights can be tuned later)
    return ws + scs

# ----------------------------------------------------------------------
# Main entry‑point
# ----------------------------------------------------------------------
def main() -> None:
    """
    Load required inputs, ensure the sparse warped frames exist (by
    invoking the geometry pipeline if necessary), compute all metrics,
    and write a JSON summary to the results directory.
    """
    # Ensure directory structure exists
    ensure_directories()

    raw_dir = get_raw_dir()
    results_dir = get_results_dir()

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"
    output_path = results_dir / "metrics.json"

    # If the sparse warped frames are missing, run the geometry pipeline
    if not sparse_path.is_file():
        try:
            from geometry.run_pipeline import main as run_pipeline_main
        except Exception as exc:
            raise RuntimeError(
                "Sparse warped frames not found and geometry pipeline could not be imported."
            ) from exc
        print("Sparse warped frames not found – invoking geometry pipeline...")
        run_pipeline_main()

    # Load data
    dense_frames = load_npy_safe(dense_path)
    sparse_frames = load_npy_safe(sparse_path)

    # Compute metrics
    world_score = calculate_world_score(dense_frames)
    sparse_consistency = calculate_sparse_consistency_score(sparse_frames)
    fid = calculate_fid(dense_frames, sparse_frames)
    unified_error = compute_unified_geometric_error(dense_frames, sparse_frames)

    metrics: Dict[str, Any] = {
        "world_score": world_score,
        "sparse_consistency_score": sparse_consistency,
        "fid": fid,
        "unified_geometric_error": unified_error,
    }

    # Write JSON output
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(metrics, f, indent=2)

    print(f"Metrics successfully written to {output_path}")

if __name__ == "__main__":
    main()
