"""
src/data/download.py
---------------------

Downloads the perovskite defect formation energy dataset from the
verified Zenodo URL (see the task description). The file is written
to ``data/raw/materials_defects.csv`` and a SHA‑256 checksum file is
created in ``data/checksums/raw_defects.sha256``.
"""

import hashlib
import sys
from pathlib import Path

import pandas as pd
import requests
from llmxive_toolkit import get_logger, paths

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants
# ----------------------------------------------------------------------
ZENODO_URL = (
    "https://zenodo.org/records/10028980/files/Data.csv?download=1"
)
RAW_CSV_PATH = paths.data("raw", "materials_defects.csv")
CHECKSUM_PATH = paths.data("checksums", "raw_defects.sha256")


def _download_csv(url: str) -> pd.DataFrame:
    """Download the CSV from *url* and return it as a DataFrame.

    The function raises any network‑related exception – we never
    silently fall back to synthetic data.
    """
    log.info(f"Downloading raw dataset from {url}")
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    # ``pandas.read_csv`` can read from a file‑like object.
    from io import StringIO

    return pd.read_csv(StringIO(response.text))


def _write_checksum(file_path: Path, checksum_path: Path) -> None:
    """Write the SHA‑256 checksum of *file_path* to *checksum_path*."""
    checksum_path.parent.mkdir(parents=True, exist_ok=True)
    sha256 = hashlib.sha256()
    with file_path.open("rb") as f:
        for block in iter(lambda: f.read(8192), b""):
            sha256.update(block)
    checksum_path.write_text(sha256.hexdigest())
    log.info(f"Checksum written to {checksum_path}")


def main() -> None:
    """
    Entry point for ``python -m src.data.download``.
    Downloads the dataset, writes it to ``data/raw/materials_defects.csv``,
    and creates the checksum file.
    """
    try:
        df = _download_csv(ZENODO_URL)
    except Exception as exc:
        log.error(f"Failed to download dataset: {exc}")
        raise

    # Ensure the target directory exists.
    RAW_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(RAW_CSV_PATH, index=False)
    log.info(f"Raw dataset written to {RAW_CSV_PATH}")

    # Compute and write checksum.
    _write_checksum(RAW_CSV_PATH, CHECKSUM_PATH)


if __name__ == "__main__":
    # When executed as a script we exit with a non‑zero code on failure.
    try:
        main()
    except Exception as exc:
        log.error(str(exc))
        sys.exit(1)
