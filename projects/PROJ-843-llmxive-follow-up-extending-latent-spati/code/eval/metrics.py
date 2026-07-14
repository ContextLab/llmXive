"""
Evaluation metrics for User Story 3.

This module implements the following public helpers (as declared in the
project's API surface):

* ``calculate_world_score`` – topological fidelity between dense baseline
  frames and sparse‑warped frames.
* ``calculate_sparse_consistency_score`` – average reprojection error for the
  sparse pipeline.
* ``extract_inception_features`` – feature extraction using a pretrained
  Inception‑v3 network (torchvision).
* ``calculate_fid`` – Fréchet Inception Distance between two feature
  distributions.
* ``compute_unified_geometric_error`` – a simple geometric error metric
  (variance of pixel values across the warped sequence).
* ``main`` – orchestrates the above, writes a JSON file
  ``data/results/metrics.json`` that downstream scripts (ANOVA,
  reporting, etc.) consume.

The implementation relies only on the public API defined in other modules
(``config`` for directory helpers, ``numpy``/``torch`` for computation) and
therefore does not break existing contracts.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Tuple

import numpy as np
import torch
from torch import nn

# Import helpers from the existing config module.
from config import (
    get_raw_dir,
    get_results_dir,
    ensure_directories,
)
from eval.download_dense_baseline import main as download_dense_baseline_main

###########################################################################
# Helper utilities
###########################################################################

def _load_npy(path: Path) -> np.ndarray:
    """Load a ``.npy`` file, raising a clear error if the file does not exist."""
    if not path.is_file():
        raise FileNotFoundError(f"Expected .npy file at {path} but it was not found.")
    return np.load(path, allow_pickle=True)

def _save_json(data: Dict[str, Any], path: Path) -> None:
    """Serialise ``data`` as pretty‑printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fp:
        json.dump(data, fp, indent=2, sort_keys=True)

###########################################################################
# Metric implementations
###########################################################################

def calculate_world_score(
    dense_frames: np.ndarray, sparse_frames: np.ndarray
) -> float:
    """
    Topological fidelity metric (WorldScore).

    The original specification (see ``spec.md``) defines WorldScore as the
    mean per‑pixel L2 distance between the dense baseline and the sparse
    reconstruction, normalised by the dynamic range of the dense frames.

    Parameters
    ----------
    dense_frames : np.ndarray
        Shape ``(N, H, W, C)`` – dense baseline video frames.
    sparse_frames : np.ndarray
        Shape ``(N, H, W, C)`` – sparse‑warped video frames.

    Returns
    -------
    float
        Normalised mean L2 distance (lower is better).
    """
    if dense_frames.shape != sparse_frames.shape:
        raise ValueError(
            f"Shape mismatch: dense {dense_frames.shape} vs sparse {sparse_frames.shape}"
        )
    diff = dense_frames.astype(np.float32) - sparse_frames.astype(np.float32)
    l2 = np.linalg.norm(diff.reshape(diff.shape[0], -1), axis=1)  # per‑frame L2
    mean_l2 = float(l2.mean())

    # Normalise by the maximum possible L2 distance (pixel range 0‑255)
    max_l2 = np.sqrt((255.0 ** 2) * dense_frames.shape[1] * dense_frames.shape[2] * dense_frames.shape[3])
    world_score = mean_l2 / max_l2
    return world_score

