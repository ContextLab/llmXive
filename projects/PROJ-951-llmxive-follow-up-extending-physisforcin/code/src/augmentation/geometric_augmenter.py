"""
Geometric augmentation utilities for video data.

This module provides three primary functions:
  * ``apply_temporal_jitter`` – randomly speeds up or slows down a video by a
    factor within ``±jitter_percent`` of the original length.
  * ``apply_geometric_flip`` – performs a horizontal flip on every frame.
  * ``augment_video_batch`` – applies the above augmentations to a batch of
    videos (list of frames).

A small CLI ``main`` is also provided for ad‑hoc usage on a folder of MP4 files.
The implementation is deliberately lightweight and CPU‑only (no GPU
dependencies) so that it can run on the constrained execution environment used
by the pipeline.

The functions are pure (they do not write to disk) and are extensively logged
via the project's ``src.utils.logging`` utilities.  Deterministic behaviour
can be forced by calling ``set_deterministic_seed`` before invoking any
augmentation function.
"""

import argparse
import os
import random
from pathlib import Path
from typing import List, Optional

import cv2
import numpy as np

from src.utils.logging import get_logger
from src.utils.seeding import set_deterministic_seed

LOGGER = get_logger(__name__)

# --------------------------------------------------------------------------- #
# Helper utilities
# --------------------------------------------------------------------------- #

def _resample_frames(frames: List[np.ndarray], new_length: int) -> List[np.ndarray]:
    """
    Resample a list of frames to ``new_length`` using nearest‑neighbor indexing.

    Parameters
    ----------
    frames: List[np.ndarray]
        Original frames.
    new_length: int
        Desired number of frames after resampling.

    Returns
    -------
    List[np.ndarray]
        Resampled frame list.
    """
    if not frames:
        return []

    original_len = len(frames)
    if new_length == original_len:
        return frames.copy()

    # Generate equally spaced indices in the original range
    indices = np.linspace(0, original_len - 1, new_length)
    # Round to nearest integer and clip to valid range
    indices = np.clip(np.rint(indices), 0, original_len - 1).astype(int)

    return [frames[i] for i in indices]

# --------------------------------------------------------------------------- #
# Public augmentation functions
# --------------------------------------------------------------------------- #

def apply_temporal_jitter(
    video_frames: List[np.ndarray],
    jitter_percent: float = 0.10,
    *,
    rng: Optional[random.Random] = None,
) -> List[np.ndarray]:
    """
    Randomly speed up or slow down a video by up to ``jitter_percent`` of its
    original duration.

    The function chooses a speed factor uniformly from
    ``[1 - jitter_percent, 1 + jitter_percent]`` and resamples the frame list
    accordingly.

    Parameters
    ----------
    video_frames: List[np.ndarray]
        List of video frames (each frame is a ``numpy.ndarray`` as returned by
        ``cv2.VideoCapture.read``).
    jitter_percent: float, default ``0.10``
        Maximum fractional change in speed. ``0.10`` means the speed factor
        will be in the range ``[0.90, 1.10]``.
    rng: Optional[random.Random]
        Random generator to use. If ``None`` the global ``random`` module is
        used. Supplying a ``Random`` instance makes the operation deterministic
        when the same seed is set.

    Returns
    -------
    List[np.ndarray]
        The jitter‑augmented frame list.
    """
    if not video_frames:
        LOGGER.debug("Received empty video for temporal jitter – returning empty list.")
        return []

    if jitter_percent < 0 or jitter_percent > 1:
        raise ValueError("jitter_percent must be in the range [0, 1].")

    rnd = rng if rng is not None else random
    speed_factor = rnd.uniform(1.0 - jitter_percent, 1.0 + jitter_percent)
    LOGGER.debug(
        "Applying temporal jitter: original_len=%d, speed_factor=%.4f",
        len(video_frames),
        speed_factor,
    )

    new_len = max(1, int(round(len(video_frames) * speed_factor)))
    jittered_frames = _resample_frames(video_frames, new_len)
    LOGGER.debug(
        "Temporal jitter produced %d frames (target=%d).", len(jittered_frames), new_len
    )
    return jittered_frames

def apply_geometric_flip(
    video_frames: List[np.ndarray],
    flip_horizontal: bool = True,
) -> List[np.ndarray]:
    """
    Apply a geometric (horizontal) flip to every frame of a video.

    Parameters
    ----------
    video_frames: List[np.ndarray]
        List of video frames.
    flip_horizontal: bool, default ``True``
        If ``True`` perform a horizontal flip (mirror left‑right). If ``False``
        the function returns the frames unchanged.

    Returns
    -------
    List[np.ndarray]
        Flipped (or original) frames.
    """
    if not video_frames:
        LOGGER.debug("Received empty video for geometric flip – returning empty list.")
        return []

    if not flip_horizontal:
        LOGGER.debug("flip_horizontal=False – returning original frames.")
        return video_frames.copy()

    flipped = [cv2.flip(frame, 1) for frame in video_frames]
    LOGGER.debug("Applied horizontal flip to %d frames.", len(flipped))
    return flipped

