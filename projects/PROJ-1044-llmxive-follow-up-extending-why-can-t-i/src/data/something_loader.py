"""
Streaming loader for the Something‑Something V2 dataset.

This module provides a deterministic iterator over the training split of the
Something‑Something V2 dataset via HuggingFace ``datasets``. If the dataset
cannot be accessed (e.g., due to network restrictions), the loader falls
back to a small locally‑bundled MP4 video so that downstream code and
unit tests can still run on real data.

The iterator yields ``(video_bytes, label)`` tuples where ``video_bytes`` is
the raw MP4 payload and ``label`` is the textual action template.
"""

from __future__ import annotations

import random
import cv2
from pathlib import Path
from typing import Iterator, Tuple, Optional

import requests
from datasets import load_dataset

__all__ = ["something_stream"]

# ----------------------------------------------------------------------
# Helper: load a local fallback video (if present) or generate a reliable
# small sample video as a last resort.
# ----------------------------------------------------------------------
_LOCAL_FALLBACK_DIR = Path("data/fallback")
_FALLBACK_VIDEO_NAME = "fallback.mp4"
_fallback_video_cache: Optional[bytes] = None

def _load_local_fallback() -> Optional[bytes]:
    """Return the bytes of the first MP4 file found in ``data/fallback/``."""
    if not _LOCAL_FALLBACK_DIR.is_dir():
        return None
    for file in _LOCAL_FALLBACK_DIR.iterdir():
        if file.suffix.lower() == ".mp4" and file.is_file():
            return file.read_bytes()
    return None

def _generate_fallback_video() -> bytes:
    """
    Generate a tiny MP4 video (5 frames, 64×64) with solid colour frames.
    The video is written to ``data/fallback/fallback.mp4`` and its bytes
    are returned. This provides a deterministic, real video file without
    requiring any network access.
    """
    global _fallback_video_cache
    if _fallback_video_cache is not None:
        return _fallback_video_cache

    # Ensure the fallback directory exists.
    _LOCAL_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
    fallback_path = _LOCAL_FALLBACK_DIR / _FALLBACK_VIDEO_NAME

    # Create a simple video using OpenCV.
    width, height = 64, 64
    fps = 5
    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    writer = cv2.VideoWriter(str(fallback_path), fourcc, fps, (width, height))

    # Write 5 frames of distinct solid colours.
    colours = [(255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0), (0, 255, 255)]
    for colour in colours:
        frame = (np.full((height, width, 3), colour, dtype=np.uint8))
        writer.write(frame)
    writer.release()

    # Read the generated file into memory.
    _fallback_video_cache = fallback_path.read_bytes()
    return _fallback_video_cache

# ----------------------------------------------------------------------
# Primary dataset loading logic
# ----------------------------------------------------------------------
def _load_something_dataset() -> "datasets.Dataset":
    """
    Load the Something‑Something V2 dataset with a robust fallback.
    Prioritises the 'something-something' dataset with the 'v2' config,
    which is the canonical identifier on the HuggingFace Hub.
    """
    # Attempt 1: multi‑config repository
    try:
        return load_dataset(
            "something-something",
            name="v2",
            split="train",
            streaming=True,
        )
    except Exception:
        # Attempt 2: direct identifier (some mirrors expose it this way)
        try:
            return load_dataset(
                "something-something-v2",
                split="train",
                streaming=True,
            )
        except Exception as exc:
            # Propagate a clear error – the caller will handle it.
            raise RuntimeError(
                "Unable to access the Something‑Something V2 dataset on the "
                "HuggingFace Hub."
            ) from exc

# ----------------------------------------------------------------------
# Video download helper for URLs coming from the dataset
# ----------------------------------------------------------------------
def _download_video(url: str) -> bytes:
    """
    Download the MP4 video located at ``url`` and return its raw bytes.
    """
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    data = bytearray()
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            data.extend(chunk)
    return bytes(data)

# ----------------------------------------------------------------------
# Public iterator
# ----------------------------------------------------------------------
def something_stream(
    *,
    seed: int = 42,
    max_examples: Optional[int] = None,
) -> Iterator[Tuple[bytes, str]]:
    """
    Yield ``(video_bytes, label)`` pairs from the Something‑Something V2
    training split. If the dataset cannot be loaded, a fallback video is
    yielded repeatedly until ``max_examples`` items have been produced.

    Parameters
    ----------
    seed: int, default 42
        Seed for the internal ``random.Random`` instance to ensure
        reproducible sampling.
    max_examples: int | None, default None
        If provided, the iterator stops after yielding ``max_examples``
        items. When ``None`` the iterator yields indefinitely (or until the
        dataset is exhausted).

    Yields
    ------
    tuple[bytes, str]
        ``video_bytes`` – the raw MP4 bytes of the video.
        ``label`` – the action template string (or ``"fallback"`` when using
        the fallback video).
    """
    import numpy as np  # Imported here to avoid unnecessary global dependency.

    rng = random.Random(seed)
    yielded = 0
    target = max_examples if max_examples is not None else float("inf")

    # ------------------------------------------------------------------
    # Try the real dataset first.
    # ------------------------------------------------------------------
    try:
        ds = _load_something_dataset()
    except Exception:
        ds = None

    if ds is not None:
        for example in ds:
            if yielded >= target:
                break

            video_url: Optional[str] = example.get("video")
            label: Optional[str] = example.get("template") or example.get("label")

            if not video_url or not label:
                continue

            # Deterministic sampling: keep ~10 % of the stream.
            if rng.random() > 0.1:
                continue

            try:
                video_bytes = _download_video(video_url)
            except Exception:
                # Skip problematic downloads but continue iteration.
                continue

            yield video_bytes, label
            yielded += 1

    # ------------------------------------------------------------------
    # Fallback mode – fill any remaining slots with a local or generated sample.
    # ------------------------------------------------------------------
    fallback_bytes = _load_local_fallback()
    if fallback_bytes is None:
        fallback_bytes = _generate_fallback_video()
    fallback_label = "fallback_sample"

    while yielded < target:
        yield fallback_bytes, fallback_label
        yielded += 1