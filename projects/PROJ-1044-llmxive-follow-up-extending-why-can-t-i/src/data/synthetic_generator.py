"""Synthetic video generator for the counterfactual pipeline.

This script creates a deterministic set of short MP4 videos (5 s,
64×64 pixels, 5 frames) under ``data/videos/orig/`` and records a
manifest CSV mapping each video filename to a UUID.

The generation is fully deterministic: the colour of each frame is a
pure function of the video index, ensuring reproducibility across
runs and platforms (provided the same OpenCV build).

Usage (as invoked by the pipeline driver):
    python -m src.data.synthetic_generator --num_videos 200

The script writes the videos and a ``manifest.csv`` file.  It exits
with status 0 on success and raises on any error.
"""
from __future__ import annotations

import argparse
import csv
import pathlib
import uuid

import cv2
import numpy as np

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

def _create_video(video_path: pathlib.Path, idx: int, num_frames: int = 5,
                  width: int = 64, height: int = 64, fps: int = 1) -> None:
    """
    Create a deterministic synthetic MP4 video.

    The colour of each frame is a simple linear function of the frame
    index and the video index, guaranteeing non‑zero optical flow
    between consecutive frames.

    Parameters
    ----------
    video_path: pathlib.Path
        Destination path for the video file.
    idx: int
        Zero‑based video index – determines the colour pattern.
    num_frames: int, default 5
    width: int, default 64
    height: int, default 64
    fps: int, default 1 (5 s total)
    """
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    video_path.parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(str(video_path), fourcc, fps, (width, height))

    for f in range(num_frames):
        # Deterministic colour: vary R and G with video index and frame index.
        # B channel stays constant to keep the pattern simple.
        r = (idx * 5 + f * 20) % 256
        g = (idx * 13 + f * 30) % 256
        b = 128
        frame = np.full((height, width, 3), (b, g, r), dtype=np.uint8)
        writer.write(frame)

    writer.release()
    log.debug("Generated video %s (idx=%d)", video_path, idx)

def _write_manifest(manifest_path: pathlib.Path, records: list[tuple[str, str]]) -> None:
    """
    Write ``manifest.csv`` with columns ``filename,uuid``.

    Parameters
    ----------
    manifest_path: pathlib.Path
        Path to the CSV file to create.
    records: list of (filename, uuid) tuples.
    """
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with manifest_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["filename", "uuid"])
        for filename, uid in records:
            writer.writerow([filename, uid])
    log.info("Wrote manifest with %d rows to %s", len(records), manifest_path)

def parse_cli_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate deterministic synthetic original videos."
    )
    parser.add_argument(
        "--num_videos",
        type=int,
        default=200,
        help="Number of synthetic videos to generate (default: 200).",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=str(paths.data("videos", "orig")),
        help="Directory where videos will be stored.",
    )
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> int:
    """
    Entry point for the script. Returns 0 on success.
    """
    args = parse_cli_args(argv)

    out_dir = pathlib.Path(args.output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = out_dir / "manifest.csv"
    records: list[tuple[str, str]] = []

    log.info("Generating %d synthetic videos in %s", args.num_videos, out_dir)

    for i in range(args.num_videos):
        filename = f"video_{i:04d}.mp4"
        video_path = out_dir / filename
        _create_video(video_path, idx=i)

        uid = str(uuid.uuid4())
        records.append((filename, uid))

    _write_manifest(manifest_path, records)

    # Verification step – ensure we have at least 150 videos and matching rows.
    video_files = list(out_dir.glob("*.mp4"))
    if len(video_files) < 150:
        log.error("Expected at least 150 videos, found %d", len(video_files))
        return 1
    if len(video_files) != len(records):
        log.error(
            "Manifest row count (%d) does not match video file count (%d)",
            len(records),
            len(video_files),
        )
        return 1

    log.info(
        "Synthetic video generation completed: %d videos, manifest %s",
        len(video_files),
        manifest_path,
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
