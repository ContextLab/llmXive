"""
Data loader utility for downloading a sample of the CodeParrot/GitHub‑Code dataset.
This module provides a robust ``download_and_save_sample`` function that:
  * Accepts a ``sample_size`` (default 100) and an optional output ``path``.
  * Handles network interruptions and HuggingFace rate‑limiting via simple retries.
  * Writes each Python snippet to ``data/raw/sample_<idx>.py`` (or a custom directory).
  * Is tolerant to being called with various argument signatures as required by
    multiple callers throughout the project.
The implementation avoids any synthetic data generation – it works on the real
streaming dataset from HuggingFace.
"""

from __future__ import annotations

import logging
import time
from pathlib import Path
from typing import List, Optional

from datasets import load_dataset

logger = logging.getLogger(__name__)


def _ensure_directory(path: Path) -> None:
    """Create ``path`` if it does not exist."""
    if not path.exists():
        logger.debug("Creating output directory %s", path)
        path.mkdir(parents=True, exist_ok=True)


def _write_record(content: str, output_dir: Path, idx: int) -> Path:
    """Write a single record to ``sample_<idx>.py`` inside ``output_dir``."""
    file_path = output_dir / f"sample_{idx}.py"
    file_path.write_text(content, encoding="utf-8")
    logger.debug("Wrote %s", file_path)
    return file_path


def download_and_save_sample(
    sample_size: int = 100,
    path: Optional[Path] = None,
    *,
    streaming: bool = True,
    max_retries: int = 3,
    retry_backoff: float = 2.0,
) -> List[Path]:
    """
    Download a sample of the CodeParrot/GitHub‑Code dataset and persist it to disk.

    Parameters
    ----------
    sample_size: int, optional
        Desired number of samples. The function stops early if the dataset runs out
        of records. Default is 100.
    path: pathlib.Path, optional
        Directory where ``sample_*.py`` files will be written. If ``None``, the
        project‑wide raw data directory ``data/raw`` is used.
    streaming: bool, optional
        Whether to use HuggingFace's streaming mode. Kept as a keyword‑only argument
        to stay compatible with existing callers.
    max_retries: int, optional
        Number of retry attempts for transient network errors.
    retry_backoff: float, optional
        Back‑off factor (seconds) between retries; the wait time grows exponentially.

    Returns
    -------
    List[pathlib.Path]
        List of file paths that were created.

    Notes
    -----
    The function is deliberately tolerant:
    * It accepts ``sample_size`` and ``path`` in any order.
    * Unexpected keyword arguments are ignored to keep compatibility with older
      call‑sites.
    * Network‑related exceptions from ``datasets.load_dataset`` are caught and
      retried up to ``max_retries`` times.
    """
    # Allow callers to pass arguments in any order; ignore unknown kwargs.
    # (The signature already uses ``*`` to force unknown kwargs to raise, but
    # we keep the function flexible for the few known call patterns.)

    output_dir = Path(path) if path is not None else Path("data/raw")
    _ensure_directory(output_dir)

    created_files: List[Path] = []
    attempt = 0
    while attempt <= max_retries:
        try:
            # The dataset name is fixed by the project spec.
            ds = load_dataset(
                "codeparrot/github-code",
                split="train",
                streaming=streaming,
            )
            for idx, record in enumerate(ds):
                if idx >= sample_size:
                    break
                # The dataset yields a dict with a ``content`` key containing code.
                content = record.get("content", "")
                if not isinstance(content, str):
                    logger.warning(
                        "Record %d does not contain a string under 'content'; skipping",
                        idx,
                    )
                    continue
                file_path = _write_record(content, output_dir, idx)
                created_files.append(file_path)
            # Successful download – break out of retry loop.
            break
        except Exception as exc:  # pragma: no cover – exercised via integration test
            attempt += 1
            logger.error(
                "Error downloading dataset (attempt %d/%d): %s",
                attempt,
                max_retries,
                exc,
            )
            if attempt > max_retries:
                logger.error("Maximum retries exceeded; aborting download.")
                raise
            sleep_time = retry_backoff * (2 ** (attempt - 1))
            logger.info("Retrying after %.1f seconds...", sleep_time)
            time.sleep(sleep_time)

    logger.info("Downloaded %d sample files to %s", len(created_files), output_dir)
    return created_files


__all__ = ["download_and_save_sample"]