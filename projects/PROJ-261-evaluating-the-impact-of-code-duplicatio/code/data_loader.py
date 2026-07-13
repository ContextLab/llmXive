"""
Data loader utilities for the project.

Provides a robust `download_and_save_sample` function that streams a small
sample from a publicly available HuggingFace dataset, writes it to a CSV
file, and handles common network‑related issues such as rate limiting or
temporary connectivity loss.

The function is deliberately flexible in its signature – it accepts the
sample size as a positional argument, a keyword argument, or falls back to
a default value.  This satisfies the various call‑sites across the code
base (see the task description).
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

def _resolve_parameters(*args: Any, **kwargs: Any) -> tuple[int, Path]:
    """
    Resolve ``sample_size`` and ``output_path`` from a flexible call signature.

    Supported call patterns:
    - ``download_and_save_sample()``                     -> defaults
    - ``download_and_save_sample(200)``                 -> positional sample size
    - ``download_and_save_sample(sample_size=200)``     -> keyword sample size
    - ``download_and_save_sample(output_path=Path(...))``
    - ``download_and_save_sample(200, Path(...))``      -> positional both
    """
    # Default values
    sample_size: int = 100
    output_path: Path = Path("data/raw/github-code-sample.csv")

    # Positional arguments handling
    if args:
        if len(args) >= 1:
            sample_size = int(args[0])
        if len(args) >= 2:
            output_path = Path(args[1])

    # Keyword arguments handling (override positional if present)
    if "sample_size" in kwargs:
        sample_size = int(kwargs["sample_size"])
    if "output_path" in kwargs:
        output_path = Path(kwargs["output_path"])

    return sample_size, output_path

def download_and_save_sample(*args: Any, **kwargs: Any) -> None:
    """
    Download a small sample of code snippets from a public HuggingFace dataset
    and store them as a CSV file with columns ``file_path`` and ``code``.

    The function is tolerant to network hiccups:
    - Retries up to three times with exponential back‑off.
    - Logs each retry attempt.
    - Propagates the exception if all retries fail.

    Parameters can be supplied either positionally or as keywords; see
    ``_resolve_parameters`` for the exact resolution rules.
    """
    sample_size, output_path = _resolve_parameters(*args, **kwargs)

    logger.info(
        "Downloading %d rows from the HuggingFace dataset into %s",
        sample_size,
        output_path,
    )

    # Ensure the target directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    max_retries = 3
    attempt = 0
    while attempt < max_retries:
        try:
            # ``codeparrot/codeparrot-clean`` is a public dataset that contains a
            # ``content`` column with raw source code.  Streaming avoids downloading
            # the full dataset and respects the 500 MB size constraint.
            dataset = load_dataset(
                "codeparrot/codeparrot-clean", split="train", streaming=True
            )
            with output_path.open("w", newline="", encoding="utf-8") as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=["file_path", "code"])
                writer.writeheader()
                for i, record in enumerate(dataset):
                    if i >= sample_size:
                        break
                    # The dataset provides the source code under the key ``content``.
                    code_snippet: str = record.get("content", "")
                    # Construct a deterministic pseudo file name.
                    file_name = f"sample_{i}.py"
                    writer.writerow({"file_path": file_name, "code": code_snippet})
            logger.info(
                "Successfully wrote %d rows to %s", sample_size, output_path
            )
            # Exit the retry loop on success.
            break
        except Exception as exc:  # pragma: no cover – exercised via retries in CI
            attempt += 1
            logger.warning(
                "Attempt %d/%d failed while downloading dataset: %s",
                attempt,
                max_retries,
                exc,
            )
            if attempt >= max_retries:
                logger.error("All retry attempts exhausted; raising exception.")
                raise
            # Exponential back‑off before the next retry.
            backoff_seconds = 2 ** attempt
            time.sleep(backoff_seconds)