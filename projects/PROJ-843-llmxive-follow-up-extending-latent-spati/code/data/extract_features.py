"""
Sparse feature extraction utilities.

Public API:
  * ``load_sequence_frames`` – load image file paths for a sequence.
  * ``extract_sparse_features`` – compute SIFT/ORB keypoints & descriptors.
  * ``is_fast_sequence`` – heuristic to decide whether a sequence is “fast”.
  * ``process_sequence`` – end‑to‑end processing for a single sequence.
  * ``main`` – entry‑point used by the orchestrator.
"""

import os
import sys
import json
import cv2
import numpy as np
from pathlib import Path
from typing import List, Tuple

# Configuration helpers – now return ``Path`` objects.
from config import get_stratified_dir, get_features_dir, ensure_directories

# ----------------------------------------------------------------------
def load_sequence_frames(seq_dir: Path) -> List[Path]:
    """
    Return a list of image file paths (sorted) for the given sequence
    directory.  Supports common image extensions.
    """
    img_exts = {".png", ".jpg", ".jpeg", ".bmp", ".tiff"}
    frames = sorted(
        p for p in seq_dir.iterdir() if p.suffix.lower() in img_exts
    )
    if not frames:
        raise FileNotFoundError(f"No image frames found in {seq_dir}")
    return frames

# ----------------------------------------------------------------------
def extract_sparse_features(
    image_path: Path,
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Extract sparse SIFT (or ORB as a fallback) keypoints and descriptors
    from a single image.

    Returns
    -------
    coords : np.ndarray, shape (N, 2)
        ``(x, y)`` pixel coordinates of the keypoints.
    descs : np.ndarray, shape (N, D)
        Descriptor vectors.
    """
    img = cv2.imread(str(image_path), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError(f"Unable to read image {image_path}")

    # Prefer SIFT (available in recent OpenCV builds); fall back to ORB.
    if hasattr(cv2, "SIFT_create"):
        detector = cv2.SIFT_create()
    else:
        detector = cv2.ORB_create()

    keypoints, descriptors = detector.detectAndCompute(img, None)
    if not keypoints or descriptors is None:
        # Return empty arrays rather than crashing – downstream code can
        # decide how to treat low‑density frames.
        return np.empty((0, 2), dtype=np.float32), np.empty((0, 0), dtype=np.float32)

    coords = np.array([kp.pt for kp in keypoints], dtype=np.float32)
    return coords, descriptors

# ----------------------------------------------------------------------
def is_fast_sequence(seq_dir: Path) -> bool:
    """
    Very lightweight heuristic: if the number of frames is greater than
    a threshold, we label the sequence as “fast”.  This mirrors the
    specification that fast sequences may have low feature density.
    """
    try:
        frames = load_sequence_frames(seq_dir)
    except FileNotFoundError:
        return False
    return len(frames) > 30  # arbitrary threshold for demo purposes

# ----------------------------------------------------------------------
def process_sequence(seq_dir: Path, out_dir: Path) -> None:
    """
    Extract sparse features for every frame in ``seq_dir`` and store them
    as ``<frame_name>.npz`` under ``out_dir``.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    frames = load_sequence_frames(seq_dir)

    for frame_path in frames:
        coords, descs = extract_sparse_features(frame_path)
        # Store both arrays; downstream code expects ``coords`` and
        # ``descriptors`` keys.
        out_file = out_dir / f"{frame_path.stem}.npz"
        np.savez_compressed(out_file, coords=coords, descriptors=descs)

# ----------------------------------------------------------------------
def main() -> None:
    """
    Orchestrator entry‑point – walks through the stratified dataset and
    extracts features for each sequence.
    """
    stratified_dir: Path = get_stratified_dir()
    features_dir: Path = get_features_dir()

    ensure_directories([features_dir])

    # The stratified directory contains four sub‑folders (the strata).
    for stratum in stratified_dir.iterdir():
        if not stratum.is_dir():
            continue
        for seq in stratum.iterdir():
            if not seq.is_dir():
                continue
            out_seq_dir = features_dir / stratum.name / seq.name
            try:
                process_sequence(seq, out_seq_dir)
            except Exception as exc:
                print(
                    f"[extract_features] Skipping sequence {seq} due to error: {exc}",
                    file=sys.stderr,
                )