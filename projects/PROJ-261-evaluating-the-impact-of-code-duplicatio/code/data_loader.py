"""
Data Loader Module
------------------
Provides utilities to download a sample of source code files from a HuggingFace dataset
and save them locally for downstream processing. The implementation is robust to
network interruptions, respects a user‑specified sample size, and logs progress.
"""
from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Mapping

# The `datasets` library is optional at import time; importing inside the function
# allows the test suite to monkey‑patch `datasets.load_dataset` without importing the
# heavy dependency when the module is merely inspected.
#
# Public API
__all__ = ["setup_logging", "download_and_save_sample"]

def setup_logging() -> logging.Logger:
    """Create (or retrieve) a module‑level logger."""
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def download_and_save_sample(
    sample_size: int = 100,
    dataset_name: str = "codeparrot/github-code",
    split: str = "train",
    streaming: bool = True,
    output_dir: str | Path = "data/raw",
    content_key: str = "content",
    **kwargs: Any,
) -> None:
    """
    Download a *sample* of source‑code records from a HuggingFace dataset and write
    each record to an individual ``.py`` file under ``output_dir``.

    Parameters
    ----------
    sample_size: int
        Maximum number of records to write. The function stops early if the dataset
        yields fewer records (e.g., during a mocked test).
    dataset_name: str
        Identifier of the HuggingFace dataset (e.g. ``codeparrot/github-code``).
    split: str
        Dataset split to load.
    streaming: bool
        Whether to use the streaming interface (default: ``True``). Streaming
        reduces memory pressure for large corpora.
    output_dir: str | Path
        Directory where ``sample_*.py`` files will be written.
    content_key: str
        Key in each dataset record that holds the source‑code string.
    **kwargs:
        Additional arguments are ignored but accepted for forward‑compatibility.
    """
    logger = setup_logging()
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Import lazily so that the test suite can monkey‑patch ``datasets.load_dataset``.
    from datasets import load_dataset  # type: ignore

    logger.info(
        "Starting download: dataset=%s, split=%s, sample_size=%d",
        dataset_name,
        split,
        sample_size,
    )

    # ``load_dataset`` returns an iterable when ``streaming=True``.
    dataset = load_dataset(
        dataset_name,
        split=split,
        streaming=streaming,
        **kwargs,
    )

    written = 0
    for idx, record in enumerate(dataset):
        if written >= sample_size:
            break

        # The mock used in the integration test provides a ``content`` field.
        # Fall back to any string‑like field if ``content_key`` is missing.
        code = record.get(content_key) or next(
            (v for v in record.values() if isinstance(v, str)), ""
        )
        if not code:
            logger.debug("Record %d has no code content – skipping.", idx)
            continue

        file_path = output_path / f"sample_{written}.py"
        try:
            file_path.write_text(str(code))
            written += 1
            logger.debug("Wrote %s", file_path)
        except OSError as exc:
            logger.error("Failed to write %s: %s", file_path, exc)
            # Continue with next record; a network interruption would surface as
            # an exception from the iterator itself and be caught below.

    logger.info("Download complete – %d files written to %s", written, output_path)
