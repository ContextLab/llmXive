"""
src.ingest.load_illusions
=========================

This module provides a command‑line interface for downloading and cleaning the
Müller‑Lyer illusion dataset from OpenNeuro.  It supports two usage styles:

1. The original sub‑command style used by the verification step::

   python -m src.ingest.load_illusions download_muller [--seed N]

2. A flag‑based style used by the quick‑start documentation::

   python -m src.ingest.load_illusions \\
       --download \\
       --output-dir data/raw \\
       --clean \\
       --raw-dir data/raw \\
       --clean-dir data/clean \\
       --seed 42

Both styles ultimately call the same internal functions that
* download the raw parquet file from the verified OpenNeuro collection,
* clean the data according to the required schema, and
* write the outputs to the exact paths expected by the pipeline.

The implementation is deterministic – it seeds NumPy, ``random`` and the
Python hash seed via :func:`src.utils.seed.set_global_seed`.  All paths are
created using the ``llmxive_toolkit.paths`` helpers which guarantee the target
directories exist.

The module can also be imported and the ``download_and_clean`` function called
programmatically.
"""

import argparse
import logging
import sys
from pathlib import Path
import shutil

import pandas as pd
from huggingface_hub import hf_hub_download
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger
from src.utils.seed import set_global_seed

# ----------------------------------------------------------------------
# Configuration
# ----------------------------------------------------------------------
# Verified OpenNeuro identifier for the Müller‑Lyer dataset.
# The dataset is hosted on the Hugging Face Hub under the repo
# ``openneuro/muller-lyer``.  The primary parquet file is named
# ``muller_lyer.parquet``.
OPENNEURO_DATASET_ID = "openneuro/muller-lyer"
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
def _ensure_output_paths(
    raw_dir: Path | None = None, clean_dir: Path | None = None
) -> tuple[Path, Path]:
    """
    Return the paths for the raw parquet file and the cleaned CSV,
    creating parent directories if necessary.

    Parameters
    ----------
    raw_dir : Path | None
        Directory where the raw parquet should be stored.  If ``None``,
        the default ``data/raw`` directory (as created by ``paths.data``)
        is used.
    clean_dir : Path | None
        Directory where the cleaned CSV should be stored.  If ``None``,
        the default ``data/clean`` directory is used.

    Returns
    -------
    tuple[Path, Path]
        (raw_path, clean_path)
    """
    if raw_dir is None:
        raw_path = paths.data("raw", "muller_lyer.parquet")
    else:
        raw_path = raw_dir / "muller_lyer.parquet"

    if clean_dir is None:
        clean_path = paths.data("clean", "clean_muller_lyer.csv")
    else:
        clean_path = clean_dir / "clean_muller_lyer.csv"

    # ``paths`` ensures the parent directories exist.
    raw_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path.parent.mkdir(parents=True, exist_ok=True)

    return raw_path, clean_path

def _download_parquet(raw_path: Path) -> None:
    """
    Download the parquet file from OpenNeuro (via the Hugging Face Hub) and
    write it to ``raw_path``.  The function raises ``RuntimeError`` if the
    download fails.
    """
    log.info(
        "Downloading Müller‑Lyer dataset from OpenNeuro (%s)", OPENNEURO_DATASET_ID
    )
    try:
        # ``hf_hub_download`` fetches the file from the Hub without requiring
        # authentication because the repository is public.
        downloaded_file = hf_hub_download(
            repo_id=OPENNEURO_DATASET_ID,
            filename="muller_lyer.parquet",
        )
    except Exception as exc:
        raise RuntimeError(
            f"Failed to download parquet file from repository "
            f"'{OPENNEURO_DATASET_ID}'. Ensure the repository and file exist."
        ) from exc

    # Copy the downloaded file to the desired location (preserving the exact
    # filename expected by downstream steps).
    try:
        shutil.copyfile(downloaded_file, raw_path)
    except Exception as exc:
        raise RuntimeError(f"Failed to copy parquet to {raw_path}") from exc

    log.info("Raw parquet written to %s", raw_path)

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Enforce column presence, drop rows with missing values in required
    columns, and warn about duplicate ``subject_id`` entries.
    """
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(
            f"Dataset is missing required columns: {missing_cols}"
        )

    # Drop rows with NaN in any required column.
    before_rows = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped = before_rows - len(df_clean)
    if dropped > 0:
        log.warning(
            "Dropped %d rows with missing values in required columns.", dropped
        )

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
        raise RuntimeError(
            f"Failed to write cleaned CSV to {clean_path}"
        ) from exc

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
        log.info(
            "Raw parquet already exists at %s – skipping download.", raw_path
        )

    # Step 2 – load parquet, clean, and write CSV.
    try:
        df_raw = pd.read_parquet(raw_path)
    except Exception as exc:
        raise RuntimeError(
            f"Unable to read parquet file from {raw_path}"
        ) from exc

    df_clean = _clean_dataframe(df_raw)
    _write_clean_csv(df_clean, clean_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """
    Parse command‑line arguments.

    The parser supports two mutually exclusive styles:

    * Sub‑command style (used by the verification step):
      ``download_muller``

    * Flag‑based style (used by quickstart.md):
      ``--download`` / ``--clean`` with optional directory arguments.
    """
    # Detect flag‑based invocation
    if any(
        arg.startswith("--download") or arg.startswith("--clean")
        for arg in (argv or [])
    ):
        parser = argparse.ArgumentParser(
            description="Download and/or clean the Müller‑Lyer illusion dataset."
        )
        parser.add_argument(
            "--download",
            action="store_true",
            help="Download the raw parquet file.",
        )
        parser.add_argument(
            "--clean",
            action="store_true",
            help="Clean the raw parquet into a tidy CSV.",
        )
        parser.add_argument(
            "--output-dir",
            type=str,
            default="data/raw",
            help="Directory to store the raw parquet file (used with --download).",
        )
        parser.add_argument(
            "--raw-dir",
            type=str,
            default="data/raw",
            help="Directory containing the raw parquet file (used with --clean).",
        )
        parser.add_argument(
            "--clean-dir",
            type=str,
            default="data/clean",
            help="Directory to store the cleaned CSV (used with --clean).",
        )
        parser.add_argument(
            "--seed",
            type=int,
            default=42,
            help="Random seed for deterministic processing (default: 42).",
        )
        return parser.parse_args(argv)

    # Fallback to sub‑command style
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

    # Flag‑based interface
    if getattr(args, "download", False) or getattr(args, "clean", False):
        set_global_seed(args.seed)

        # Resolve directories
        raw_dir = (
            Path(args.output_dir) if getattr(args, "output_dir", None) else None
        )
        clean_dir = (
            Path(args.clean_dir) if getattr(args, "clean_dir", None) else None
        )

        raw_path, clean_path = _ensure_output_paths(raw_dir, clean_dir)

        if args.download:
            if not raw_path.is_file():
                _download_parquet(raw_path)
            else:
                log.info(
                    "Raw parquet already exists at %s – skipping download.", raw_path
                )

        if args.clean:
            if not raw_path.is_file():
                raise RuntimeError(
                    f"Raw parquet not found at {raw_path}. Run with --download first."
                )
            try:
                df_raw = pd.read_parquet(raw_path)
            except Exception as exc:
                raise RuntimeError(
                    f"Unable to read parquet file from {raw_path}"
                ) from exc

            df_clean = _clean_dataframe(df_raw)
            _write_clean_csv(df_clean, clean_path)

        return

    # Sub‑command interface
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