def calculate_sparse_consistency_score(
    sparse_frames: np.ndarray, dense_frames: np.ndarray | None = None
) -> float:
    """
    Sparse‑Consistency Score (SC‑Score).

    When a dense baseline is available we simply reuse the normalised L2
    distance (identical to ``calculate_world_score``).  When the baseline
    is not supplied we fall back to a simple intra‑sequence variance metric,
    which still captures how stable the sparse reconstruction is.

    Parameters
    ----------
    sparse_frames : np.ndarray
        Shape ``(N, H, W, C)`` – sparse‑warped frames.
    dense_frames : np.ndarray | None
        Optional dense baseline for a more faithful SC‑Score.

    Returns
    -------
    float
        Normalised error (lower is better).
    """
    if dense_frames is not None:
        return calculate_world_score(dense_frames, sparse_frames)

    # Fallback: variance across the temporal dimension
    var = np.var(sparse_frames.astype(np.float32), axis=0)  # (H, W, C)
    mean_var = float(var.mean())
    # Normalise by the variance of a full‑range image (0‑255)
    max_var = (255.0 ** 2) / 12.0  # variance of uniform[0,255]
    return mean_var / max_var

def calculate_sparse_consistency_score(sparse_frames: np.ndarray) -> float:
    """
    Convert raw ``uint8`` frames to a ``torch`` tensor suitable for Inception‑v3.

    - Rescale to ``[0, 1]``.
    - Resize to ``299×299`` (required by Inception‑v3).
    - Normalise with ImageNet statistics.
    """
    import torchvision.transforms as T  # Imported lazily to avoid hard dependency at import time

    transform = T.Compose(
        [
            T.ToPILImage(),
            T.Resize((299, 299)),
            T.ToTensor(),
            T.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
        ]
    )
    tensors = []
    for frame in frames:
        # Ensure frame is H×W×C and uint8
        if frame.dtype != np.uint8:
            frame = frame.astype(np.uint8)
        tensor = transform(frame)
        tensors.append(tensor)
    batch = torch.stack(tensors)  # shape (N, 3, 299, 299)
    return batch

def extract_inception_features(frames: np.ndarray) -> np.ndarray:
    """
    Extract Inception‑v3 ``pool3`` features for a set of video frames.

    Returns
    -------
    np.ndarray
        Shape ``(N, 2048)`` – the ``pool3`` activations for each frame.
    """
    # Lazy import to keep the module import‑lightweight.
    import torchvision.models as models

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    # Load pretrained Inception‑v3 (the model returns logits; we hook the pool3 layer)
    inception = models.inception_v3(pretrained=True, aux_logits=False, transform_input=False)
    inception.eval()
    inception.to(device)

    # Grab the pool3 output via a forward hook.
    features: list[torch.Tensor] = []

    def _hook(module: nn.Module, input: Tuple[torch.Tensor, ...], output: torch.Tensor):
        # ``output`` is the pre‑softmax logits; we need the penultimate layer.
        # In torchvision's implementation the last pooling layer is named ``Mixed_7c``
        # followed by ``AdaptiveAvgPool2d`` which yields (N, 2048, 1, 1).
        # The hook is attached to that AdaptiveAvgPool2d.
        features.append(output.squeeze(-1).squeeze(-1).detach().cpu())

    # Attach hook to the final average pooling layer.
    pooling_layer = inception.avgpool
    handle = pooling_layer.register_forward_hook(_hook)

    with torch.no_grad():
        batch = _preprocess_for_inception(frames).to(device)
        # Forward pass; the hook populates ``features``.
        _ = inception(batch)

    handle.remove()
    # ``features`` is a list of one tensor (batch) because the hook fires once.
    # Convert to a single NumPy array.
    if not features:
        raise RuntimeError("Failed to capture Inception features.")
    feats = features[0].numpy()
    return feats

def calculate_fid(features_real: np.ndarray, features_gen: np.ndarray) -> float:
    """
    Compute the Fréchet Inception Distance between two feature distributions.

    Parameters
    ----------
    features_real : np.ndarray
        Shape ``(N, D)`` – features from the dense baseline.
    features_gen : np.ndarray
        Shape ``(M, D)`` – features from the sparse reconstruction.

    Returns
    -------
    float
        The FID score (lower is better).
    """
    mu_real = np.mean(features_real, axis=0)
    mu_gen = np.mean(features_gen, axis=0)
    sigma_real = np.cov(features_real, rowvar=False)
    sigma_gen = np.cov(features_gen, rowvar=False)

    diff = mu_real - mu_gen
    covmean, _ = np.linalg.sqrtm(sigma_real @ sigma_gen, disp=False)
    if np.iscomplexobj(covmean):
        covmean = covmean.real
    covmean = covmean.numpy()

    fid = float(diff @ diff + np.trace(sigma_real + sigma_gen - 2 * covmean))
    return fid

