"""
data_loader.py
---------------
Downloads a small, reproducible sample of the ``codeparrot/github-code`` dataset
and stores it as a CSV suitable for the rest of the pipeline.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Mapping

from datasets import LoadDatasetError, load_dataset

logger = logging.getLogger(__name__)

def download_and_save_sample(
    sample_size: int = 100,
    output_path: Path | None = None,
    *args,
    **kwargs,
) -> None:
    """
    Stream a subset of the ``codeparrot/github-code`` dataset and write it to CSV.

    The function is tolerant of old call‑signatures:
    * Positional arguments are interpreted as ``sample_size`` then ``output_path``.
    * Keyword arguments ``sample_size`` and ``output_path`` are also accepted.

    The CSV has two columns:
    ``file_path`` – a synthetic identifier for the snippet,
    ``code``      – the raw source code string.
    """
    # Resolve legacy positional arguments
    if args:
        if len(args) >= 1 and sample_size == 100:
            sample_size = args[0]
        if len(args) >= 2 and output_path is None:
            output_path = args[1]

    # Resolve possible keyword arguments passed via **kwargs
    if "sample_size" in kwargs:
        sample_size = kwargs["sample_size"]
    if "output_path" in kwargs:
        output_path = kwargs["output_path"]

    if output_path is None:
        output_path = Path("data/raw/github-code-sample.csv")

    logger.info("Downloading %d examples from codeparrot/github-code → %s", sample_size, output_path)

    try:
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
        )
    except LoadDatasetError as exc:
        logger.error("Failed to load dataset: %s", exc)
        raise

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "code"])
        writer.writeheader()
        count = 0
        for i, item in enumerate(dataset):
            # The dataset schema includes a ``content`` field with the source code.
            code = item.get("content") or item.get("code") or ""
            if not isinstance(code, str):
                continue
            writer.writerow({"file_path": f"snippet_{i}", "code": code})
            count += 1
            if count >= sample_size:
                break

    logger.info("Saved %d code snippets to %s", count, output_path)
