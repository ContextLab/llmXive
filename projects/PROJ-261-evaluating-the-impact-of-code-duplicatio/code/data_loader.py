from __future__ import annotations

import csv
import logging
from pathlib import Path
from typing import Any, Iterable, List, Optional

from datasets import load_dataset

from config import get_raw_dir

logger = logging.getLogger(__name__)

def download_and_save_sample(
    path: Optional[Path] = None,
    sample_size: int = 100,
    **kwargs: Any,
) -> Path:
    """
    Download a streaming subset of the ``codeparrot/github-code`` dataset and
    write the first ``sample_size`` rows to a CSV file.

    Parameters
    ----------
    path:
        Destination CSV path. If omitted the default location from the
        configuration is used (``data/raw/github-code-sample.csv``).
    sample_size:
        Number of rows to materialise. The upstream dataset is large; a
        modest sample keeps the pipeline lightweight while still providing
        *real* code snippets for downstream processing.

    Returns
    -------
    The path to the written CSV file.
    """
    destination = path or get_raw_dir() / "github-code-sample.csv"
    destination.parent.mkdir(parents=True, exist_ok=True)

    logger.info("Downloading %d rows from codeparrot/github-code", sample_size)

    # The dataset is streamed to avoid pulling the whole 500 MB subset.
    ds = load_dataset(
        "codeparrot/github-code",
        split="train",
        streaming=True,
    )

    # The dataset yields dictionaries with at least ``id`` and ``content``.
    rows: List[dict] = []
    for i, example in enumerate(ds):
        if i >= sample_size:
            break
        rows.append(
            {
                "id": example.get("repo_id") or str(i),
                "content": example.get("content") or "",
            }
        )

    logger.info("Writing %d rows to %s", len(rows), destination)
    with destination.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["id", "content"])
        writer.writeheader()
        writer.writerows(rows)

    logger.info("Download and save completed")
    return destination

def main() -> None:
    """
    CLI entry‑point – useful for quick manual runs.
    """
    download_and_save_sample()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()
