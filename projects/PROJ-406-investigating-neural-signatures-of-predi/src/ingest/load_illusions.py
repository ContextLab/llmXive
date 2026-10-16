"""
src.ingest.load_illusions
=========================

This module provides a command-line interface for downloading and cleaning the
Müller-Lyer illusion dataset from OpenNeuro/HuggingFace.

It supports two usage styles:
1. Sub-command style: python -m src.ingest.load_illusions download_muller
2. Flag-based style: python -m src.ingest.load_illusions --download --clean

The implementation is deterministic and enforces the required data schema.
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
# We try multiple potential repository IDs and methods to ensure we find the data.
# These are based on common OpenNeuro mirroring patterns on Hugging Face.
OPENNEURO_REPO_IDS = [
    "openneuro/muller-lyer",
    "OpenNeuro/muller-lyer",
    "openneuro/muller_lyer",
    "OpenNeuro/muller_lyer",
]

PARQUET_FILENAME = "muller_lyer.parquet"

# Required columns as per FR-001 and spec.md
REQUIRED_COLUMNS = [
    "subject_id",
    "stimulus_type",
    "response",
    "trial_id",
    "stimulus_parameters",
]

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def _ensure_output_paths(
    raw_dir: Path | None = None, clean_dir: Path | None = None
) -> tuple[Path, Path]:
    """Return paths for raw parquet and cleaned CSV, creating dirs if needed."""
    if raw_dir is None:
        raw_path = paths.data("raw", "muller_lyer.parquet")
    else:
        raw_path = raw_dir / "muller_lyer.parquet"

    if clean_dir is None:
        clean_path = paths.data("clean", "clean_muller_lyer.csv")
    else:
        clean_path = clean_dir / "clean_muller_lyer.csv"

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path.parent.mkdir(parents=True, exist_ok=True)

    return raw_path, clean_path

def _download_parquet(raw_path: Path) -> None:
    """
    Download the parquet file using multiple strategies:
    1. Try hf_hub_download for direct file access.
    2. Try datasets.load_dataset to handle HF dataset objects.
    """
    log.info("Attempting to download Müller-Lyer dataset from OpenNeuro/HF")
    
    # Strategy 1: Direct file download via hf_hub_download
    for repo_id in OPENNEURO_REPO_IDS:
        try:
            downloaded_file = hf_hub_download(
                repo_id=repo_id,
                filename=PARQUET_FILENAME,
            )
            log.info("Successfully downloaded file from repo %s", repo_id)
            shutil.copyfile(downloaded_file, raw_path)
            return
        except Exception as exc:
            log.debug("hf_hub_download failed for %s: %s", repo_id, exc)

    # Strategy 2: Use datasets.load_dataset (handles dataset objects)
    for repo_id in OPENNEURO_REPO_IDS:
        try:
            # Load dataset and convert to pandas
            ds = load_dataset(repo_id, split='train', streaming=False)
            df = ds.to_pandas()
            df.to_parquet(raw_path, index=False)
            log.info("Successfully loaded dataset from repo %s via datasets.load_dataset", repo_id)
            return
        except Exception as exc:
            log.debug("load_dataset failed for %s: %s", repo_id, exc)

    raise RuntimeError(
        f"Failed to download Müller-Lyer data from any known sources: {OPENNEURO_REPO_IDS}. "
        "Please verify dataset availability or provide a direct URL."
    )

def _clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Enforce column presence, drop NaNs in critical fields, and warn on duplicates."""
    missing_cols = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Drop rows with missing values in critical columns (FR-001)
    before_rows = len(df)
    df_clean = df.dropna(subset=REQUIRED_COLUMNS)
    dropped = before_rows - len(df_clean)
    if dropped > 0:
        log.warning("Dropped %d rows with missing values in required columns.", dropped)

    # Warn about duplicate subject IDs (FR-001: warn, not error)
    dup_counts = df_clean["subject_id"].value_counts()
    duplicate_subjects = dup_counts[dup_counts > 1]
    if not duplicate_subjects.empty:
        log.warning(
            "Found %d duplicate subject_id entries. Duplicates retained but flagged.",
            duplicate_subjects.size,
        )
    return df_clean

def _write_clean_csv(df_clean: pd.DataFrame, clean_path: Path) -> None:
    """Write the cleaned DataFrame to CSV."""
    log.info("Writing cleaned CSV to %s", clean_path)
    df_clean.to_csv(clean_path, index=False, encoding="utf-8")

# ----------------------------------------------------------------------
# Public API
# ----------------------------------------------------------------------
def download_and_clean(seed: int = 42) -> None:
    """High-level function to download and clean the dataset."""
    set_global_seed(seed)
    raw_path, clean_path = _ensure_output_paths()

    if not raw_path.is_file():
        _download_parquet(raw_path)
    else:
        log.info("Raw parquet already exists at %s – skipping download.", raw_path)

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
    """Parse CLI arguments for both sub-command and flag-based styles."""
    if any(arg.startswith("--download") or arg.startswith("--clean") for arg in (argv or [])):
        parser = argparse.ArgumentParser(description="Download/clean Müller-Lyer dataset.")
        parser.add_argument("--download", action="store_true")
        parser.add_argument("--clean", action="store_true")
        parser.add_argument("--output-dir", type=str, default="data/raw")
        parser.add_argument("--raw-dir", type=str, default="data/raw")
        parser.add_argument("--clean-dir", type=str, default="data/clean")
        parser.add_argument("--seed", type=int, default=42)
        return parser.parse_args(argv)

    parser = argparse.ArgumentParser(description="Download/clean Müller-Lyer dataset.")
    subparsers = parser.add_subparsers(dest="command", required=True)
    dl_parser = subparsers.add_parser("download_muller")
    dl_parser.add_argument("--seed", type=int, default=42)
    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    if getattr(args, "download", False) or getattr(args, "clean", False):
        set_global_seed(args.seed)
        raw_dir = Path(args.output_dir) if getattr(args, "output_dir", None) else None
        clean_dir = Path(args.clean_dir) if getattr(args, "clean_dir", None) else None
        raw_path, clean_path = _ensure_output_paths(raw_dir, clean_dir)

        if args.download:
            if not raw_path.is_file():
                _download_parquet(raw_path)
            else:
                log.info("Raw parquet already exists at %s", raw_path)

        if args.clean:
            if not raw_path.is_file():
                raise RuntimeError(f"Raw parquet not found at {raw_path}. Run --download first.")
            df_raw = pd.read_parquet(raw_path)
            df_clean = _clean_dataframe(df_raw)
            _write_clean_csv(df_clean, clean_path)
        return

    if args.command == "download_muller":
        log.info("Running download_muller with seed=%s", args.seed)
        download_and_clean(seed=args.seed)

if __name__ == "__main__":
    main(sys.argv[1:])