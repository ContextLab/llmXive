"""
extract_frames.py

Extract frames from video clips stored in ``data/stimuli/`` (or a user‑specified
input directory) using OpenCV. By default one frame per second is extracted.
Frames are saved as JPEG files in an output directory that can be either user‑
supplied or automatically created as a temporary directory.

The script can be executed directly:

    python -m src.metrics.extract_frames --input-dir data/stimuli --output-dir /tmp/frames

If ``--output-dir`` is omitted a temporary directory is created and its path
is printed to stdout. The directory hierarchy mirrors the video filenames:

    <output_dir>/
        video_name_1/
            frame_0001.jpg
            frame_0002.jpg
            ...
        video_name_2/
            ...

The implementation purposefully avoids any synthetic data handling – it will
raise an exception if the input directory does not exist or if a video file
cannot be opened.
"""

import argparse
import os
import sys
import tempfile
from pathlib import Path
from typing import List

import cv2


SUPPORTED_VIDEO_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv"}


def is_video_file(path: Path) -> bool:
    """Return ``True`` if *path* has a supported video suffix."""
    return path.suffix.lower() in SUPPORTED_VIDEO_EXTENSIONS


def list_video_files(directory: Path) -> List[Path]:
    """Return a list of video files (supported extensions) inside *directory*."""
    if not directory.is_dir():
        raise NotADirectoryError(f"Input directory does not exist: {directory}")
    return [p for p in directory.iterdir() if p.is_file() and is_video_file(p)]


def extract_frames_from_video(video_path: Path, output_dir: Path, fps: float = 1.0) -> int:
    """
    Extract frames from *video_path* at *fps* frames per second.

    Frames are saved as JPEG files named ``frame_####.jpg`` inside *output_dir*.
    The function returns the number of frames written.

    Raises:
        RuntimeError: if the video cannot be opened.
    """
    cap = cv2.VideoCapture(str(video_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file: {video_path}")

    video_fps = cap.get(cv2.CAP_PROP_FPS)
    if video_fps <= 0:
        # Fallback: treat the video as having 1 FPS if the property is unavailable
        video_fps = 1.0

    # Compute the interval (in frames) between extracted frames
    frame_interval = max(int(round(video_fps / fps)), 1)

    output_dir.mkdir(parents=True, exist_ok=True)

    frame_idx = 0
    saved_count = 0
    while True:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % frame_interval == 0:
            # Save the current frame
            frame_filename = output_dir / f"frame_{saved_count:04d}.jpg"
            cv2.imwrite(str(frame_filename), frame)
            saved_count += 1

        frame_idx += 1

    cap.release()
    return saved_count


def process_all_videos(input_dir: Path, output_dir: Path, fps: float = 1.0) -> None:
    """
    Walk through *input_dir*, extract frames from each video, and store them
    under *output_dir* in sub‑folders named after the video stem.
    """
    video_files = list_video_files(input_dir)
    if not video_files:
        print(f"No video files found in {input_dir}", file=sys.stderr)
        return

    for video_path in video_files:
        video_output_dir = output_dir / video_path.stem
        print(f"Extracting frames from {video_path.name} → {video_output_dir}")
        extracted = extract_frames_from_video(video_path, video_output_dir, fps=fps)
        print(f"  → {extracted} frame(s) saved.")


def parse_arguments(argv: List[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract one frame per second from video clips."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        default=Path("data/stimuli"),
        help="Directory containing video clips (default: data/stimuli).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help=(
            "Directory to store extracted frames. If omitted a temporary directory "
            "is created and its path is printed to stdout."
        ),
    )
    parser.add_argument(
        "--fps",
        type=float,
        default=1.0,
        help="Number of frames to extract per second (default: 1).",
    )
    return parser.parse_args(argv)


def main(argv: List[str] | None = None) -> None:
    args = parse_arguments(argv)

    input_dir = args.input_dir
    if not input_dir.is_dir():
        print(f"Error: input directory does not exist: {input_dir}", file=sys.stderr)
        sys.exit(1)

    # Determine output directory
    if args.output_dir is None:
        # Create a temporary directory and inform the user where it lives
        output_dir = Path(tempfile.mkdtemp(prefix="extracted_frames_"))
        print(f"Created temporary output directory: {output_dir}")
    else:
        output_dir = args.output_dir
        output_dir.mkdir(parents=True, exist_ok=True)

    process_all_videos(input_dir, output_dir, fps=args.fps)


if __name__ == "__main__":
    main()