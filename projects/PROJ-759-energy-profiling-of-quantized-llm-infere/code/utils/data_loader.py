"""
Data loader utilities for the energy profiling project.

This module provides a function to download the WikiText‑2 dataset
from the HuggingFace Hub, store it as a Parquet file under
``data/raw/wikitext2.parquet`` and record its SHA‑256 checksum in
``data/raw/README.md``. The implementation uses the ``datasets`` library
(which pulls in ``pyarrow`` for Parquet support) and writes the full
dataset (not a synthetic placeholder) so that contract tests checking
file existence and checksum pass on real data.
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Optional

from llmxive_toolkit import get_logger, paths

# The datasets library is a runtime dependency declared in ``requirements.txt``.
from datasets import load_dataset

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
    Download the WikiText‑2 dataset and store it as a Parquet file.

    Parameters
    ----------
    parquet_path: Optional[Path]
        Destination path for the Parquet file. If ``None`` the default
        location ``data/raw/wikitext2.parquet`` (relative to the project
        root) is used.

    Returns
    -------
    Path
        The path to the written Parquet file.

    Raises
    ------
    RuntimeError
        If the file cannot be written.
    """
    # Resolve destination path
    if parquet_path is None:
        parquet_path = paths.data("raw", "wikitext2.parquet")
    else:
        parquet_path = Path(parquet_path)

    # Ensure parent directory exists (paths.data already creates it)
    parquet_path.parent.mkdir(parents=True, exist_ok=True)

    log.info("Downloading WikiText‑2 dataset via ``datasets`` library...")
    # Load the raw WikiText‑2 (train split). The dataset is small enough
    # to fit in memory, but we still use the library's streaming API for
    # robustness.
    dataset = load_dataset(
        "wikitext", "wikitext-2-raw-v1", split="train", streaming=False
    )

    # Convert to a pandas DataFrame and write to Parquet.
    # ``datasets`` objects expose ``to_pandas`` which uses pyarrow under
    # the hood.
    df = dataset.to_pandas()
    try:
        df.to_parquet(parquet_path, engine="pyarrow")
    except Exception as exc:
        log.error("Failed to write Parquet file: %s", exc)
        raise RuntimeError("Unable to write WikiText‑2 Parquet file") from exc

    log.info("WikiText‑2 dataset written to %s", parquet_path)

    # Compute checksum and write README
    checksum = _compute_sha256(parquet_path)
    readme_path = parquet_path.parent / "README.md"
    _write_readme(checksum, readme_path)

    return parquet_path


if __name__ == "__main__":
    # Allow the module to be executed directly for convenience:
    # ``python -m utils.data_loader``
    download_wikitext2()
