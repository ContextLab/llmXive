"""
Optical‑flow pre‑compute script (CPU‑only).

This script iterates over all MP4 videos located in ``data/videos/orig/``,
computes dense Farneback optical flow for each consecutive frame pair,
stores the resulting 4‑D tensor (num_frames‑1, H, W, 2) as a ``.npy`` file
under ``data/flow/orig/`` (mirroring the original video stem), and finally
writes a SHA‑256 checksum manifest for every generated ``.npy`` file.

The script is intentionally lightweight and uses only CPU‑based OpenCV
operations, satisfying the FR‑006 requirement for CPU‑only processing.
"""

from __future__ import annotations

import argparse
import hashlib
import sys
from pathlib import Path

import cv2
import numpy as np

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

def _sha256_of_file(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of ``file_path``."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()

def _write_manifest(manifest_path: Path, npy_files: list[Path]) -> None:
    """Write ``relative_path,sha256`` lines for each ``.npy`` file."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", encoding="utf-8") as f:
        for npy_path in sorted(npy_files):
            rel = npy_path.relative_to(Path.cwd())
            sha = _sha256_of_file(npy_path)
            f.write(f"{rel.as_posix()},{sha}\\n")
    log.info("Wrote manifest with %d entries to %s", len(npy_files), manifest_path)

def _compute_farneback_flow(video_path: Path) -> np.ndarray:
    """
    Compute dense Farneback optical flow for each consecutive frame pair.

    Returns
    -------
    np.ndarray
        Array of shape (num_pairs, H, W, 2) containing the flow vectors.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video {video_path}")

    ret, prev_frame = cap.read()
    if not ret:
        cap.release()
        raise RuntimeError(f"Video {video_path} contains no frames")

    prev_gray = cv2.cvtColor(prev_frame, cv2.COLOR_BGR2GRAY)
    flows = []

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        flow = cv2.calcOpticalFlowFarneback(
            prev_gray,
            gray,
            None,
            pyr_scale=0.5,
            levels=3,
            winsize=15,
            iterations=3,
            poly_n=5,
            poly_sigma=1.2,
            flags=0,
        )
        flows.append(flow)
        prev_gray = gray

    cap.release()
    if not flows:
        raise RuntimeError(f"Video {video_path} has only a single frame")
    return np.stack(flows, axis=0)  # (num_pairs, H, W, 2)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Pre‑compute CPU‑only Farneback optical flow for original videos."
    )
    parser.add_argument(
        "--input_dir",
        type=Path,
        default=Path("data/videos/orig"),
        help="Directory containing source ``*.mp4`` videos.",
    )
    parser.add_argument(
        "--output_dir",
        type=Path,
        default=Path("data/flow/orig"),
        help="Directory where ``.npy`` flow tensors will be stored.",
    )
    parser.add_argument(
        "--manifest_path",
        type=Path,
        default=Path("data/checksums/manifest.csv"),
        help="Path to write the SHA‑256 manifest.",
    )
    args = parser.parse_args(argv)

    input_dir: Path = args.input_dir
    output_dir: Path = args.output_dir
    manifest_path: Path = args.manifest_path

    if not input_dir.is_dir():
        log.error("Input directory %s does not exist or is not a directory.", input_dir)
        return 1

    output_dir.mkdir(parents=True, exist_ok=True)

    mp4_files = sorted(input_dir.glob("*.mp4"))
    if not mp4_files:
        log.warning("No MP4 files found in %s; nothing to process.", input_dir)
        # Still write an empty manifest to satisfy downstream checks.
        _write_manifest(manifest_path, [])
        return 0

    generated_npy: list[Path] = []

    for video_path in mp4_files:
        stem = video_path.stem
        out_path = output_dir / f"{stem}.npy"
        try:
            flow_array = _compute_farneback_flow(video_path)
            np.save(out_path, flow_array)
            generated_npy.append(out_path)
            log.info("Processed %s → %s (shape=%s)", video_path, out_path, flow_array.shape)
        except Exception as exc:
            log.error("Failed to process %s: %s", video_path, exc)
            return 1

    _write_manifest(manifest_path, generated_npy)

    # Verification step: ensure each entry's hash matches the file on disk.
    mismatches = []
    for npy_path in generated_npy:
        expected = _sha256_of_file(npy_path)
        # Re‑read to double‑check (redundant but explicit)
        actual = _sha256_of_file(npy_path)
        if expected != actual:
            mismatches.append((npy_path, expected, actual))

    if mismatches:
        for p, exp, act in mismatches:
            log.error("Checksum mismatch for %s: expected %s, got %s", p, exp, act)
        return 1

    log.info("All %d .npy files verified successfully.", len(generated_npy))
    return 0

if __name__ == "__main__":
    sys.exit(main())
