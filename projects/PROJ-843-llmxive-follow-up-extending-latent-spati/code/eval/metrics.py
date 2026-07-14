"""
Metrics computation: WorldScore, Sparse-Consistency, FID.
"""
import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple
import numpy as np
import cv2
from sklearn.metrics import pairwise_distances

from config import get_results_dir, get_raw_dir, ensure_directories

def calculate_world_score(sparse_warped_path: Path, dense_baseline_path: Path) -> float:
    """
    Compute WorldScore (topological fidelity).
    Compares sparse warped frames against dense baseline.
    """
    if not sparse_warped_path.exists() or not dense_baseline_path.exists():
        raise FileNotFoundError("Input files missing.")

    sparse_data = np.load(sparse_warped_path)
    dense_data = np.load(dense_baseline_path)

    # Handle shape mismatches by resizing or slicing
    # Ensure both are (N, H, W, C) or (N, C, H, W)
    if sparse_data.ndim == 3: sparse_data = sparse_data[:, np.newaxis, :, :]
    if dense_data.ndim == 3: dense_data = dense_data[:, np.newaxis, :, :]

    # Resize to match if necessary (simple resize for metric)
    if sparse_data.shape[2:] != dense_data.shape[2:]:
        # Resize sparse to match dense
        target_h, target_w = dense_data.shape[2], dense_data.shape[3]
        sparse_resized = []
        for i in range(len(sparse_data)):
            img = cv2.resize(sparse_data[i].transpose(1, 2, 0), (target_w, target_h))
            sparse_resized.append(img.transpose(2, 0, 1))
        sparse_data = np.stack(sparse_resized)

    # Compute correlation or MSE
    # WorldScore: 1 - (MSE / max_possible_MSE)
    mse = np.mean((sparse_data - dense_data) ** 2)
    max_val = 255.0 ** 2
    score = 1.0 - (mse / max_val)
    return max(0.0, min(1.0, score))

def calculate_sparse_consistency_score(warped_frames_path: Path) -> float:
    """
    Compute Sparse-Consistency Score (re-projection error proxy).
    Measures internal consistency of the warped frames.
    """
    if not warped_frames_path.exists():
        raise FileNotFoundError(f"File not found: {warped_frames_path}")

    data = np.load(warped_frames_path)
    if data.ndim == 3: data = data[:, np.newaxis, :, :]

    # Compute variance across frames as a proxy for consistency
    # Lower variance = higher consistency
    variance = np.var(data)
    # Normalize to 0-1 score (inverted)
    # Assuming max variance is around 255^2 / 12
    max_var = (255.0 ** 2) / 12.0
    score = 1.0 - (variance / max_var)
    return max(0.0, min(1.0, score))

def calculate_fid(features_sparse: np.ndarray, features_dense: np.ndarray) -> float:
    """
    Calculate Fréchet Inception Distance (simplified).
    """
    # Compute means and covariances
    mu1 = np.mean(features_sparse, axis=0)
    sigma1 = np.cov(features_sparse, rowvar=False)
    mu2 = np.mean(features_dense, axis=0)
    sigma2 = np.cov(features_dense, rowvar=False)

    # FID formula
    diff = mu1 - mu2
    covmean = sigma1 @ sigma2
    # Trace of sqrt
    # Simplified: trace of product
    fid = np.sum(diff ** 2) + np.trace(sigma1 + sigma2 - 2 * np.sqrt(sigma1 @ sigma2 + 1e-6))
    return float(fid)

def compute_unified_geometric_error(warped_path: Path) -> float:
    """Internal validation metric."""
    return 0.0 # Placeholder

def main():
    """CLI entry point."""
    sparse_path = get_results_dir() / "sparse_warped_frames.npy"
    dense_path = get_raw_dir() / "dense_baseline_frames.npy"

    if sparse_path.exists() and dense_path.exists():
        ws = calculate_world_score(sparse_path, dense_path)
        scs = calculate_sparse_consistency_score(sparse_path)
        print(f"WorldScore: {ws}")
        print(f"Sparse-Consistency: {scs}")
    else:
        print("Missing input files for metrics.")

if __name__ == "__main__":
    main()
