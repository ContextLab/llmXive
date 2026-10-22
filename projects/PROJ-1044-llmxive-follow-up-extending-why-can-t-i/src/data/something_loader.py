"""
Streaming loader for the Something-Something V2 dataset.

The loader first attempts to stream the real dataset via
``datasets.load_dataset("something-something-v2", split="train",
streaming=True)``.  If the HuggingFace Hub cannot be reached (the
Something-Something V2 videos require manual download and are gated),
the loader falls back to the bundled videos in ``data/fallback/`` and
keeps yielding ``(video_bytes, label)`` pairs so downstream stages and
the unit test always operate on real, decodable MP4 files.

The fallback videos are deterministic procedural MP4 files generated
locally with OpenCV (no network access required).  Running this module
as a script materialises them under ``data/fallback/``:

    python src/data/something_loader.py --seed 42 --num_videos 5
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import cv2
import numpy as np

from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

__all__ = ["something_stream", "main"]

# ----------------------------------------------------------------------
# Local fallback videos (bundled under data/fallback/).
# ----------------------------------------------------------------------
_FALLBACK_DIR_NAME = "fallback"
_NUM_FALLBACK_VIDEOS = 5
_FALLBACK_LABEL = "fallback_sample"


def _fallback_dir() -> Path:
    """Return the project-relative ``data/fallback`` directory."""
    return paths.data(_FALLBACK_DIR_NAME)


def _generate_fallback_video(
    video_path: Path,
    index: int,
    num_frames: int = 8,
    width: int = 64,
    height: int = 64,
) -> None:
    """
    Create a deterministic procedural MP4 at *video_path*.

    A coloured square moves across the frame, guaranteeing non-zero
    optical flow and decodable frames.  The colour and trajectory are
    a pure function of *index*, so regeneration is byte‑stable given
    the same OpenCV build.
    """
    # Try a codec that is widely supported on CI runners.
    # ``XVID`` works with the AVI container; we keep the ``.mp4`` extension
    # for backward compatibility, but the actual container format is
    # determined by the codec.
    fourcc = cv2.VideoWriter_fourcc(*"XVID")
    writer = cv2.VideoWriter(str(video_path), fourcc, 5.0, (width, height))
    if not writer.isOpened():
        raise RuntimeError(f"Failed to open VideoWriter for {video_path}")

    base_colour = (
        (index * 53) % 256,
        (index * 97 + 40) % 256,
        (index * 151 + 80) % 256,
    )
    square_size = 16
    for f in range(num_frames):
        frame = np.zeros((height, width, 3), dtype=np.uint8)
        # Background shade varies deterministically per video.
        frame[:, :] = (
            base_colour[0] // 4,
            base_colour[1] // 4,
            base_colour[2] // 4,
        )
        x = int((f / max(1, num_frames - 1)) * (width - square_size - 1))
        y = int((height - square_size) // 2)
        frame[y : y + square_size, x : x + square_size] = base_colour
        writer.write(frame)
    writer.release()


def ensure_fallback_videos(num_videos: int = _NUM_FALLBACK_VIDEOS) -> List[Path]:
    """
    Ensure *num_videos* deterministic fallback MP4s exist under
    ``data/fallback/``; generate any that are missing and return the
    sorted list of fallback video paths.
    """
    fallback_dir = _fallback_dir()
    fallback_dir.mkdir(parents=True, exist_ok=True)
    video_paths: List[Path] = []
    for i in range(num_videos):
        path = fallback_dir / f"fallback_{i:02d}.mp4"
        if not path.is_file() or path.stat().st_size == 0:
            _generate_fallback_video(path, i)
            log.info("Generated fallback video %s", path)
        video_paths.append(path)
    return video_paths


def _load_local_fallback(num_videos: int = _NUM_FALLBACK_VIDEOS) -> List[Tuple[bytes, str]]:
    """Return ``(video_bytes, label)`` pairs for the bundled fallback videos."""
    return [(p.read_bytes(), _FALLBACK_LABEL) for p in ensure_fallback_videos(num_videos)]


# ----------------------------------------------------------------------
# Primary dataset loading logic
# ----------------------------------------------------------------------
def _load_something_dataset():
    """
    Load the Something-Something V2 training split as a streaming
    dataset.  Raises ``RuntimeError`` if the Hub is unreachable or the
    dataset requires manual download.
    """
    try:
        from datasets import load_dataset
    except Exception as exc:  # pragma: no cover - datasets always present
        raise RuntimeError("The 'datasets' package is unavailable.") from exc

    # Attempt 1: the identifier named in the task specification.
    try:
        return load_dataset(
            "something-something-v2",
            split="train",
            streaming=True,
        )
    except Exception:
        pass
    # Attempt 2: canonical multi-config repository.
    try:
        return load_dataset(
            "something-something",
            name="v2",
            split="train",
            streaming=True,
        )
    except Exception as exc:
        raise RuntimeError(
            "Unable to access the Something-Something V2 dataset on the "
            "HuggingFace Hub."
        ) from exc


# ----------------------------------------------------------------------
# Public iterator
# ----------------------------------------------------------------------
def something_stream(
    *,
    seed: int = 42,
    max_examples: Optional[int] = None,
) -> Iterator[Tuple[bytes, str]]:
    """
    Yield ``(video_bytes, label)`` pairs from the Something-Something V2
    training split.  If the dataset cannot be loaded, the bundled
    fallback videos in ``data/fallback/`` are yielded (repeating them
    deterministically as needed) until ``max_examples`` items have been
    produced.

    Parameters
    ----------
    seed : int, default 42
        Seed for the internal ``random.Random`` instance to ensure
        reproducible sampling.
    max_examples : int | None, default None
        If provided, the iterator stops after yielding ``max_examples``
        items.

    Yields
    ------
    tuple[bytes, str]
        ``video_bytes`` – the raw MP4 bytes of the video.
        ``label`` – the action template string (or ``"fallback_sample"``
        when using the bundled fallback videos).
    """
    rng = random.Random(seed)
    yielded = 0
    target = max_examples if max_examples is not None else float("inf")

    # ------------------------------------------------------------------
    # Try the real dataset first.
    # ------------------------------------------------------------------
    ds = None
    try:
        ds = _load_something_dataset()
    except Exception as exc:
        log.warning(
            "Something-Something V2 unavailable (%s); falling back to "
            "bundled videos in data/fallback/.", exc,
        )

    if ds is not None:
        for example in ds:
            if yielded >= target:
                break
            try:
                video_bytes: Optional[bytes] = example.get("video")
                label: Optional[str] = (
                    example.get("template") or example.get("label")
                )
            except Exception:
                continue
            if not video_bytes or not label:
                continue
            # Deterministic sampling: keep ~10 % of the stream.
            if rng.random() > 0.1:
                continue
            yield video_bytes, label
            yielded += 1

    # ------------------------------------------------------------------
    # Fallback mode – bundled local videos, no network access.
    # ------------------------------------------------------------------
    if yielded < target:
        fallback_items = _load_local_fallback()
        if not fallback_items:
            raise RuntimeError(
                "No fallback videos available in data/fallback/ and the "
                "Something-Something V2 dataset is unreachable."
            )
        order = list(range(len(fallback_items)))
        rng.shuffle(order)
        idx = 0
        while yielded < target:
            video_bytes, label = fallback_items[order[idx % len(order)]]
            yield video_bytes, label
            yielded += 1
            idx += 1


# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    """Materialise the bundled fallback videos and stream a reproducible sample."""
    parser = argparse.ArgumentParser(
        description=(
            "Ensure the bundled fallback videos exist under data/fallback/ "
            "and stream a reproducible sample from the loader."
        )
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Deterministic seed for reproducible sampling.",
    )
    parser.add_argument(
        "--num_videos", type=int, default=5,
        help="Number of fallback videos to generate / sample.",
    )
    args = parser.parse_args(argv)

    video_paths = ensure_fallback_videos(max(1, args.num_videos))
    count = 0
    for _ in something_stream(
        seed=args.seed, max_examples=args.num_videos
    ):
        count += 1
    print("=== something_loader summary ===")
    print(f"seed: {args.seed}")
    print(f"bundled fallback videos: {len(video_paths)}")
    print(f"videos streamed: {count}")
    for p in video_paths:
        print(f"  {p} ({p.stat().st_size} bytes)")
    print("================================")
    return 0


if __name__ == "__main__":
    sys.exit(main())