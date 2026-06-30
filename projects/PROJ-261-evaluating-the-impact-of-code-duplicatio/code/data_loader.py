"""
Data Loader for the GitHub Code dataset.

This module provides utilities to stream a subset of the
``codeparrot/github-code`` dataset from HuggingFace and save it as a CSV
file under ``data/raw/``. The primary entry point is :func:`download_and_save_sample`,
which can be invoked both directly (e.g., ``python -m code.data_loader``) and
indirectly through the pipeline orchestrated in ``code/main.py``.
"""

from __future__ import annotations

import csv
import logging
import os
import sys
import time
from pathlib import Path
from typing import Any

from datasets import load_dataset  # type: ignore

logger = logging.getLogger(__name__)

# --------------------------------------------------------------------------- #
# Configuration constants
# --------------------------------------------------------------------------- #
DEFAULT_OUTPUT_PATH = Path("data/raw/github-code-sample.csv")
DEFAULT_NUM_SAMPLES = 10_000  # reasonable default for CI; can be increased.


def _stream_dataset(num_samples: int = DEFAULT_NUM_SAMPLES) -> Any:
    """
    Stream the ``codeparrot/github-code`` dataset.

    Parameters
    ----------
    num_samples : int
        Maximum number of rows to stream and write.

    Returns
    -------
    generator
        Yields dictionaries representing rows of the dataset.
    """
    logger.info("Loading dataset ``codeparrot/github-code`` in streaming mode.")
    try:
        ds = load_dataset(
            "codeparrot/github-code",
            split="train",
            streaming=True,
        )
    except Exception as exc:
        logger.exception("Failed to load dataset: %s", exc)
        raise

    for i, row in enumerate(ds):
        if i >= num_samples:
            break
        yield row

# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #
def download_and_save_sample(*args: Any, **kwargs: Any) -> str:
    """
    Download a sample of the GitHub code dataset and save it to CSV.

    The function is deliberately permissive in its signature (accepting
    ``*args`` and ``**kwargs``) so that it can be called from multiple
    locations without raising ``TypeError``. Any positional or keyword
    arguments are ignored.

    Returns
    -------
    str
        Absolute path to the generated CSV file.
    """
    # Resolve optional overrides from kwargs; fall back to defaults.
    output_path: Path = Path(kwargs.get("output_path", DEFAULT_OUTPUT_PATH))
    num_samples: int = int(kwargs.get("num_samples", DEFAULT_NUM_SAMPLES))

    # Ensure the parent directory exists.
    output_path.parent.mkdir(parents=True, exist_ok=True)

    logger.info(
        "Saving a sample of %d rows to %s",
        num_samples,
        output_path,
    )
    start = time.time()
    try:
        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.writer(csvfile)
            # Write a generic header – the dataset contains many fields; we
            # only persist a subset useful for downstream stages.
            writer.writerow(["repo_name", "file_path", "content"])
            for row in _stream_dataset(num_samples):
                repo = row.get("repo_name", "")
                path = row.get("path", "")
                content = row.get("content", "")
                writer.writerow([repo, path, content])
    except Exception as exc:
        logger.exception("Failed while writing CSV: %s", exc)
        raise
    elapsed = time.time() - start
    logger.info("Dataset sample saved in %.2f seconds.", elapsed)

    return str(output_path.resolve())

def main() -> int:  # pragma: no cover
    """
    Simple CLI entry point so the module can be executed with:
    ``python -m code.data_loader``.
    """
    logging.basicConfig(level=logging.INFO)
    try:
        download_and_save_sample()
        return 0
    except Exception as exc:  # pragma: no cover
        logger.exception("Data download failed: %s", exc)
        return 1

if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
