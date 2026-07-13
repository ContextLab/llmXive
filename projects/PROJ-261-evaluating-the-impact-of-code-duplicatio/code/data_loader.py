"""
Data Loader utilities for the project.

This module provides a robust ``download_and_save_sample`` function that
streams a subset of the ``codeparrot/github-code`` dataset from the Hugging
Face Hub, writes the selected rows to a CSV file, and includes retry logic
to handle rate‑limiting (HTTP 429) and transient network interruptions.

The function is deliberately flexible – it accepts positional arguments,
keyword arguments, and defaults so that all existing call‑sites in the
code‑base remain compatible.
"""

from __future__ import annotations

import csv
import logging
import time
from pathlib import Path
from typing import Any, Optional

from datasets import load_dataset
from requests.exceptions import HTTPError, ConnectionError

logger = logging.getLogger(__name__)

DEFAULT_SAMPLE_SIZE = 10
DEFAULT_OUTPUT_PATH = Path("data/raw/github-code-sample.csv")
MAX_RETRIES = 3
BACKOFF_FACTOR = 2  # exponential back‑off multiplier


def _stream_dataset() -> Any:
    """
    Return a streaming iterator over the ``codeparrot/github-code`` dataset.

    The ``load_dataset`` call uses ``streaming=True`` so that only the
    requested number of rows are materialised in memory.
    """
    # ``codeparrot/github-code`` is a public dataset; we request the
    # ``train`` split which contains the source files.
    return load_dataset(
        "codeparrot/github-code",
        split="train",
        streaming=True,
    )


def _write_rows_to_csv(
    rows: list[dict[str, Any]],
    output_path: Path = DEFAULT_OUTPUT_PATH,
) -> None:
    """
    Write a list of dictionaries to ``output_path`` as a CSV file.

    The CSV must contain the columns ``file_path`` and ``code`` as required
    by downstream consumers and the integration test.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open(mode="w", newline="", encoding="utf-8") as csvfile:
        fieldnames = ["file_path", "code"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    "file_path": row.get("path", row.get("file_path", "")),
                    "code": row.get("content", row.get("code", "")),
                }
            )
    logger.info("Wrote %d rows to %s", len(rows), output_path)


def download_and_save_sample(
    *args,
    sample_size: Optional[int] = None,
    output_path: Optional[Path] = None,
    **kwargs,
) -> Path:
    """
    Download a small sample of the GitHub code corpus and save it as CSV.

    Parameters
    ----------
    sample_size : int, optional
        Number of rows to download. If omitted the default
        ``DEFAULT_SAMPLE_SIZE`` is used.
    output_path : pathlib.Path, optional
        Destination CSV file. Defaults to
        ``data/raw/github-code-sample.csv``.
    *args, **kwargs
        Accepted for backward compatibility – they are ignored unless they
        contain ``sample_size`` or ``output_path`` as positional arguments.

    Returns
    -------
    pathlib.Path
        Path to the written CSV file.

    The function retries the download on HTTP 429 (rate‑limit) and generic
    connection errors, using exponential back‑off.
    """
    # Resolve positional arguments for legacy callers.
    # Historical signatures were:
    #   download_and_save_sample()
    #   download_and_save_sample(sample_size)
    #   download_and_save_sample(sample_size, output_path)
    if args:
        # first positional argument may be sample_size
        if sample_size is None:
            sample_size = args[0]
        if len(args) > 1 and output_path is None:
            output_path = Path(args[1])

    # Keyword arguments may also be supplied via **kwargs
    sample_size = sample_size or kwargs.get("sample_size", DEFAULT_SAMPLE_SIZE)
    output_path = (
        Path(output_path)
        if output_path
        else Path(kwargs.get("output_path", DEFAULT_OUTPUT_PATH))
    )

    logger.info(
        "Downloading %d rows from codeparrot/github-code to %s",
        sample_size,
        output_path,
    )

    attempt = 0
    while attempt < MAX_RETRIES:
        try:
            dataset_iter = _stream_dataset()
            rows: list[dict[str, Any]] = []
            for idx, item in enumerate(dataset_iter):
                if idx >= sample_size:
                    break
                rows.append(item)
            if not rows:
                raise RuntimeError("No rows were retrieved from the dataset.")
            _write_rows_to_csv(rows, output_path)
            return output_path
        except (HTTPError, ConnectionError) as exc:
            # Detect rate‑limit (HTTP 429) or generic connectivity issues.
            if isinstance(exc, HTTPError) and exc.response.status_code != 429:
                logger.error("Non‑rate‑limit HTTP error: %s", exc)
                raise
            attempt += 1
            sleep_time = BACKOFF_FACTOR ** attempt
            logger.warning(
                "Download failed (attempt %d/%d). Retrying in %s seconds...",
                attempt,
                MAX_RETRIES,
                sleep_time,
            )
            time.sleep(sleep_time)
    # If we exit the loop, all retries failed.
    raise RuntimeError(
        f"Failed to download sample after {MAX_RETRIES} attempts."
    )