"""
Data loader utilities for the energy profiling project.

This module provides a function to download the WikiText‑2 dataset from the
HuggingFace Hub, store it as a Parquet file under ``data/raw/wikitext2.parquet``,
and record its SHA‑256 checksum in ``data/raw/README.md``.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

__all__ = ["download_wikitext2"]


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    h = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


def _write_readme(checksum: str, readme_path: Path) -> None:
    """Write a small README containing the checksum."""
    content = f"""# WikiText‑2 dataset

This file contains the SHA‑256 checksum of the Parquet file
``wikitext2.parquet`` stored in this directory.

**SHA‑256:** `{checksum}`

The checksum can be used to verify data integrity after download.
"""
    readme_path.write_text(content, encoding="utf-8")
    log.info("Wrote checksum README to %s", readme_path)


def download_wikitext2(parquet_path: Optional[Path] = None) -> Path:
    """
    Download the WikiText‑2 dataset, store it as Parquet, and record its checksum.

    Parameters
    ----------
    parquet_path: Optional[Path]
        Destination path for the Parquet file. If ``None`` the default location
        ``data/raw/wikitext2.parquet`` (relative to the project root) is used.

    Returns
    -------
    Path
        The path to the written Parquet file.

    Raises
    ------
    RuntimeError
        If the dataset cannot be downloaded or written.
    """
    # Resolve destination path
    if parquet_path is None:
        parquet_path = paths.data("raw", "wikitext2.parquet")
    else:
        parquet_path = Path(parquet_path)

    # Ensure parent directory exists (paths.data already creates it)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Downloading WikiText‑2 dataset...")
    try:
        # Load the raw WikiText‑2 dataset (test split is sufficient for benchmarking)
        ds = load_dataset("wikitext", "wikitext-2-raw-v1", split="test")
    except Exception as exc:
        log.error("Failed to download WikiText‑2 dataset: %s", exc)
        raise RuntimeError("Unable to download WikiText‑2 dataset") from exc

    # Convert to pandas DataFrame and write as Parquet
    try:
        df = pd.DataFrame(ds)
        df.to_parquet(parquet_path, index=False)
    except Exception as exc:
        log.error("Failed to write Parquet file: %s", exc)
        raise RuntimeError("Unable to write WikiText‑2 Parquet file") from exc

    log.info("WikiText‑2 dataset written to %s", parquet_path)

    # Compute checksum and write README
    checksum = _compute_sha256(parquet_path)
    readme_path = parquet_path.parent / "README.md"
    _write_readme(checksum, readme_path)

    return parquet_path