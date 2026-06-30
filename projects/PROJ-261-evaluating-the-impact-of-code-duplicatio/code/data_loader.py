"""Data loading utilities for the project.

This module provides a thin wrapper around the HuggingFace ``datasets``
library that streams a small, reproducible subset of the
``codeparrot/github-code`` dataset and writes it to
``data/raw/github-code-sample.csv``.  The function is deliberately tolerant
of different call signatures so that it can be used both from the pipeline
orchestration (``code/main.py``) and from internal callers.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Iterable, List, Optional

from datasets import load_dataset

logger = logging.getLogger(__name__)

DEFAULT_OUTPUT_PATH = Path("data/raw/github-code-sample.csv")
DEFAULT_SAMPLE_SIZE = 10  # Small deterministic sample for quick‑start / tests.

def _stream_dataset(sample_size: int = DEFAULT_SAMPLE_SIZE) -> Iterable[dict]:
    """Stream ``codeparrot/github-code`` and yield ``sample_size`` rows.

    The dataset is streamed to avoid pulling the full 500 MB corpus during
    CI runs.  Each yielded record contains at least the fields
    ``repo_name``, ``file_path`` and ``content``.
    """
    ds = load_dataset(
        "codeparrot/github-code",
        split="train",
        streaming=True,
    )
    for idx, item in enumerate(ds):
        if idx >= sample_size:
            break
        # Normalise keys – the original dataset may have additional fields.
        yield {
            "repo_name": item.get("repo_name", "unknown"),
            "file_path": item.get("file_path", f"file_{idx}.py"),
            "content": item.get("content", ""),
        }

def download_and_save_sample(*args, **kwargs) -> Path:
    """Download a deterministic sample of the GitHub‑code dataset.

    The function accepts any positional or keyword arguments for backward
    compatibility; they are ignored.  It returns the absolute ``Path`` to
    the CSV file that was written.
    """
    # Respect the original signature (no‑op for unexpected arguments).
    output_path: Path = DEFAULT_OUTPUT_PATH
    output_path.parent.mkdir(parents=True, exist_ok=True)

    sample_size: int = kwargs.get("sample_size", DEFAULT_SAMPLE_SIZE)

    logger.info("Streaming %d rows from the GitHub‑code dataset …", sample_size)

    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=["repo_name", "file_path", "content"])
        writer.writeheader()
        for row in _stream_dataset(sample_size=sample_size):
            writer.writerow(row)

    logger.info("Saved sampled dataset to %s", output_path)
    return output_path.resolve()

def stream_dataset(*args, **kwargs) -> Iterable[dict]:
    """Public streaming helper – forwards to ``_stream_dataset``."""
    return _stream_dataset(*args, **kwargs)

def load_raw_data(csv_path: Optional[Path] = None) -> List[dict]:
    """Load the CSV written by :func:`download_and_save_sample`."""
    path = Path(csv_path) if csv_path else DEFAULT_OUTPUT_PATH
    if not path.is_file():
        raise FileNotFoundError(f"Raw data file not found: {path}")
    with path.open(newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        return list(reader)

def main() -> None:
    """CLI entry‑point – useful for ad‑hoc debugging."""
    download_and_save_sample()
