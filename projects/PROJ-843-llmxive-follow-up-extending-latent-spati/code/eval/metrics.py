"""
Evaluation Metrics Module
=========================

This module implements the required evaluation metrics for User Story 3:

* **WorldScore** – a simple proxy for topological fidelity of the dense baseline.
* **Sparse‑Consistency Score** – average reprojection error for the sparse pipeline.
* **Fréchet Inception Distance (FID)** – compares the distribution of Inception‑V3
  features of the dense baseline frames vs. the sparse‑warped frames.
* **Unified Geometric Error** – a combined photometric‑geometric error used by the
  downstream ANOVA / sensitivity scripts.

The implementation deliberately avoids external heavy‑weight dependencies
beyond what is already declared in ``requirements.txt`` (``torch``, ``torchvision``,
``numpy`` and the project's own ``config`` utilities).  All functions are written
to be tolerant of missing or malformed inputs – they log a clear message and
return ``None`` so that the rest of the pipeline can continue gracefully.

The script can be executed directly:

    $ python code/eval/metrics.py

which will read the required input files, compute the metrics and write a JSON
file ``data/results/metrics.json`` containing a dictionary with the following keys:

    {
        "world_score": <float>,
        "sparse_consistency_score": <float>,
        "fid": <float>,
        "unified_geometric_error": <float>
    }

The output format matches what ``code/eval/anova.py`` and ``code/eval/report.py``
expect.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple, Optional

import numpy as np
import torch
import torchvision.transforms as T
from torchvision.models import inception_v3

# Project utilities
from config import (
    get_raw_dir,
    get_results_dir,
    ensure_directories,
)

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------
def _log(message: str) -> None:
    """Very light‑weight logger – prints to stdout."""
    print(f"[metrics] {message}")

def _load_npy(path: Path) -> Optional[np.ndarray]:
    """Load a ``.npy`` file, returning ``None`` on failure."""
    try:
        arr = np.load(path, allow_pickle=False)
        _log(f"Loaded {path} (shape={arr.shape}, dtype={arr.dtype})")
        return arr
    except Exception as exc:  # pragma: no cover – defensive
        _log(f"Failed to load {path}: {exc}")
        return None

# ----------------------------------------------------------------------
# Metric implementations
# ----------------------------------------------------------------------
def calculate_world_score(dense_frames: np.ndarray) -> float:
    """
    Compute a proxy *WorldScore* for the dense baseline.

    The original paper defines WorldScore as a topological fidelity metric.
    Re‑creating the exact formulation would require additional data that is
    not part of the repository.  For the purposes of the automated pipeline
    we use a simple, deterministic surrogate:

    * For each consecutive pair of frames we compute the average per‑pixel
      L2 distance.
    * The final score is ``1 / (1 + mean_distance)`` – a higher value indicates
      more similarity (i.e. higher fidelity).

    Parameters
    ----------
    dense_frames: np.ndarray
        Shape ``(N, H, W, C)`` where ``C`` is expected to be 3 (RGB).

    Returns
    -------
    float
        The WorldScore value in the interval (0, 1].
    """
    if dense_frames.ndim != 4 or dense_frames.shape[-1] != 3:
        raise ValueError(
            "WorldScore expects frames of shape (N, H, W, 3). Got "
            f"{dense_frames.shape}"
        )
    # Compute per‑pixel L2 distance between consecutive frames
    diffs = dense_frames[1:].astype(np.float32) - dense_frames[:-1].astype(np.float32)
    l2 = np.linalg.norm(diffs.reshape(diffs.shape[0], -1), axis=1)  # (N‑1,)
    mean_l2 = float(l2.mean())
    world_score = 1.0 / (1.0 + mean_l2)
    _log(f"WorldScore computed: {world_score:.6f} (mean L2={mean_l2:.4f})")
    return world_score

def calculate_sparse_consistency_score(sparse_warped_frames: np.ndarray) -> float:
    """
    Compute a *Sparse‑Consistency Score* based on reprojection error.

    The sparse pipeline stores warped RGB frames (shape ``(N, H, W, 3)``).
    We reuse the same surrogate as WorldScore – average per‑pixel L2 distance
    between consecutive warped frames – and invert it so that lower error yields
    a higher score.

    Returns
    -------
    float
        Consistency score in (0, 1].
    """
    if sparse_warped_frames.ndim != 4 or sparse_warped_frames.shape[-1] != 3:
        raise ValueError(
            "Sparse‑Consistency expects frames of shape (N, H, W, 3). Got "
            f"{sparse_warped_frames.shape}"
        )
    diffs = sparse_warped_frames[1:].astype(np.float32) - sparse_warped_frames[:-1].astype(
        np.float32
    )
    l2 = np.linalg.norm(diffs.reshape(diffs.shape[0], -1), axis=1)
    mean_l2 = float(l2.mean())
    score = 1.0 / (1.0 + mean_l2)
    _log(
        f"Sparse‑Consistency Score computed: {score:.6f} (mean L2={mean_l2:.4f})"
    )
    return score

def _preprocess_for_inception(frames: np.ndarray) -> torch.Tensor:
    """
    Convert a batch of ``uint8`` RGB frames to the format expected by
    ``torchvision.models.inception_v3`` (3 × 299 × 299, float, normalized).

    Parameters
    ----------
    frames : np.ndarray
        Shape ``(N, H, W, 3)`` with dtype ``uint8`` or ``float`` in [0, 255].

    Returns
    -------
    torch.Tensor
        Shape ``(N, 3, 299, 299)``.
    """
    transform = T.Compose(
        [
            T.ToPILImage(),
            T.Resize((299, 299)),
            T.ToTensor(),
            T.Normalize(
                mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]
            ),
        ]
    )
    tensors = []
    for i in range(frames.shape[0]):
        img = frames[i]
        if img.dtype != np.uint8:
            img = np.clip(img, 0, 255).astype(np.uint8)
        tensors.append(transform(img))
    batch = torch.stack(tensors)  # (N, 3, 299, 299)
    return batch

def extract_inception_features(frames: np.ndarray) -> np.ndarray:
    """
    Extract Inception‑V3 features (the pool3 layer) for a set of frames.

    The function runs on CPU only (the project is CPU‑only CI).  Features are
    returned as a ``(N, D)`` NumPy array where ``D`` is the dimensionality of
    the pool3 output (2048).

    Parameters
    ----------
    frames : np.ndarray
        Shape ``(N, H, W, 3)``.

    Returns
    -------
    np.ndarray
        Feature matrix of shape ``(N, 2048)``.
    """
    _log("Extracting Inception‑V3 features...")
    device = torch.device("cpu")
    model = inception_v3(pretrained=True, transform_input=False)
    model.eval()
    model.to(device)

    # The Inception model returns a tuple (logits, aux_logits) when training;
    # in eval mode it returns logits.  We hook the pool3 layer.
    # A simple way is to replace the fully‑connected classifier with an identity
    # and take the output of the last average‑pooling layer.
    # torchvision's InceptionV3 has ``Mixed_7c`` followed by ``AdaptiveAvgPool2d``.
    # We'll forward‑pass and then access the ``avgpool`` output.
    # To keep things simple we register a forward hook.
    features = []

    def _hook(module, input, output):
        # ``output`` shape: (N, 2048, 1, 1)
        features.append(output.squeeze(-1).squeeze(-1).cpu().numpy())

    handle = model.avgpool.register_forward_hook(_hook)

    batch = _preprocess_for_inception(frames).to(device)
    with torch.no_grad():
        _ = model(batch)

    handle.remove()
    if not features:
        raise RuntimeError("Failed to capture Inception features.")
    feats = np.concatenate(features, axis=0)  # (N, 2048)
    _log(f"Inception features shape: {feats.shape}")
    return feats

def calculate_fid(features1: np.ndarray, features2: np.ndarray) -> float:
    """
    Compute the Fréchet Inception Distance between two feature distributions.

    Parameters
    ----------
    features1, features2 : np.ndarray
        Shape ``(N, D)`` where ``D`` is the feature dimensionality (2048).

    Returns
    -------
    float
        The FID value (lower is better).
    """
    if features1.ndim != 2 or features2.ndim != 2:
        raise ValueError("Feature arrays must be 2‑D.")
    mu1 = np.mean(features1, axis=0)
    mu2 = np.mean(features2, axis=0)
    sigma1 = np.cov(features1, rowvar=False)
    sigma2 = np.cov(features2, rowvar=False)

    diff = mu1 - mu2
    covmean, _ = np.linalg.sqrtm(sigma1 @ sigma2, disp=False)
    if np.iscomplexobj(covmean):
        covmean = covmean.real

    fid = float(diff @ diff + np.trace(sigma1 + sigma2 - 2 * covmean))
    _log(f"FID computed: {fid:.4f}")
    return fid

def compute_unified_geometric_error(
    sparse_warped_frames: np.ndarray, dense_frames: np.ndarray
) -> float:
    """
    Unified Geometric Error combines photometric discrepancy with geometric
    reprojection error.  For a lightweight implementation we compute the
    average L2 distance between the sparse‑warped frames and the dense baseline
    frames (after aligning the number of frames).

    Returns
    -------
    float
        Mean per‑pixel L2 error.
    """
    if sparse_warped_frames.shape != dense_frames.shape:
        # Align by truncating to the shorter sequence
        min_len = min(sparse_warped_frames.shape[0], dense_frames.shape[0])
        sparse = sparse_warped_frames[:min_len].astype(np.float32)
        dense = dense_frames[:min_len].astype(np.float32)
    else:
        sparse = sparse_warped_frames.astype(np.float32)
        dense = dense_frames.astype(np.float32)

    diff = sparse - dense
    l2 = np.linalg.norm(diff.reshape(diff.shape[0], -1), axis=1)
    mean_err = float(l2.mean())
    _log(f"Unified Geometric Error (mean L2) = {mean_err:.4f}")
    return mean_err

# ----------------------------------------------------------------------
# Main driver
# ----------------------------------------------------------------------
def main() -> None:
    """
    Entry‑point for the ``metrics`` script.

    It performs the following steps:

    1. Ensure the standard project directories exist.
    2. Load ``data/raw/dense_baseline_frames.npy``.
    3. Load ``data/results/sparse_warped_frames.npy``.
    4. Compute all metrics.
    5. Write a JSON file ``data/results/metrics.json`` with the results.
    """
    # 1. Directories
    ensure_directories()
    results_dir = get_results_dir()
    ensure_directories(results_dir)

    # 2. Load inputs
    dense_path = get_raw_dir() / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    dense_frames = _load_npy(dense_path)
    sparse_frames = _load_npy(sparse_path)

    if dense_frames is None or sparse_frames is None:
        _log("Required input files are missing – aborting metric computation.")
        return

    # 3. Compute metrics
    try:
        world_score = calculate_world_score(dense_frames)
    except Exception as exc:  # pragma: no cover
        _log(f"WorldScore computation failed: {exc}")
        world_score = None

    try:
        sparse_score = calculate_sparse_consistency_score(sparse_frames)
    except Exception as exc:  # pragma: no cover
        _log(f"Sparse‑Consistency computation failed: {exc}")
        sparse_score = None

    # FID – may be expensive; guard against failures.
    try:
        dense_feat = extract_inception_features(dense_frames)
        sparse_feat = extract_inception_features(sparse_frames)
        fid = calculate_fid(dense_feat, sparse_feat)
    except Exception as exc:  # pragma: no cover
        _log(f"FID computation failed: {exc}")
        fid = None

    try:
        unified_error = compute_unified_geometric_error(sparse_frames, dense_frames)
    except Exception as exc:  # pragma: no cover
        _log(f"Unified Geometric Error computation failed: {exc}")
        unified_error = None

    # 4. Assemble results
    metrics: Dict[str, Any] = {
        "world_score": world_score,
        "sparse_consistency_score": sparse_score,
        "fid": fid,
        "unified_geometric_error": unified_error,
    }

    # 5. Write JSON
    out_path = results_dir / "metrics.json"
    try:
        with open(out_path, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)
        _log(f"Metrics written to {out_path}")
    except Exception as exc:  # pragma: no cover
        _log(f"Failed to write metrics JSON: {exc}")

if __name__ == "__main__":
    # When invoked as a script we run the main driver.
    main()