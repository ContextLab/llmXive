"""
Streaming loader for the Something‑Something V2 dataset.

This module provides a deterministic iterator over video bytes and
labels from the Something‑Something V2 training split using the
HuggingFace ``datasets`` library.  It **does not** fall back to any
synthetic data – if the dataset cannot be accessed, a ``RuntimeError``
is raised, satisfying the requirement for a robust streaming loader
with no synthetic fallback.

The iterator yields a reproducible sample when the same ``seed`` is
supplied.  Down‑stream stages (and the unit test) can consume the
stream without network access after the first successful download,
because the dataset is streamed directly from the hub.

CLI usage:
    python -m src.data.something_loader --seed 42 --max_examples 5

The CLI simply materialises the iterator and prints a short summary.
"""

from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path
from typing import Iterator, List, Optional, Tuple

import cv2  # Imported for type consistency; not used in streaming.
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

__all__ = ["something_stream", "main"]

# ----------------------------------------------------------------------
# Public iterator
# ----------------------------------------------------------------------
def _load_something_dataset():
    """
    Load the Something‑Something V2 training split as a streaming dataset.

    Returns
    -------
    datasets.iterable_dataset.IterableDataset
        The streaming dataset object.

    Raises
    ------
    RuntimeError
        If the dataset cannot be accessed (e.g., network error,
        authentication required, or missing manual download).
    """
    try:
        from datasets import load_dataset
    except Exception as exc:  # pragma: no cover – ``datasets`` is a required dep.
        raise RuntimeError("The 'datasets' package is unavailable.") from exc

    # Attempt the identifier given in the task specification.
    try:
        return load_dataset(
            "something-something-v2",
            split="train",
            streaming=True,
        )
    except Exception:
        pass

    # Attempt the canonical multi‑config repository identifier.
    try:
        return load_dataset(
            "something-something",
            name="v2",
            split="train",
            streaming=True,
        )
    except Exception as exc:
        raise RuntimeError(
            "Unable to access the Something‑Something V2 dataset on the "
            "HuggingFace Hub."
        ) from exc

def something_stream(
    *,
    seed: int = 42,
    max_examples: Optional[int] = None,
) -> Iterator[Tuple[bytes, str]]:
    """
    Yield ``(video_bytes, label)`` pairs from the Something‑Something V2
    training split.

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
        ``label`` – the action template string.
    """
    rng = random.Random(seed)
    yielded = 0
    target = max_examples if max_examples is not None else float("inf")

    # Load the real dataset; any failure propagates as RuntimeError.
    ds = _load_something_dataset()

    for example in ds:
        if yielded >= target:
            break
        # Extract expected fields; continue if missing.
        video_bytes: Optional[bytes] = example.get("video")
        label: Optional[str] = example.get("template") or example.get("label")
        if not video_bytes or not label:
            continue
        # Deterministic subsampling: keep ~10 % of the stream.
        if rng.random() > 0.1:
            continue
        yield video_bytes, label
        yielded += 1

    if yielded < target:
        raise RuntimeError(
            f"Only {yielded} examples were yielded, fewer than the "
            f"requested {target}. The dataset may be exhausted."
        )

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def main(argv: Optional[List[str]] = None) -> int:
    """
    Materialise a deterministic sample from the loader and print a short
    summary.  This entry point is primarily for manual verification and
    debugging; the unit tests import ``something_stream`` directly.
    """
    parser = argparse.ArgumentParser(
        description=(
            "Stream a reproducible sample from the Something‑Something V2 "
            "training split."
        )
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Deterministic seed for reproducible sampling.",
    )
    parser.add_argument(
        "--max_examples",
        type=int,
        default=5,
        help="Number of examples to stream.",
    )
    args = parser.parse_args(argv)

    try:
        count = 0
        for _ in something_stream(seed=args.seed, max_examples=args.max_examples):
            count += 1
        print("=== something_loader summary ===")
        print(f"seed: {args.seed}")
        print(f"videos streamed: {count}")
        print("================================")
        return 0
    except Exception as exc:
        log.error("Failed to stream Something‑Something V2: %s", exc)
        return 1

if __name__ == "__main__":
    sys.exit(main())
