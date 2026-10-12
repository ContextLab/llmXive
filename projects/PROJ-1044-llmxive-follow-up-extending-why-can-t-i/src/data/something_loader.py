"""
Streaming loader for the Something‑Something V2 dataset.

This module provides a deterministic iterator over the training split of the
``something-something-v2`` HuggingFace dataset.  Each yielded item is a tuple
``(video_url, label)`` where ``video_url`` is a publicly‑accessible URL to the
MP4 video and ``label`` is the textual action template (e.g. ``"Putting something
onto something"``).  The iterator can be limited to a maximum number of examples
and uses a fixed random seed to make sampling reproducible.

The implementation relies on the ``datasets`` library and therefore requires
the ``datasets`` package to be listed in ``requirements.txt``.
"""

from __future__ import annotations

import random
from typing import Iterator, Tuple, Optional

from datasets import load_dataset

__all__ = ["something_stream"]


def something_stream(
    *,
    seed: int = 42,
    max_examples: Optional[int] = None,
) -> Iterator[Tuple[str, str]]:
    """
    Yield ``(video_url, label)`` pairs from the Something‑Something V2 training split.

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
    tuple[str, str]
        ``video_url`` – a string URL pointing at the MP4 video file.
        ``label`` – the action template string associated with the video.
    """
    # The HuggingFace dataset identifier for Something‑Something V2.
    ds = load_dataset(
        "something-something-v2",
        split="train",
        streaming=True,
    )

    rng = random.Random(seed)

    # The streaming dataset yields dictionaries.  The relevant keys are
    # ``video`` (a URL) and ``template`` (human‑readable action description).
    # Some versions also expose a ``label`` integer; we prefer the textual
    # template because it is deterministic and self‑contained.
    count = 0
    for example in ds:
        video_url: Optional[str] = example.get("video")
        # Prefer the textual template; fall back to ``label`` if necessary.
        label: Optional[str] = example.get("template") or example.get("label")

        if not video_url or not label:
            # Skip malformed entries – they should be extremely rare.
            continue

        # Deterministic sampling: we shuffle the order using the RNG and then
        # yield items in that shuffled order.  Because the dataset is streamed,
        # we cannot reshuffle globally, but applying ``rng.random()`` as a
        # lightweight proxy yields a reproducible subset when ``max_examples`` is
        # set.
        if max_examples is not None:
            # Accept the example with probability that ensures we roughly
            # collect ``max_examples`` items without needing a second pass.
            # The threshold is chosen conservatively.
            if rng.random() > (max_examples / (max_examples + 10)):
                continue

        yield video_url, label
        count += 1
        if max_examples is not None and count >= max_examples:
            break
