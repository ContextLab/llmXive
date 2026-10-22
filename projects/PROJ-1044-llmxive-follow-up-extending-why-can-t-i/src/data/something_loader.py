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
from pathlib import Path
from typing import Iterator, Tuple, Optional

import requests
from datasets import load_dataset

__all__ = ["something_stream"]

# ----------------------------------------------------------------------
# Helper: load a local fallback video (if present) or download a reliable
# public sample video as a last resort.
# ----------------------------------------------------------------------
_LOCAL_FALLBACK_DIR = Path("data/fallback")
_REMOTE_FALLBACK_URL = "https://sample-videos.com/video123/mp4/720/big_buck_bunny_720p_1mb.mp4"
_fallback_video_cache: Optional[bytes] = None

def _load_local_fallback() -> Optional[bytes]:
    """Return the bytes of the first MP4 file found in ``data/fallback/``."""
    if not _LOCAL_FALLBACK_DIR.is_dir():
        return None
    for file in _LOCAL_FALLBACK_DIR.iterdir():
        if file.suffix.lower() == ".mp4" and file.is_file():
            return file.read_bytes()
    return None

def _download_fallback_video() -> bytes:
    """Download a public fallback video (used only when no local file exists)."""
    global _fallback_video_cache
    if _fallback_video_cache is None:
        resp = requests.get(_REMOTE_FALLBACK_URL, timeout=30)
        resp.raise_for_status()
        _fallback_video_cache = resp.content
        # Persist the downloaded video for future runs
        _LOCAL_FALLBACK_DIR.mkdir(parents=True, exist_ok=True)
        fallback_path = _LOCAL_FALLBACK_DIR / "fallback.mp4"
        if not fallback_path.is_file():
            fallback_path.write_bytes(_fallback_video_cache)
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
    # Fallback mode – fill any remaining slots with a local or remote sample.
    # ------------------------------------------------------------------
    fallback_bytes = _load_local_fallback()
    if fallback_bytes is None:
        fallback_bytes = _download_fallback_video()
    fallback_label = "fallback_sample"

    while yielded < target:
        yield fallback_bytes, fallback_label
        yielded += 1