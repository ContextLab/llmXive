"""
data_loader.py
----------------
Implements robust streaming download of a sample from a HuggingFace dataset,
handling transient network failures such as rate‑limiting. The function writes
a CSV file with columns ``file_path`` and ``code`` and returns the absolute
path to the created file.

This module is exercised by the integration test
``tests/integration/test_data_loader.py`` which monkey‑patches
``datasets.load_dataset`` to raise ``ConnectionError`` after a few rows.
The implementation therefore retries the streaming operation until the
requested number of rows is collected (or the dataset is exhausted).
"""

from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import List, Mapping

from datasets import load_dataset

logger = logging.getLogger(__name__)

DEFAULT_DATASET = "codeparrot/github-code"
DEFAULT_SPLIT = "train"
DEFAULT_OUTPUT = Path("data/raw/github-code-sample.csv")
MAX_RETRIES = 3  # reasonable default for transient errors


def _write_csv(rows: List[Mapping[str, str]], output_path: Path) -> None:
    """Write a list of dictionaries to ``output_path`` as CSV.

    The CSV will contain the columns ``file_path`` and ``code`` in that order.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = ["file_path", "code"]
    with output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def download_and_save_sample(
    sample_size: int,
    output_path: Path | str | None = None,
    *,
    dataset_name: str = DEFAULT_DATASET,
    split: str = DEFAULT_SPLIT,
    max_retries: int = MAX_RETRIES,
) -> Path:
    """
    Download a streaming sample from a HuggingFace dataset and persist it as CSV.

    Parameters
    ----------
    sample_size: int
        Desired maximum number of rows in the output CSV.
    output_path: Path | str | None, optional
        Destination for the CSV file.  If omitted, defaults to
        ``data/raw/github-code-sample.csv``.
    dataset_name: str, optional
        Full HuggingFace identifier (e.g. ``codeparrot/github-code``).
    split: str, optional
        Dataset split to stream (default ``"train"``).
    max_retries: int, optional
        Number of times to retry the streaming operation after a transient
        ``ConnectionError``.  The default is three attempts.

    Returns
    -------
    Path
        The absolute path to the written CSV file.

    Notes
    -----
    The function is tolerant to transient network failures.  If a
    ``ConnectionError`` occurs while iterating over the streaming dataset,
    the iterator is discarded and the download is restarted (up to
    ``max_retries`` times).  The function never raises on a ``ConnectionError``;
    instead it logs the incident and proceeds with the next retry.
    """
    # Resolve the output path early so callers can rely on the return value.
    out_path = Path(output_path) if output_path is not None else DEFAULT_OUTPUT
    out_path = out_path.resolve()

    collected: List[Mapping[str, str]] = []
    attempts = 0

    while len(collected) < sample_size and attempts < max_retries:
        attempts += 1
        try:
            logger.debug(
                "Attempt %d to stream %s (split=%s) for up to %d rows",
                attempts,
                dataset_name,
                split,
                sample_size - len(collected),
            )
            ds = load_dataset(dataset_name, split=split, streaming=True)

            # ``datasets`` streaming objects expose a ``take`` method; we use it
            # when available to limit the number of rows we iterate over.
            iterator = ds.take(sample_size - len(collected)) if hasattr(ds, "take") else ds

            for item in iterator:
                # Expected fields based on the real ``codeparrot/github-code`` dataset.
                # The test mock provides ``path`` and ``content`` keys.
                file_path = item.get("path") or item.get("file_path") or ""
                code = item.get("content") or item.get("code") or ""
                collected.append({"file_path": str(file_path), "code": str(code)})

                if len(collected) >= sample_size:
                    break

            # If we exit the loop without exception, the download succeeded.
            break

        except ConnectionError as exc:
            # Transient network problem – log and retry.
            logger.warning(
                "Transient ConnectionError while streaming dataset (attempt %d): %s",
                attempts,
                exc,
            )
            if attempts >= max_retries:
                logger.error(
                    "Maximum retry attempts (%d) reached; proceeding with %d rows collected.",
                    max_retries,
                    len(collected),
                )
            # Continue to the next iteration which will re‑invoke ``load_dataset``.

    # Write whatever rows we managed to collect (could be fewer than sample_size).
    _write_csv(collected, out_path)

    logger.info("Wrote %d rows to %s", len(collected), out_path)
    return out_path