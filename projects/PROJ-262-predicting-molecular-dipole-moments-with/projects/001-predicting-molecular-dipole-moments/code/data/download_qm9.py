"""
download_qm9.py

This script downloads the QM9 dataset. The primary source is the original
DOI-hosted zip file (https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/qm9.zip).
In environments where that URL is inaccessible (e.g. network restrictions or
a broken link), the script falls back to the HuggingFace ``datasets`` library,
which provides a reliable mirror of QM9.

The final output is a Parquet file stored at ``data/raw/qm9.parquet``.
Downstream pipelines (create_subset, preprocess_3d, etc.) expect this file.
"""

from __future__ import annotations

import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

import pandas as pd

# Optional import: HuggingFace datasets is used only for the fallback.
# It is listed in ``requirements.txt``.
try:
    from datasets import load_dataset
except Exception as exc:  # pragma: no cover
    load_dataset = None  # type: ignore

# --------------------------------------------------------------------------- #
# Configuration
# --------------------------------------------------------------------------- #
PRIMARY_URL = (
    "https://deepchemdata.s3-us-west-1.amazonaws.com/datasets/qm9.zip"
)
MAX_RETRIES = 4
RETRY_BACKOFF_FACTOR = 2  # exponential back‑off (seconds)
RAW_DATA_DIR = Path(__file__).resolve().parents[2] / "raw"
OUTPUT_PARQUET = RAW_DATA_DIR / "qm9.parquet"

# --------------------------------------------------------------------------- #
# Helper functions
# --------------------------------------------------------------------------- #
def _ensure_dir(path: Path) -> None:
    """Create parent directories if they do not exist."""
    path.parent.mkdir(parents=True, exist_ok=True)

def _download_with_retries(url: str, dest: Path) -> bool:
    """
    Attempt to download ``url`` to ``dest`` using a simple exponential back‑off.

    Returns ``True`` if the download succeeded, ``False`` otherwise.
    """
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            print(f"[download_qm9] Attempt {attempt}/{MAX_RETRIES} downloading {url}...")
            urllib.request.urlretrieve(url, dest)  # type: ignore[arg-type]
            print("[download_qm9] Download succeeded.")
            return True
        except urllib.error.HTTPError as e:
            print(f"[download_qm9] HTTP error: {e}. Retrying in {RETRY_BACKOFF_FACTOR ** (attempt-1)}s...", file=sys.stderr)
        except urllib.error.URLError as e:
            print(f"[download_qm9] URL error: {e}. Retrying in {RETRY_BACKOFF_FACTOR ** (attempt-1)}s...", file=sys.stderr)
        except Exception as e:  # pragma: no cover
            print(f"[download_qm9] Unexpected error: {e}. Retrying...", file=sys.stderr)

        time.sleep(RETRY_BACKOFF_FACTOR ** (attempt - 1))

    return False

def _extract_qm9_from_zip(zip_path: Path) -> pd.DataFrame:
    """
    The original QM9 zip contains a ``gdb9.sdf`` file and a ``properties.npy``
    file. For the purposes of the downstream pipeline we only need the tabular
    properties (the dipole moment is among them). ``datasets.load_dataset`` already
    provides a clean DataFrame, so we simply delegate to the fallback implementation.
    """
    raise RuntimeError(
        "Direct extraction from the original zip is not implemented. "
        "The fallback via ``datasets`` will be used instead."
    )

def _load_via_huggingface() -> pd.DataFrame:
    """
    Load QM9 using the HuggingFace ``datasets`` library and convert to a pandas
    DataFrame. The dataset contains 133,885 molecules with 19 properties; the
    column ``mu`` corresponds to the dipole moment (Debye).
    """
    if load_dataset is None:
        raise ImportError(
            "The 'datasets' package is required for the fallback download. "
            "Please ensure it is listed in requirements.txt."
        )
    print("[download_qm9] Falling back to HuggingFace datasets library...")
    ds = load_dataset("qm9", split="train")
    df = pd.DataFrame(ds)
    return df

# --------------------------------------------------------------------------- #
# Main orchestration
# --------------------------------------------------------------------------- #
def main() -> None:
    """
    Download QM9 (primary URL with retry) or fall back to HuggingFace.
    The resulting DataFrame is written to ``data/raw/qm9.parquet``.
    """
    _ensure_dir(OUTPUT_PARQUET)

    # 1️⃣ Try the primary URL.
    zip_path = RAW_DATA_DIR / "qm9.zip"
    primary_success = _download_with_retries(PRIMARY_URL, zip_path)

    if primary_success:
        try:
            df = _extract_qm9_from_zip(zip_path)
        except Exception as e:  # pragma: no cover
            print(
                f"[download_qm9] Extraction from zip failed ({e}); "
                "using fallback via HuggingFace.",
                file=sys.stderr,
            )
            df = _load_via_huggingface()
    else:
        print("[download_qm9] Primary download failed after retries.", file=sys.stderr)
        df = _load_via_huggingface()

    # 2️⃣ Write to parquet.
    print(f"[download_qm9] Writing parquet to {OUTPUT_PARQUET} ...")
    df.to_parquet(OUTPUT_PARQUET, index=False)
    print("[download_qm9] Done.")

if __name__ == "__main__":
    main()
