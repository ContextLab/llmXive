"""
src.ingest.load_illusions
=========================

This module provides a command‑line interface for downloading and cleaning the
Müller‑Lyer illusion dataset from OpenNeuro.  It is invoked by the CI with::

    python -m src.ingest.load_illusions download_muller

The command performs two steps:

1. **Download** the raw parquet file from the verified OpenNeuro repository and
   store it under ``data/raw/muller_lyer.parquet``.
2. **Clean** the parquet into a tidy CSV (``data/clean/clean_muller_lyer.csv``)
   enforcing the presence of required columns, dropping rows with missing values
   in those columns, and emitting a warning for duplicate ``subject_id`` entries.

The script is deterministic – it seeds NumPy, ``random`` and the Python hash
seed via :func:`src.utils.seed.set_global_seed`.  All paths are created using the
``llmxive_toolkit.paths`` helpers which guarantee the target directories exist.

The implementation uses the ``datasets`` library (``datasets.load_dataset``) to
fetch the OpenNeuro parquet file.  The dataset identifier is hard‑coded to the
verified OpenNeuro collection ``openneuro/muller_lyer``; if the URL or identifier
changes the script will raise an informative ``RuntimeError`` rather than silently
falling back to synthetic data.

The module can also be imported and the ``download_and_clean`` function called
programmatically.

----
"""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from src.utils.seed import set_global_seed

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified OpenNeuro identifier for the Müller‑Lyer dataset.
# This identifier is authoritative – if the dataset is moved or renamed the
# script will raise an error.
OPENNEURO_DATASET_ID = "openneuro/muller_lyer"
# The split name used by the OpenNeuro collection – most collections expose a
# single split called ``train``.
OPENNEURO_SPLIT = "train"

# Required columns in the cleaned CSV.  The schema file
# ``contracts/clean-muller-lyer.schema.yaml`` mirrors this list.
REQUIRED_COLUMNS = [
    "subject_id",
    "stimulus_type",
    "response",
    "trial_id",
    "stimulus_parameters",
]

# ----------------------------------------------------------------------
# Logging
# ----------------------------------------------------------------------
log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_output_paths() -> tuple[Path, Path]:
    """
    Return the paths for the raw parquet file and the cleaned CSV,
    creating parent directories if necessary.
    """
    raw_path = paths.data("raw", "muller_lyer.parquet")
    clean_path = paths.data("clean", "clean_muller_lyer.csv")
    # ``paths`` ensures the directories exist.
    return raw_path, clean_path

def _download_parquet(raw_path: Path) -> None:
    """
    Download the parquet file from OpenNeuro and write it to ``raw_path``.
    The function raises ``RuntimeError`` if the download fails.
    """
    log.info("Downloading Müller‑Lyer dataset from OpenNeuro (%s)", OPENNEURO_DATASET_ID)
    try:
        # ``load_dataset`` returns a DatasetDict; we request the specified split.
        ds = load_dataset(OPENNEURO_DATASET_ID, split=OPENNEURO_SPLIT, streaming=False)
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download dataset '{OPENNEURO_DATASET_ID}'. "
            "Check the identifier and network connectivity."
        ) from exc

    # The dataset is expected to contain a column named ``file`` that holds the
    # parquet bytes, but many OpenNeuro collections expose the data directly.
    # We therefore attempt to write the whole dataset to parquet.
    try:
        df = ds.to_pandas()
    except Exception as exc:
        raise RuntimeError(
            "Unable to convert the downloaded dataset to a pandas DataFrame."
        ) from exc

    log.info("Writing raw parquet to %s", raw_path)
    try:
        df.to_parquet(raw_path, index=False)
    except Exception as exc:
        raise RuntimeError(f"Failed to write parquet file to {raw_path}") from exc

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce column presence, drop rows with missing values in required
    columns, and warn about duplicate ``subject_id`` entries.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Drop rows with NaN in any required column.
    before_rows = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped = before_rows - len(df_clean)
    if dropped > 0:
        log.warning("Dropped %d rows with missing values in required columns.", dropped)

    # Warn about duplicate subject IDs.
    dup_counts = df_clean["subject_id"].value_counts()
    duplicate_subjects = dup_counts[dup_counts > 1]
    if not duplicate_subjects.empty:
        log.warning(
            "Found %d duplicate subject_id entries. Duplicates will be retained "
            "but flagged as a warning (not an error).",
            duplicate_subjects.size,
        )
    return df_clean

def _write_clean_csv(df_clean: pd.DataFrame, clean_path: Path) -> None:
    """
    Write the cleaned DataFrame to CSV.  The CSV uses UTF‑8 encoding and does
    not write the index column.
    """
    log.info("Writing cleaned CSV to %s", clean_path)
    try:
        df_clean.to_csv(clean_path, index=False, encoding="utf-8")
    except Exception as exc:
        raise RuntimeError(f"Failed to write cleaned CSV to {clean_path}") from exc

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def download_and_clean(seed: int = 42) -> None:
    """
    Download the raw parquet file and produce a cleaned CSV.

    Parameters
    ----------
    seed : int, optional
        Random seed for deterministic behaviour (default 42).  The seed is
        applied via :func:`src.utils.seed.set_global_seed`.
    """
    set_global_seed(seed)
    raw_path, clean_path = _ensure_output_paths()

    # Step 1 – download raw parquet (skip if already exists to make the command
    # idempotent).
    if not raw_path.is_file():
        _download_parquet(raw_path)
    else:
        log.info("Raw parquet already exists at %s – skipping download.", raw_path)

    # Step 2 – load parquet, clean, and write CSV.
    try:
        df_raw = pd.read_parquet(raw_path)
    except Exception as exc:
        raise RuntimeError(f"Unable to read parquet file from {raw_path}") from exc

    df_clean = _clean_dataframe(df_raw)
    _write_clean_csv(df_clean, clean_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Download and clean the Müller‑Lyer illusion dataset."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    dl_parser = subparsers.add_parser(
        "download_muller",
        help="Download the raw dataset and produce a cleaned CSV.",
    )
    dl_parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for deterministic processing (default: 42).",
    )

    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if args.command == "download_muller":
        log.info("Running download_muller with seed=%s", args.seed)
        download_and_clean(seed=args.seed)
    else:
        # This branch should never be hit because argparse enforces required
        # sub‑commands.
        raise RuntimeError(f"Unknown command: {args.command}")

if __name__ == "__main__":
    # When executed as a script ``python src/ingest/load_illusions.py download_muller``
    # the ``argv`` passed to ``main`` is ``sys.argv[1:]``.
    main(sys.argv[1:])
