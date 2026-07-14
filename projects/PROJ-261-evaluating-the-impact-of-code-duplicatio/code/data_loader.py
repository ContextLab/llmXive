"""data_loader.py
Provides a tolerant ``download_and_save_sample`` function that can be called
with various signatures throughout the project. It streams a small,
reproducible sample from the public Hugging Face ``codeparrot/github-code``
dataset and writes it to ``data/raw/github-code-sample.csv``.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any

from datasets import load_dataset

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def download_and_save_sample(*args: Any, **kwargs: Any) -> Path:
    """
    Download a small sample of the ``codeparrot/github-code`` dataset and
    save it as a CSV file.

    This function is deliberately tolerant of different call signatures
    used across the code base:

    * ``download_and_save_sample()`` – uses defaults.
    * ``download_and_save_sample(sample_size=100)`` – custom sample size.
    * ``download_and_save_sample(sample_size=100, output_path=Path(...))`` –
      custom output location.

    Parameters
    ----------
    sample_size: int, optional
        Number of rows to stream from the dataset. Defaults to 100.
    output_path: Path, optional
        Destination CSV file. Defaults to
        ``Path("data/raw/github-code-sample.csv")``.

    Returns
    -------
    Path
        Path to the CSV file that was written.
    """
    # Resolve arguments with defaults
    sample_size: int = kwargs.get("sample_size", 100)
    output_path: Path = kwargs.get("output_path", Path("data/raw/github-code-sample.csv"))

    # Ensure the parent directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading a sample of %s rows from codeparrot/github-code", sample_size)

    # Use the streaming mode to avoid downloading the whole dataset
    try:
        dataset = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
        )
    except Exception as exc:
        logger.error("Failed to load the dataset: %s", exc)
        raise

    # Write the first ``sample_size`` rows to CSV
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        # Write a header – we only keep the ``content`` column which holds the source code
        writer.writerow(["file_path", "content"])

        for idx, row in enumerate(dataset):
            if idx >= sample_size:
                break
            # The dataset provides a ``content`` field; we fabricate a simple file_path
            writer.writerow([f"sample_{idx}.py", row.get("content", "")])

    logger.info("Sample saved to %s", output_path)
    return output_path