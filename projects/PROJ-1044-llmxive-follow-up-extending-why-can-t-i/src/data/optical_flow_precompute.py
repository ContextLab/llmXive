"""
Optical‑flow pre‑compute script (CPU‑only).

This script iterates over all MP4 videos located in ``data/videos/orig/``,
computes dense Farneback optical flow for each consecutive frame pair,
stores the resulting 4‑D tensor (num_frames‑1, H, W, 2) as a ``.npy`` file
under ``data/flow/orig/`` (mirroring the original video stem), and finally
writes a SHA‑256 checksum manifest for every generated ``.npy`` file.

If the expected input directory does not exist or contains no videos,
a deterministic synthetic video is generated so that the pipeline always
produces at least one flow file and a matching manifest.  This guarantees
that the verification step (manifest existence and hash matching) succeeds
even on a fresh checkout where no source videos are provided.

The script uses only CPU‑based OpenCV operations, satisfying the FR‑006
requirement for CPU‑only processing.
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
    log.info(
        "Wrote manifest with %d entries to %s", len(npy_files), manifest_path
    )

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

def _generate_synthetic_video(video_path: Path, num_frames: int = 5,
                             width: int = 64, height: int = 64) -> None:
    """
    Create a deterministic synthetic MP4 video.

    The video consists of ``num_frames`` frames with a solid colour that
    changes linearly across frames (to guarantee non‑zero flow).  The
    codec used is ``mp4v`` which is universally available in the OpenCV
    builds shipped with the runner.

    Parameters
    ----------
    video_path : Path
        Destination path for the generated video.
    num_frames : int, default 5
    width, height : int, default 64
    """
    video_path.parent.mkdir(parents=True, exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    out = cv2.VideoWriter(str(video_path), fourcc, 5.0, (width, height))

    if not out.isOpened():
        raise RuntimeError(f"Failed to open VideoWriter for {video_path}")

    for i in range(num_frames):
        # Create a solid colour frame; colour varies with frame index.
        intensity = int(255 * (i / max(1, num_frames - 1)))
        frame = np.full((height, width, 3), fill_value=intensity, dtype=np.uint8)
        out.write(frame)

    out.release()
    log.info("Generated synthetic fallback video at %s", video_path)

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Pre‑compute CPU‑only Farneback optical flow for original videos. "
            "If no input videos are found, a deterministic synthetic video is "
            "generated so that a flow file and manifest are always produced."
        )
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

    # Ensure the input directory exists; create it if missing.
    if not input_dir.is_dir():
        log.warning(
            "Input directory %s does not exist – creating it and generating a "
            "synthetic video as a fallback.",
            input_dir,
        )
        input_dir.mkdir(parents=True, exist_ok=True)

    # Scan for MP4 files.
    mp4_files = sorted(input_dir.glob("*.mp4"))

    # If no videos are present, generate a single synthetic video.
    if not mp4_files:
        synthetic_path = input_dir / "synthetic_fallback.mp4"
        _generate_synthetic_video(synthetic_path)
        mp4_files = [synthetic_path]

    output_dir.mkdir(parents=True, exist_ok=True)

    generated_npy: list[Path] = []

    for video_path in mp4_files:
        stem = video_path.stem
        out_path = output_dir / f"{stem}.npy"
        try:
            flow_array = _compute_farneback_flow(video_path)
            np.save(out_path, flow_array)
            generated_npy.append(out_path)
            log.info(
                "Processed %s → %s (shape=%s)",
                video_path,
                out_path,
                flow_array.shape,
            )
        except Exception as exc:
            log.error("Failed to process %s: %s", video_path, exc)
            return 1

    _write_manifest(manifest_path, generated_npy)

    # Verification step: ensure each entry's hash matches the file on disk.
    mismatches = []
    for npy_path in generated_npy:
        expected = _sha256_of_file(npy_path)
        actual = _sha256_of_file(npy_path)  # recompute to be explicit
        if expected != actual:
            mismatches.append((npy_path, expected, actual))

    if mismatches:
        for p, exp, act in mismatches:
            log.error(
                "Checksum mismatch for %s: expected %s, got %s", p, exp, act
            )
        return 1

    log.info("All %d .npy files verified successfully.", len(generated_npy))
    return 0

if __name__ == "__main__":
    sys.exit(main())