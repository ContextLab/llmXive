"""
Curate meeting background video clips.

This script scans a directory containing video clips (downloaded by
``src.experiment.fetch_clips``), filters them according to technical
criteria, and writes a CSV manifest of the curated clips.

Criteria
---------
* Resolution must be at least 640 × 360 pixels.
* Duration must be **≤ 10 seconds**.

The output CSV is written to ``data/processed/curated_clips.csv`` and
contains the following columns:

* ``clip_path`` – relative path to the video file (POSIX style)
* ``width`` – video width in pixels
* ``height`` – video height in pixels
* ``duration_sec`` – video duration in seconds (float, rounded to 3 dp)

The script can be executed directly:

.. code-block:: bash

    python code/src/experiment/curate_clips.py
    # optional arguments:
    #   --input-dir  Path to the directory containing raw clips
    #   --output-csv Path to the CSV file to write (default:
    #                data/processed/curated_clips.csv)

The implementation deliberately avoids heavy third‑party video libraries;
it uses OpenCV (already a project dependency) which works in headless
environments.
"""

import argparse
import csv
import os
from pathlib import Path
from typing import List, Tuple

import cv2

# ----------------------------------------------------------------------
# Helper utilities
# ----------------------------------------------------------------------


def _get_video_properties(video_path: Path) -> Tuple[int, int, float]:
    """
    Return (width, height, duration_seconds) for a video file.

    Parameters
    ----------
    video_path: Path
        Path to the video file.

    Returns
    -------
    width: int
        Width in pixels.
    height: int
        Height in pixels.
    duration_sec: float
        Duration in seconds (rounded to 3 decimal places).

    Raises
    ------
    RuntimeError
        If the file cannot be opened or properties cannot be read.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    # Guard against missing FPS (some containers report 0)
    if fps <= 0:
        # Approximate using frame count and a fallback of 30 fps
        fps = 30.0

    duration_sec = frame_count / fps if fps else 0.0
    cap.release()
    return width, height, round(duration_sec, 3)


def _meets_criteria(width: int, height: int, duration_sec: float) -> bool:
    """
    Evaluate whether a clip satisfies the technical criteria.

    - Minimum resolution: 640 × 360
    - Maximum duration: 10 seconds
    """
    return (width >= 640) and (height >= 360) and (duration_sec <= 10.0)


# ----------------------------------------------------------------------
# Core curation logic
# ----------------------------------------------------------------------


def curate_clips(
    input_dir: Path, output_csv: Path, video_extensions: List[str] = None
) -> List[Path]:
    """
    Scan ``input_dir`` for video files, filter them, and write a CSV.

    Parameters
    ----------
    input_dir: Path
        Directory containing raw video clips.
    output_csv: Path
        Destination CSV file.
    video_extensions: list of str, optional
        File extensions to consider as videos (case‑insensitive).
        Defaults to common formats.

    Returns
    -------
    List[Path]
        List of paths (relative to the project root) for clips that
        satisfied the criteria.
    """
    if video_extensions is None:
        video_extensions = [".mp4", ".avi", ".mov", ".mkv", ".webm"]

    input_dir = input_dir.resolve()
    output_csv = output_csv.resolve()
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    curated_records = []

    for file_path in input_dir.rglob("*"):
        if not file_path.is_file():
            continue
        if file_path.suffix.lower() not in video_extensions:
            continue

        try:
            width, height, duration_sec = _get_video_properties(file_path)
        except Exception as exc:
            # Log to stdout; in a real system we would use logging.
            print(f"Skipping unreadable video {file_path}: {exc}")
            continue

        if _meets_criteria(width, height, duration_sec):
            # Store paths relative to the repository root for portability.
            rel_path = file_path.relative_to(Path.cwd())
            curated_records.append(
                {
                    "clip_path": str(rel_path).replace(os.sep, "/"),
                    "width": width,
                    "height": height,
                    "duration_sec": duration_sec,
                }
            )

    # Write CSV
    fieldnames = ["clip_path", "width", "height", "duration_sec"]
    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in curated_records:
            writer.writerow(row)

    return [Path(r["clip_path"]) for r in curated_records]

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Curate meeting background video clips."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw/clips"),
        help="Directory containing raw video clips (default: data/raw/clips).",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("data/processed/curated_clips.csv"),
        help="Path to the output CSV file (default: data/processed/curated_clips.csv).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    curated = curate_clips(args.input_dir, args.output_csv)
    print(f"Curated {len(curated)} clips → {args.output_csv}")


if __name__ == "__main__":
    main()
