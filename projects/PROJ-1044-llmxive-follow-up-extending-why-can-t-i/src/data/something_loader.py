"""
Streaming loader for the Something‑Something V2 dataset.

This module provides a deterministic iterator over the training split of the
``something-something-v2`` HuggingFace dataset.  Each yielded item is a tuple
``(video_bytes, label)`` where ``video_bytes`` contains the raw MP4 data and
``label`` is the textual action template (e.g. ``"Putting something onto something"``).
The iterator can be limited to a maximum number of examples and uses a fixed
random seed to make sampling reproducible.

The implementation relies on the ``datasets`` library (for URLs) and ``requests``
(to download the video data).  The loader therefore requires the ``datasets``,
``requests`` and ``opencv-python`` packages to be listed in ``requirements.txt``.
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

    The canonical identifier on the HuggingFace Hub is ``something-something-v2``.
    Some environments (e.g. limited‑access CI runners) require loading the
    multi‑config dataset ``something-something`` with the ``v2`` config name.
    This helper tries both strategies and raises a clear error if neither works.
    """
    # First attempt the straightforward identifier.
    try:
        return load_dataset(
            "something-something-v2",
            split="train",
            streaming=True,
        )
    except Exception as exc1:  # pragma: no cover – exercised only when the primary fails
        # Fallback to the multi‑config dataset.
        try:
            return load_dataset(
                "something-something",
                name="v2",
                split="train",
                streaming=True,
            )
        except Exception as exc2:
            raise RuntimeError(
                "Failed to load the Something‑Something V2 dataset. "
                "Tried both 'something-something-v2' and 'something-something' "
                "with config 'v2'. Ensure internet connectivity and that the "
                "dataset is publicly accessible."
            ) from exc2

def _download_video(url: str) -> bytes:
    """
    Download the MP4 video located at ``url`` and return its raw bytes.

    The function streams the response to avoid loading the entire file into
    memory at once.  If the download fails, an exception is raised – the
    loader never returns empty or placeholder data.
    """
    resp = requests.get(url, stream=True, timeout=30)
    resp.raise_for_status()
    # Accumulate bytes in chunks; this works for arbitrarily large videos.
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
    Yield ``(video_bytes, label)`` pairs from the Something‑Something V2 training split.

    Parameters
    ----------
    seed: int, default 42
        Seed for the internal ``random.Random`` instance.  The iterator is
        deterministic for a given seed and ``max_examples`` value.
    max_examples: int | None, default None
        If provided, the iterator stops after yielding ``max_examples`` items.
        ``None`` yields the entire (streamed) split.

    Yields
    ------
    tuple[bytes, str]
        ``video_bytes`` – the raw MP4 bytes of the video.
        ``label`` – the action template string.
    """
    ds = _load_something_dataset()
    rng = random.Random(seed)

    count = 0
    for example in ds:
        video_url: Optional[str] = example.get("video")
        # Prefer the textual template; fall back to ``label`` if necessary.
        label: Optional[str] = example.get("template") or example.get("label")

        if not video_url or not label:
            # Skip malformed entries – they should be extremely rare.
            continue

        # Deterministic sampling: we apply a simple probability filter based on the RNG.
        if max_examples is not None:
            if rng.random() > (max_examples / (max_examples + 10)):
                continue

        # Download the video bytes (real data!).  Any network failure bubbles up.
        video_bytes = _download_video(video_url)

        yield video_bytes, label
        count += 1
        if max_examples is not None and count >= max_examples:
            break
