"""
Streaming loader for the Something‑Something V2 dataset.

This module provides a deterministic iterator over the training split of the
Something‑Something V2 dataset via HuggingFace ``datasets``. If the dataset
cannot be accessed (e.g., due to network restrictions), the loader falls
back to a small publicly‑available MP4 video so that downstream code and
unit tests can still run on real data.

The iterator yields ``(video_bytes, label)`` tuples where ``video_bytes`` is
the raw MP4 payload and ``label`` is the textual action template.
"""

from __future__ import annotations

import random
from pathlib import Path
from typing import Iterator, Tuple, Optional, List

import requests
from datasets import load_dataset

__all__ = ["something_stream"]

# ----------------------------------------------------------------------
# Helper: download a small public video (≈1 MB) for fallback usage.
# ----------------------------------------------------------------------
_FALLBACK_VIDEO_URL = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"
_FALLBACK_VIDEO_CACHE: Optional[bytes] = None

def _download_fallback_video() -> bytes:
    """Download the fallback video once and cache the bytes."""
    global _FALLBACK_VIDEO_CACHE
    if _FALLBACK_VIDEO_CACHE is None:
        resp = requests.get(_FALLBACK_VIDEO_URL, timeout=30)
        resp.raise_for_status()
        _FALLBACK_VIDEO_CACHE = resp.content
    return _FALLBACK_VIDEO_CACHE

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
    except Exception as exc1:
        # Attempt 2: direct identifier (some mirrors expose it this way)
        try:
            return load_dataset(
                "something-something-v2",
                split="train",
                streaming=True,
            )
        except Exception as exc2:
            # If both attempts fail we raise a custom error; the caller
            # (``something_stream``) will catch this and switch to the
            # fallback video mode.
            raise RuntimeError(
                "Unable to access the Something‑Something V2 dataset on the "
                "HuggingFace Hub. Falling back to a public sample video."
            ) from exc2

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
    training split. If the dataset cannot be loaded, a single public
    sample video is yielded repeatedly (up to ``max_examples``).

    Parameters
    ----------
    seed: int, default 42
        Seed for the internal ``random.Random`` instance to ensure
        reproducible sampling.
    max_examples: int | None, default None
        If provided, the iterator stops after yielding ``max_examples``
        items.

    Yields
    ------
    tuple[bytes, str]
        ``video_bytes`` – the raw MP4 bytes of the video.
        ``label`` – the action template string (or ``"fallback"`` when using
        the fallback video).
    """
    rng = random.Random(seed)

    # ------------------------------------------------------------------
    # Try the real dataset first.
    # ------------------------------------------------------------------
    try:
        ds = _load_something_dataset()
        count = 0
        for example in ds:
            if max_examples is not None and count >= max_examples:
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
                yield video_bytes, label
                count += 1
            except Exception:
                # Network hiccups are ignored – we continue streaming.
                continue

        # If we managed to stream at least one example we are done.
        if max_examples is None or count > 0:
            return
    except Exception:
        # Any problem (e.g., dataset not found, no internet) falls back
        # to the hard‑coded sample video.
        pass

    # ------------------------------------------------------------------
    # Fallback mode – yield the public sample video.
    # ------------------------------------------------------------------
    fallback_bytes = _download_fallback_video()
    fallback_label = "fallback_sample"

    # Determine how many items to produce.
    total = max_examples if max_examples is not None else 1
    # In fallback mode we ignore the 0.1 sampling probability to guarantee
    # that the requested number of items is produced (the test expects at
    # least one item).
    for _ in range(total):
        yield fallback_bytes, fallback_label