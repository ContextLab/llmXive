"""Data Loader for the Code Duplication Project.

This module streams a subset of the ``codeparrot/github-code`` dataset
using the HuggingFace ``datasets`` library in streaming mode and writes
the sampled records to ``data/raw/github-code-sample.csv``.  The function
respects the ``streaming`` configuration flag from ``config.get_dataset_name``
and stops once roughly 500 MiB of raw text have been written (or when a
hard‑coded maximum number of samples is reached).

The CSV has three columns:
  - ``sample_id``: integer identifier from the dataset (or generated)
  - ``repo_name``: name of the source repository (if available)
  - ``content``: the raw source‑code string
"""
import csv
import logging
import os
from pathlib import Path
from typing import Iterable, List, Optional

from datasets import load_dataset

from config import (
    get_dataset_name,
    get_streaming_enabled,
    get_all_config,
)
from parse_failure_logger import log_parse_failure

logger = logging.getLogger(__name__)

RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "data" / "raw"
RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

OUTPUT_CSV = RAW_DATA_DIR / "github-code-sample.csv"

# Approx. 500 MiB in bytes
TARGET_BYTES = 500 * 1024 * 1024
# Upper bound to avoid infinite loops on very small records
MAX_SAMPLES = 200_000


def setup_logging() -> None:
    """Configure module‑level logging."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s – %(message)s",
    )
    logger.info("Logging for data_loader initialized.")


def stream_dataset() -> Iterable[dict]:
    """Yield records from the ``codeparrot/github-code`` dataset.

    Returns
    -------
    Iterable[dict]
        Each dict contains at least the ``content`` field.  Other fields
        (e.g. ``repo_name``) are passed through if present.
    """
    dataset_name = get_dataset_name()
    streaming = get_streaming_enabled()
    logger.info(
        "Loading dataset %s with streaming=%s", dataset_name, streaming
    )
    try:
        # ``load_dataset`` with ``streaming=True`` returns an iterator‑like
        # dataset that yields examples one‑by‑one.
        ds = load_dataset(dataset_name, split="train", streaming=streaming)
    except Exception as exc:
        logger.error("Failed to load dataset %s: %s", dataset_name, exc)
        raise

    for record in ds:
        yield record


def download_and_save_sample(
    target_path: Path = OUTPUT_CSV,
    max_bytes: int = TARGET_BYTES,
    max_samples: int = MAX_SAMPLES,
) -> Path:
    """Stream the dataset and write a size‑bounded CSV sample.

    Parameters
    ----------
    target_path : Path
        Destination CSV file.
    max_bytes : int
        Stop once the cumulative size of the ``content`` field reaches this
        many bytes.
    max_samples : int
        Upper bound on the number of rows to write (safety guard).

    Returns
    -------
    Path
        The path that was written.
    """
    logger.info("Beginning streaming download to %s", target_path)
    total_bytes = 0
    written = 0

    with target_path.open("w", newline="", encoding="utf-8") as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["sample_id", "repo_name", "content"])

        for idx, record in enumerate(stream_dataset()):
            if written >= max_samples:
                logger.info(
                    "Reached maximum sample count (%d); stopping.", max_samples
                )
                break

            content = record.get("content")
            if not isinstance(content, str):
                # Record is malformed – log and skip.
                log_parse_failure(
                    f"Missing or non‑string 'content' in record {idx}"
                )
                continue

            repo_name = record.get("repo_name", "")
            writer.writerow([idx, repo_name, content])
            total_bytes += len(content.encode("utf-8"))
            written += 1

            if total_bytes >= max_bytes:
                logger.info(
                    "Reached target size of ~%d bytes after %d rows.",
                    max_bytes,
                    written,
                )
                break

    logger.info(
        "Finished streaming download: %d rows, %d bytes written.",
        written,
        total_bytes,
    )
    return target_path


def load_raw_data(csv_path: Path = OUTPUT_CSV) -> List[dict]:
    """Read the CSV produced by :func:`download_and_save_sample`.

    Returns a list of dictionaries with the same keys as the CSV header.
    """
    logger.info("Loading raw data from %s", csv_path)
    data = []
    with csv_path.open("r", newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            data.append(row)
    logger.info("Loaded %d records from raw CSV.", len(data))
    return data


def main() -> None:
    """Entry‑point used by the quick‑start run‑book."""
    setup_logging()
    # Ensure the raw directory exists before writing.
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)
    download_and_save_sample()