def compute_unified_geometric_error(sparse_frames: np.ndarray) -> float:
    """
    Unified geometric error (photometric consistency) on held‑out frames.

    The metric is defined as the average temporal variance of pixel
    intensities across the warped sequence – a proxy for geometric
    stability.

    Returns
    -------
    float
        Normalised variance (lower is better).
    """
    # Compute variance over time for each pixel/channel.
    var = np.var(sparse_frames.astype(np.float32), axis=0)  # (H, W, C)
    mean_var = float(var.mean())
    # Normalise by the theoretical maximum variance of a uniform [0,255] image.
    max_var = (255.0 ** 2) / 12.0
    return mean_var / max_var

###########################################################################
# Main orchestration
###########################################################################

def main() -> None:
    """
    Compute all evaluation metrics and write them to ``data/results/metrics.json``.

    Expected input files:
    - ``data/raw/dense_baseline_frames.npy`` – dense baseline video frames.
    - ``data/results/sparse_warped_frames.npy`` – sparse‑warped frames produced
      by the geometry pipeline.

    The function is deliberately defensive: missing files raise a clear error
    so that the pipeline fails fast and the user can address the upstream
    problem.
    """
    # Resolve paths via the config helpers.
    raw_dir = Path(get_raw_dir())
    results_dir = Path(get_results_dir())
    dense_path = raw_dir / "dense_baseline_frames.npy"
    sparse_path = results_dir / "sparse_warped_frames.npy"

    # Ensure the output directory exists.
    ensure_directories(results_dir)

    # Load data.
    dense_frames = _load_npy(dense_path)
    sparse_frames = _load_npy(sparse_path)

    # ------------------------------------------------------------------ #
    # 1. WorldScore
    # ------------------------------------------------------------------ #
    world_score = calculate_world_score(dense_frames, sparse_frames)

    # ------------------------------------------------------------------ #
    # 2. Sparse‑Consistency Score
    # ------------------------------------------------------------------ #
    sparse_consistency = calculate_sparse_consistency_score(sparse_frames, dense_frames)

    # ------------------------------------------------------------------ #
    # 3. FID (requires Inception features)
    # ------------------------------------------------------------------ #
    # Feature extraction can be memory‑intensive; we process in batches of
    # at most 64 frames to stay within typical CI memory limits.
    batch_size = 64
    def _batch_features(arr: np.ndarray) -> np.ndarray:
        feats = []
        for i in range(0, len(arr), batch_size):
            batch = arr[i : i + batch_size]
            feats.append(extract_inception_features(batch))
        return np.concatenate(feats, axis=0)

    features_dense = _batch_features(dense_frames)
    features_sparse = _batch_features(sparse_frames)
    fid_score = calculate_fid(features_dense, features_sparse)

    # ------------------------------------------------------------------ #
    # 4. Unified Geometric Error
    # ------------------------------------------------------------------ #
    unified_error = compute_unified_geometric_error(sparse_frames)

    # ------------------------------------------------------------------ #
    # Assemble results
    # ------------------------------------------------------------------ #
    metrics: Dict[str, Any] = {
        "world_score": world_score,
        "sparse_consistency_score": sparse_consistency,
        "fid": fid_score,
        "unified_geometric_error": unified_error,
    }

    output_path = results_dir / "metrics.json"
    _save_json(metrics, output_path)
    print(f"Metrics written to {output_path}")

if __name__ == "__main__":
    # Allow the script to be executed directly.
    main()
