"""curate_clips.py
-----------------
Implements the T032c task: filter fetched meeting background clips based
on technical criteria (resolution ≥ 640×360, duration ≤ 10 seconds) and
write a CSV manifest of the curated clips.

The script can be executed directly::

    python -m src.experiment.curate_clips \\
          --input-dir data/raw/meeting_clips \\
          --output-csv data/processed/curated_clips.csv

It expects the input directory to contain video files (any format
readable by OpenCV).  For each video, it extracts the frame width,
height, and duration (computed from frame count and FPS).  Clips that
satisfy the criteria are written to the output CSV with the following
columns:

    clip_path,width,height,duration_seconds

The implementation relies only on the public API surface already
present in the repository (standard library + ``opencv-python-headless``).
"""

import argparse
import csv
import os
from pathlib import Path
from typing import List, Tuple

import cv2


def _get_video_properties(video_path: Path) -> Tuple[int, int, float]:
    """Return (width, height, duration_seconds) of the video.

    Raises:
        RuntimeError: If the video cannot be opened or its properties are
        unavailable.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {video_path}")

    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)

    # Guard against zero or NaN fps which would cause division errors.
    if fps <= 0 or frame_count <= 0:
        cap.release()
        raise RuntimeError(
            f"Invalid FPS ({fps}) or frame count ({frame_count}) for {video_path}"
        )

    duration_seconds = frame_count / fps
    cap.release()
    return width, height, duration_seconds


def curate_clips(
    input_dir: Path, output_csv: Path, min_width: int = 640, min_height: int = 360, max_duration: float = 10.0
) -> List[Tuple[str, int, int, float]]:
    """Filter video clips according to resolution and duration constraints.

    Args:
        input_dir: Directory containing the raw video clips.
        output_csv: Destination CSV file that will contain the curated list.
        min_width: Minimum allowed video width (default 640).
        min_height: Minimum allowed video height (default 360).
        max_duration: Maximum allowed duration in seconds (default 10.0).

    Returns:
        A list of tuples ``(clip_path, width, height, duration_seconds)`` for
        all clips that satisfy the criteria.
    """
    input_dir = input_dir.expanduser().resolve()
    output_csv = output_csv.expanduser().resolve()

    if not input_dir.is_dir():
        raise FileNotFoundError(f"Input directory does not exist: {input_dir}")

    # Ensure the parent directory of the CSV exists.
    output_csv.parent.mkdir(parents=True, exist_ok=True)

    curated: List[Tuple[str, int, int, float]] = []

    # Iterate over video files.  We consider any file with a typical video
    # extension; OpenCV will attempt to open it regardless.
    video_extensions = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
    for video_path in sorted(input_dir.rglob("*")):
        if video_path.suffix.lower() not in video_extensions:
            continue  # Skip non‑video files.

        try:
            width, height, duration = _get_video_properties(video_path)
        except Exception as exc:
            # Log the failure and continue with the next file.
            print(f"[WARN] Skipping unreadable video {video_path}: {exc}")
            continue

        if width >= min_width and height >= min_height and duration <= max_duration:
            curated.append(
                (str(video_path), width, height, round(duration, 3))
            )
        else:
            # Optionally report why a clip was excluded for debugging.
            reason = []
            if width < min_width or height < min_height:
                reason.append(
                    f"resolution {width}x{height} < {min_width}x{min_height}"
                )
            if duration > max_duration:
                reason.append(f"duration {duration:.2f}s > {max_duration}s")
            print(f"[INFO] Excluding {video_path} ({', '.join(reason)})")

    # Write the CSV manifest.
    with output_csv.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["clip_path", "width", "height", "duration_seconds"])
        for row in curated:
            writer.writerow(row)

    print(f"[DONE] Curated {len(curated)} clips → {output_csv}")
    return curated


def parse_arguments() -> argparse.Namespace:
    """Parse command‑line arguments for the script."""
    parser = argparse.ArgumentParser(
        description="Curate meeting background video clips based on resolution and duration."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/raw/meeting_clips"),
        help="Directory containing raw video clips downloaded by fetch_clips.",
    )
    parser.add_argument(
        "--output-csv",
        type=Path,
        default=Path("data/processed/curated_clips.csv"),
        help="Path to the output CSV file listing curated clips.",
    )
    return parser.parse_args()


def main() -> None:
    """Entry point for ``python -m src.experiment.curate_clips``."""
    args = parse_arguments()
    curate_clips(args.input_dir, args.output_csv)


if __name__ == "__main__":
    main()