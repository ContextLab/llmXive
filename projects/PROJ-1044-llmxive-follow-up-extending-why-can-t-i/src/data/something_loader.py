"""
Streaming loader for the Something‑Something V2 dataset.

This module provides a deterministic iterator over the training split of the
Something-Something V2 dataset via HuggingFace datasets. Each yielded item is 
a tuple (video_bytes, label).
"""

from __future__ import annotations

import random
from typing import Iterator, Tuple, Optional

import requests
from datasets import load_dataset

__all__ = ["something_stream"]

def _load_something_dataset() -> "datasets.Dataset":
    """
    Load the Something‑Something V2 dataset with a robust fallback.
    Prioritizes the 'something-something' dataset with 'v2' config as it is 
    the standard HuggingFace structure.
    """
    # Attempt 1: Standard multi-config dataset
    try:
        return load_dataset(
            "something-something",
            name="v2",
            split="train",
            streaming=True,
        )
    except Exception as exc1:
        # Attempt 2: Direct identifier
        try:
            return load_dataset(
                "something-something-v2",
                split="train",
                streaming=True,
            )
        except Exception as exc2:
            raise RuntimeError(
                "Failed to load Something-Something V2 dataset. "
                "Tried 'something-something' (v2 config) and 'something-something-v2'. "
                "Ensure internet connectivity and HF dataset access."
            ) from exc2

def _download_video(url: str) -> bytes:
    """
    Download the MP4 video located at url and return its raw bytes.
    """
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    data = bytearray()
    for chunk in resp.iter_content(chunk_size=8192):
        if chunk:
            data.extend(chunk)
    return bytes(data)

def something_stream(
    *,
    seed: int = 42,
    max_examples: Optional[int] = None,
) -> Iterator[Tuple[bytes, str]]:
    """
    Yield (video_bytes, label) pairs from the Something‑Something V2 training split.

    Parameters
    ----------
    seed: int, default 42
        Seed for the internal random.Random instance to ensure reproducible sampling.
    max_examples: int | None, default None
        If provided, the iterator stops after yielding max_examples items.

    Yields
    ------
    tuple[bytes, str]
        video_bytes – the raw MP4 bytes of the video.
        label – the action template string.
    """
    ds = _load_something_dataset()
    rng = random.Random(seed)

    count = 0
    for example in ds:
        if max_examples is not None and count >= max_examples:
            break

        video_url: Optional[str] = example.get("video")
        label: Optional[str] = example.get("template") or example.get("label")

        if not video_url or not label:
            continue

        # Reproducible sampling: Use the seeded RNG to decide if we keep this item.
        # We use a fixed probability (e.g., 0.1) to sample. Because the stream 
        # order is fixed and the RNG is seeded, the same videos are always picked.
        if rng.random() > 0.1:
            continue

        try:
            video_bytes = _download_video(video_url)
            yield video_bytes, label
            count += 1
        except Exception:
            # Log and skip network failures to keep the pipeline moving
            continue
