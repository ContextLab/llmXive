from __future__ import annotations
import csv
import logging
import time
from pathlib import Path
from typing import Any, Optional

from datasets import load_dataset

logger = logging.getLogger(__name__)

def download_and_save_sample(
    sample_size: int = 100,
    output_path: Optional[Path] = None,
    *args,
    **kwargs,
) -> None:
    """
    Download a sample from the ``codeparrot/github-code`` dataset using streaming
    mode and write it to ``data/raw/github-code-sample.csv`` (or a custom path).

    The function is tolerant to a variety of call signatures:
    * ``download_and_save_sample()`` – uses defaults.
    * ``download_and_save_sample(sample_size=…)`` – keyword argument.
    * ``download_and_save_sample(…)`` – positional argument (interpreted as
      ``sample_size``).
    * ``download_and_save_sample(sample_size=…, output_path=…)`` – both explicit.

    It implements a simple exponential‑backoff retry strategy to cope with
    transient network errors or HTTP 429 rate‑limit responses.
    """
    # Resolve positional arguments
    if args:
        # If the first positional argument is an int, treat it as sample_size
        if isinstance(args[0], int):
            sample_size = args[0]

    # Resolve keyword arguments that may override defaults
    if "sample_size" in kwargs:
        sample_size = kwargs["sample_size"]
    if "output_path" in kwargs:
        output_path = Path(kwargs["output_path"])

    # Default output location
    if output_path is None:
        output_path = Path("data/raw/github-code-sample.csv")

    # Ensure the output directory exists
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Load the dataset with streaming; retry on failures
    max_retries = 5
    backoff = 1  # seconds
    for attempt in range(max_retries):
        try:
            ds = load_dataset(
                "codeparrot/github-code",
                split="train",
                streaming=True,
            )
            break
        except Exception as exc:  # pragma: no cover – exercised via integration test
            logger.warning(
                f"Attempt {attempt + 1}/{max_retries} to load dataset failed: {exc}"
            )
            if attempt == max_retries - 1:
                raise
            time.sleep(backoff)
            backoff *= 2

    # Write the requested number of rows to CSV
    written = 0
    fieldnames = ["file_path", "code"]
    with output_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for record in ds:
            # The dataset provides a ``content`` field with the source code.
            # Some versions expose it as ``code``; we handle both.
            file_path = record.get("file_path") or record.get("path") or f"file_{written}.py"
            code = record.get("content") or record.get("code") or ""
            writer.writerow({"file_path": file_path, "code": code})
            written += 1
            if written >= sample_size:
                break

    logger.info(f"Wrote {written} rows to {output_path}")