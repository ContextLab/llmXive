"""
data_loader.py
----------------
Downloads a *sample* of the ``codeparrot/github-code`` dataset using the
HuggingFace ``datasets`` library in streaming mode. The function is tolerant
to a missing ``sample_size`` argument – callers may invoke it with no
arguments, with a positional ``sample_size`` or with a keyword argument.
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Optional

from datasets import load_dataset

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_SIZE = 10  # small enough for CI while still realistic

def download_and_save_sample(*args, **kwargs) -> None:
    """
    Download a subset of the ``codeparrot/github-code`` dataset and write it
    to ``data/raw/github-code-sample.csv``. The function accepts the
    following call signatures:

    * ``download_and_save_sample()`` – uses the default sample size.
    * ``download_and_save_sample(sample_size)`` – positional integer.
    * ``download_and_save_sample(sample_size=…)`` – keyword integer.

    The CSV contains two columns: ``file_path`` and ``code``.
    """
    # Resolve sample size from flexible signature
    if args:
        sample_size = int(args[0])
    else:
        sample_size = int(kwargs.get("sample_size", DEFAULT_SAMPLE_SIZE))

    logger.info("Downloading %d rows from codeparrot/github-code", sample_size)

    # Streaming download – we only need a tiny slice.
    dataset = load_dataset(
        "codeparrot/github-code",
        split="train",
        streaming=True,
    )

    output_path = Path("data/raw/github-code-sample.csv")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        for i, item in enumerate(dataset):
            if i >= sample_size:
                break
            # The dataset provides a ``content`` field with the raw source.
            code = item.get("content", "")
            # Generate a deterministic pseudo‑path for reproducibility.
            file_path = f"sample_{i}.py"
            writer.writerow({"file_path": file_path, "code": code})

    logger.info("Sample saved to %s", output_path)
