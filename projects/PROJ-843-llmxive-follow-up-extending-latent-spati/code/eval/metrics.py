"""
Evaluation metrics for the sparse vs dense baseline comparison.

This module provides functions to compute:
- WorldScore (PSNR between dense baseline frames and sparse warped frames)
- Sparse-Consistency Score (mean SSIM)
- Fréchet Inception Distance (FID) using a simple flatten‑image feature
- Unified Geometric Error (mean L1 pixel error)

The ``main`` entry point loads the required ``.npy`` files, computes the
metrics and writes a JSON report to ``data/results/metrics.json``.
"""
import json
import os
from pathlib import Path
from typing import Tuple

import numpy as np
import torch
from skimage.metrics import structural_similarity as ssim

# Local imports – the public API of the project
from config import (
    get_raw_dir,
    get_results_dir,
    ensure_directories,
)
from eval.download_dense_baseline import main as download_dense_baseline_main

###########################################################################
# Helper utilities
# ----------------------------------------------------------------------


def _load_npy(file_path: Path) -> np.ndarray:
    """Load a ``.npy`` file and raise a clear error if it does not exist."""
    if not file_path.is_file():
        raise FileNotFoundError(f"Required file not found: {file_path}")
    return np.load(file_path, allow_pickle=True)


def _psnr(img1: np.ndarray, img2: np.ndarray, max_val: float = 255.0) -> float:
    """Peak‑Signal‑to‑Noise‑Ratio between two images."""
    mse = np.mean((img1.astype(np.float32) - img2.astype(np.float32)) ** 2)
    if mse == 0:
        return float("inf")
    return 20 * np.log10(max_val) - 10 * np.log10(mse)


def _mean_psnr(baseline: np.ndarray, warped: np.ndarray) -> float:
    """Average PSNR over a stack of frames."""
    if baseline.shape != warped.shape:
        raise ValueError("Baseline and warped arrays must have the same shape")
    psnr_vals = [_psnr(baseline[i], warped[i]) for i in range(baseline.shape[0])]
    return float(np.mean(psnr_vals))


def _mean_ssim(baseline: np.ndarray, warped: np.ndarray) -> float:
    """Average structural similarity (SSIM) over a stack of frames."""
    if baseline.shape != warped.shape:
        raise ValueError("Baseline and warped arrays must have the same shape")
    # skimage expects channel‑last uint8 images
    ssim_vals = []
    for i in range(baseline.shape[0]):
        # multichannel=True when there are 3 colour channels
        s = ssim(
            baseline[i],
            warped[i],
            data_range=255,
            multichannel=baseline.shape[-1] == 3,
        )
        ssim_vals.append(s)
    return float(np.mean(ssim_vals))


def _flatten_features(frames: np.ndarray) -> np.ndarray:
    """
    Produce a 2‑D feature matrix (N, D) from raw frames.

    For a lightweight, fully‑CPU implementation we simply flatten the
    image pixels (after converting to float and scaling to [0, 1]).
    """
    n = frames.shape[0]
    # Normalise to [0, 1] to keep the scale comparable across datasets
    flat = frames.astype(np.float32) / 255.0
    return flat.reshape(n, -1)


def _calculate_fid(features1: np.ndarray, features2: np.ndarray) -> float:
    """
    Compute the Fréchet Inception Distance (FID) between two feature
    distributions.  This implementation follows the standard formula
    using mean and covariance of the two sets of features.
    """
    mu1 = np.mean(features1, axis=0)
    mu2 = np.mean(features2, axis=0)
    sigma1 = np.cov(features1, rowvar=False)
    sigma2 = np.cov(features2, rowvar=False)

    diff = mu1 - mu2
    covmean, _ = torch.linalg.sqrtm(
        torch.from_numpy(sigma1).float() @ torch.from_numpy(sigma2).float(),
        eps=1e-6,
    ).cpu().numpy(), None

    # Numerical errors might introduce a tiny imaginary component
    if np.iscomplexobj(covmean):
        covmean = covmean.real
    covmean = covmean.numpy()

    fid = diff @ diff + np.trace(sigma1 + sigma2 - 2 * covmean)
    return float(fid)


def _mean_l1_error(baseline: np.ndarray, warped: np.ndarray) -> float:
    """Mean absolute pixel‑wise error (L1) between two stacks of frames."""
    if baseline.shape != warped.shape:
        raise ValueError("Baseline and warped arrays must have the same shape")
    return float(np.mean(np.abs(baseline.astype(np.float32) - warped.astype(np.float32))))


# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------


def calculate_world_score(dense_path: Path, sparse_path: Path) -> float:
    """
    Compute the WorldScore metric (average PSNR) between the dense baseline
    and the sparse warped frames.
    """
    dense = _load_npy(dense_path)
    sparse = _load_npy(sparse_path)
    return _mean_psnr(dense, sparse)


def calculate_sparse_consistency_score(dense_path: Path, sparse_path: Path) -> float:
    """
    Compute the Sparse‑Consistency Score (average SSIM) between the dense
    baseline and the sparse warped frames.
    """
    dense = _load_npy(dense_path)
    sparse = _load_npy(sparse_path)
    return _mean_ssim(dense, sparse)


def calculate_fid(dense_path: Path, sparse_path: Path) -> float:
    """
    Compute a Fréchet Inception Distance‑like score using flattened pixel
    vectors as a lightweight proxy for Inception features.
    """
    dense = _load_npy(dense_path)
    sparse = _load_npy(sparse_path)

    dense_feat = _flatten_features(dense)
    sparse_feat = _flatten_features(sparse)

    return _calculate_fid(dense_feat, sparse_feat)


def compute_unified_geometric_error(dense_path: Path, sparse_path: Path) -> float:
    """
    Unified Geometric Error is defined here as the mean L1 pixel error
    between dense baseline frames and sparse warped frames.
    """
    dense = _load_npy(dense_path)
    sparse = _load_npy(sparse_path)
    return _mean_l1_error(dense, sparse)


def main() -> None:
    """
    Entry point used by the quick‑start pipeline.

    It loads the required ``.npy`` files, computes all metrics and writes
    a JSON report to ``data/results/metrics.json``.
    """
    # Ensure the standard directory layout exists
    ensure_directories()

    raw_dir = get_raw_dir()
    results_dir = get_results_dir()

    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    # Compute the four metrics
    world_score = calculate_world_score(dense_path, sparse_path)
    sparse_consistency = calculate_sparse_consistency_score(dense_path, sparse_path)
    fid_score = calculate_fid(dense_path, sparse_path)
    unified_error = compute_unified_geometric_error(dense_path, sparse_path)

    # Assemble the report
    report = {
        "world_score_psnr": world_score,
        "sparse_consistency_ssim": sparse_consistency,
        "fid": fid_score,
        "unified_geometric_error_l1": unified_error,
    }

    # Write JSON – create the results directory if necessary
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "metrics.json"
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(report, f, indent=2)

    print(f"Metrics written to {out_path}")


if __name__ == "__main__":
    main()
