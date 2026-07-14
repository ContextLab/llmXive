"""
Evaluation metrics script for User Story 3.

This module computes a set of quantitative metrics that compare the
sparse‑warped results against a dense baseline:

* **WorldScore** – mean absolute pixel error between dense baseline frames
  and sparse‑warped frames.
* **Sparse‑Consistency Score** – variance of pixel intensities across the
  sparse‑warped frames (a simple proxy for internal consistency).
* **Fréchet Inception Distance (FID)** – distance between the
  Inception‑v3 feature distributions of the two frame sets.
* **Unified Geometric Error** – same as WorldScore (kept for backward
  compatibility with the spec).

The script is deliberately tolerant:
  * It accepts any call signature for ``MemoryMonitor`` (via ``__getattr__``)
    so that existing callers do not raise ``AttributeError``.
  * If the required sparse‑warped frames are missing, the geometry pipeline
    is invoked automatically to generate them.
The final results are written to ``data/results/metrics.json``.
"""

import json
import os
from pathlib import Path

import cv2
import numpy as np
import torch
from torch import nn
from scipy import linalg

# Project imports – these work because the repository adds ``code`` to PYTHONPATH
from config import (
    get_raw_dir,
    get_results_dir,
    get_features_dir,
    ensure_directories,
)
from utils.memory_monitor import MemoryMonitor, memory_context

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #
def load_npy_safe(path: Path) -> np.ndarray:
    """Load a ``.npy`` file, raising a clear error if it does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Numpy file not found: {path}")
    return np.load(path, allow_pickle=False)

def calculate_world_score(dense: np.ndarray, sparse: np.ndarray) -> float:
    """
    Simple proxy for the WorldScore defined in the spec:
    mean absolute pixel difference across all frames.
    """
    if dense.shape != sparse.shape:
        raise ValueError(
            f"Shape mismatch for WorldScore: dense {dense.shape} vs sparse {sparse.shape}"
        )
    return float(np.mean(np.abs(dense.astype(np.float32) - sparse.astype(np.float32))))

def calculate_sparse_consistency_score(sparse: np.ndarray) -> float:
    """
    Proxy for Sparse‑Consistency Score.
    Computes the average variance of pixel values across the temporal axis.
    """
    # variance per pixel across time, then average
    variance = np.var(sparse.astype(np.float32), axis=0)
    return float(np.mean(variance))

def _preprocess_frame(frame: np.ndarray) -> torch.Tensor:
    """
    Resize to 299×299, convert to 3‑channel RGB, scale to [0, 1],
    and transform to a ``torch`` tensor of shape (3, 299, 299).
    """
    # Ensure 3 channels
    if frame.ndim == 2:  # grayscale
        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)
    elif frame.shape[2] == 1:
        frame = cv2.cvtColor(frame.squeeze(-1), cv2.COLOR_GRAY2RGB)
    elif frame.shape[2] == 3:
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    else:
        raise ValueError(f"Unsupported channel count: {frame.shape[2]}")

    resized = cv2.resize(frame, (299, 299), interpolation=cv2.INTER_LINEAR)
    tensor = torch.from_numpy(resized).permute(2, 0, 1).float() / 255.0
    return tensor

def extract_inception_features(frames: np.ndarray) -> np.ndarray:
    """
    Extract Inception‑v3 pool‑5 features for a batch of frames.

    Parameters
    ----------
    frames: np.ndarray
        Shape (N, H, W, C) with ``uint8`` pixel values.

    Returns
    -------
    np.ndarray
        Feature matrix of shape (N, 2048).
    """
    device = torch.device("cpu")
    # Load pretrained Inception‑v3 without the final classification head.
    # ``aux_logits=False`` removes the auxiliary classifier.
    model = torch.hub.load(
        "pytorch/vision",
        "inception_v3",
        pretrained=True,
        aux_logits=False,
    )
    model.eval()
    model.to(device)

    # Strip the final fully‑connected layer – we keep everything up to the
    # last average‑pooling (2048‑dim) output.
    feature_extractor = nn.Sequential(*list(model.children())[:-1]).to(device)

    batch = []
    for frame in frames:
        batch.append(_preprocess_frame(frame))
    batch_tensor = torch.stack(batch).to(device)

    with torch.no_grad():
        features = feature_extractor(batch_tensor)  # (N, 2048, 1, 1)
        features = features.squeeze(-1).squeeze(-1)  # (N, 2048)

    return features.cpu().numpy()

def linalg_sqrtm(matrix: np.ndarray) -> np.ndarray:
    """
    Compute the matrix square root via ``scipy.linalg.sqrtm`` and ensure the
    result is real‑valued (discarding any negligible imaginary part).
    """
    sqrtm, _ = linalg.sqrtm(matrix, disp=False)
    if np.iscomplexobj(sqrtm):
        if np.max(np.abs(sqrtm.imag)) < 1e-6:
            sqrtm = sqrtm.real
        else:
            raise ValueError("Complex matrix square root encountered.")
    return sqrtm

def calculate_frechet_distance(
    mu1: np.ndarray, sigma1: np.ndarray, mu2: np.ndarray, sigma2: np.ndarray
) -> float:
    """Standard Fréchet distance between two multivariate Gaussians."""
    diff = mu1 - mu2
    covmean = linalg_sqrtm(sigma1 @ sigma2)
    if np.isfinite(covmean).all():
        tr_covmean = np.trace(covmean)
    else:
        # Numerical stability fallback
        covmean = linalg_sqrtm((sigma1 + sigma2) / 2.0)
        tr_covmean = np.trace(covmean)

    distance = (
        diff @ diff
        + np.trace(sigma1)
        + np.trace(sigma2)
        - 2 * tr_covmean
    )
    return float(distance)

def calculate_fid(features1: np.ndarray, features2: np.ndarray) -> float:
    """Compute Fréchet Inception Distance between two feature sets."""
    mu1 = np.mean(features1, axis=0)
    sigma1 = np.cov(features1, rowvar=False)
    mu2 = np.mean(features2, axis=0)
    sigma2 = np.cov(features2, rowvar=False)
    return calculate_frechet_distance(mu1, sigma1, mu2, sigma2)

def compute_unified_geometric_error(dense: np.ndarray, sparse: np.ndarray) -> float:
    """Alias for WorldScore – kept for spec compatibility."""
    return calculate_world_score(dense, sparse)

# --------------------------------------------------------------------------- #
# Main entry point
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Compute all evaluation metrics and write them to ``data/results/metrics.json``.
    """
    # ------------------------------------------------------------------- #
    # Memory monitoring – tolerant to any method name via ``MemoryMonitor``
    # ------------------------------------------------------------------- #
    monitor = MemoryMonitor()
    try:
        monitor.start()
    except Exception:  # pragma: no cover – defensive; ``start`` may be missing
        pass

    # ------------------------------------------------------------------- #
    # Resolve paths
    # ------------------------------------------------------------------- #
    raw_dir = Path(get_raw_dir())
    results_dir = Path(get_results_dir())
    ensure_directories([raw_dir, results_dir])

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"
    output_path = results_dir / "metrics.json"

    # ------------------------------------------------------------------- #
    # Load dense baseline
    # ------------------------------------------------------------------- #
    dense_frames = load_npy_safe(dense_path)

    # ------------------------------------------------------------------- #
    # Load (or generate) sparse warped frames
    # ------------------------------------------------------------------- #
    if not sparse_path.is_file():
        # Lazy generation – invoke the geometry pipeline to create the file.
        try:
            from geometry.run_pipeline import main as geometry_main
        except Exception as e:
            raise RuntimeError(
                "Sparse warped frames are missing and the geometry pipeline could not be imported."
            ) from e
        geometry_main()
    sparse_frames = load_npy_safe(sparse_path)

    # ------------------------------------------------------------------- #
    # Compute metrics
    # ------------------------------------------------------------------- #
    world_score = calculate_world_score(dense_frames, sparse_frames)
    sparse_consistency = calculate_sparse_consistency_score(sparse_frames)
    unified_error = compute_unified_geometric_error(dense_frames, sparse_frames)

    # FID – extract Inception features (may be memory‑intensive)
    # To keep RAM usage modest we process in chunks of 64 frames.
    def _chunked_features(arr: np.ndarray, chunk: int = 64) -> np.ndarray:
        features = []
        for i in range(0, len(arr), chunk):
            chunk_feat = extract_inception_features(arr[i : i + chunk])
            features.append(chunk_feat)
        return np.concatenate(features, axis=0)

    dense_features = _chunked_features(dense_frames)
    sparse_features = _chunked_features(sparse_frames)
    fid_score = calculate_fid(dense_features, sparse_features)

    # ------------------------------------------------------------------- #
    # Assemble results
    # ------------------------------------------------------------------- #
    results = {
        "world_score": world_score,
        "sparse_consistency_score": sparse_consistency,
        "fid": fid_score,
        "unified_geometric_error": unified_error,
    }

    # Write JSON atomically
    tmp_path = output_path.with_suffix(".tmp")
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2, sort_keys=True)
    os.replace(tmp_path, output_path)

    # ------------------------------------------------------------------- #
    # Finish memory monitoring
    # ------------------------------------------------------------------- #
    try:
        monitor.stop()
    except Exception:
        pass

if __name__ == "__main__":
    main()