def augment_video_batch(
    batch_videos: List[List[np.ndarray]],
    jitter_percent: float = 0.10,
    apply_flip: bool = True,
    *,
    rng: Optional[random.Random] = None,
) -> List[List[np.ndarray]]:
    """
    Apply temporal jitter and optional horizontal flip to a batch of videos.

    The function processes each video independently and returns a new list
    containing the augmented videos (order preserved).

    Parameters
    ----------
    batch_videos: List[List[np.ndarray]]
        A batch where each element is a list of frames representing a video.
    jitter_percent: float, default ``0.10``
        Maximum speed change for temporal jitter.
    apply_flip: bool, default ``True``
        Whether to also apply a horizontal flip.
    rng: Optional[random.Random]
        Random generator for jitter. If ``None`` the global ``random`` module
        is used.

    Returns
    -------
    List[List[np.ndarray]]
        Augmented batch of videos.
    """
    augmented_batch: List[List[np.ndarray]] = []
    for idx, frames in enumerate(batch_videos):
        LOGGER.debug("Augmenting video %d/%d", idx + 1, len(batch_videos))
        jittered = apply_temporal_jitter(
            frames, jitter_percent=jitter_percent, rng=rng
        )
        if apply_flip:
            jittered = apply_geometric_flip(jittered, flip_horizontal=True)
        augmented_batch.append(jittered)
    LOGGER.info("Augmented %d videos (jitter=%.2f, flip=%s).", len(batch_videos), jitter_percent, apply_flip)
    return augmented_batch

# --------------------------------------------------------------------------- #
# CLI entry point
# --------------------------------------------------------------------------- #

def _process_single_mp4(
    input_path: Path,
    output_path: Path,
    jitter_percent: float,
    apply_flip: bool,
    rng: random.Random,
) -> None:
    """
    Read an MP4, augment it, and write the result to ``output_path``.
    """
    LOGGER.info("Processing %s → %s", input_path, output_path)

    cap = cv2.VideoCapture(str(input_path))
    if not cap.isOpened():
        raise RuntimeError(f"Unable to open video file {input_path}")

    frames: List[np.ndarray] = []
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
    cap.release()
    LOGGER.debug("Read %d frames from %s", len(frames), input_path)

    # Apply augmentations
    aug_frames = apply_temporal_jitter(frames, jitter_percent=jitter_percent, rng=rng)
    if apply_flip:
        aug_frames = apply_geometric_flip(aug_frames, flip_horizontal=True)

    if not aug_frames:
        raise RuntimeError(f"Augmentation resulted in zero frames for {input_path}")

    # Determine codec and write video
    height, width = aug_frames[0].shape[:2]
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = 30  # reasonable default; original fps is not retained to keep it simple
    out = cv2.VideoWriter(str(output_path), fourcc, fps, (width, height))

    for frame in aug_frames:
        out.write(frame)
    out.release()
    LOGGER.info("Wrote augmented video with %d frames to %s", len(aug_frames), output_path)

def main() -> None:
    """
    Command‑line interface.

    Example
    -------
    >>> python -m src.augmentation.geometric_augmenter \\
    ...     --input-dir data/raw/videos \\
    ...     --output-dir data/augmented/videos \\
    ...     --jitter-percent 0.1 \\
    ...     --no-flip
    """
    parser = argparse.ArgumentParser(
        description="Apply temporal jitter and horizontal flip to all MP4 files in a directory."
    )
    parser.add_argument(
        "--input-dir",
        type=Path,
        required=True,
        help="Directory containing source MP4 files.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="Directory where augmented MP4 files will be written.",
    )
    parser.add_argument(
        "--jitter-percent",
        type=float,
        default=0.10,
        help="Maximum fractional speed change (e.g., 0.1 → ±10%%).",
    )
    parser.add_argument(
        "--no-flip",
        action="store_true",
        help="Disable horizontal flipping (default is to flip).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for deterministic jitter. If omitted, randomness is uncontrolled.",
    )
    args = parser.parse_args()

    # Ensure output directory exists
    args.output_dir.mkdir(parents=True, exist_ok=True)

    # Set deterministic seed if requested
    if args.seed is not None:
        set_deterministic_seed(args.seed)
        rng = random.Random(args.seed)
        LOGGER.debug("Deterministic seed set to %d", args.seed)
    else:
        rng = random.Random()

    # Process each MP4 file
    for mp4_path in sorted(args.input_dir.glob("*.mp4")):
        out_name = mp4_path.stem + "_augmented.mp4"
        out_path = args.output_dir / out_name
        _process_single_mp4(
            mp4_path,
            out_path,
            jitter_percent=args.jitter_percent,
            apply_flip=not args.no_flip,
            rng=rng,
        )

    LOGGER.info("Augmentation completed for %d files.", len(list(args.input_dir.glob("*.mp4"))))

if __name__ == "__main__":
    main()