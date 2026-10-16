"""
src.ingest.load_illusions
=========================

This module provides a command-line interface for downloading and cleaning the
Müller‑Lyer and Ponzo illusion datasets from OpenNeuro/HuggingFace.

It supports two usage styles:
1. Sub‑command style: ``python -m src.ingest.load_illusions download_muller``
   or ``python -m src.ingest.load_illusions download_ponzo``.
2. Flag‑based style (currently for Müller‑Lyer only): ``python -m src.ingest.load_illusions --download --clean``

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
# Configuration for Müller‑Lyer
# ----------------------------------------------------------------------
MULLER_REPO_IDS = [
    "openneuro/muller-lyer",
    "OpenNeuro/muller-lyer",
    "openneuro/muller_lyer",
    "OpenNeuro/muller_lyer",
]

MULLER_PARQUET_FILENAME = "muller_lyer.parquet"

MULLER_REQUIRED_COLUMNS = [
    "subject_id",
    "stimulus_type",
    "response",
    "trial_id",
    "stimulus_parameters",
]

# ----------------------------------------------------------------------
# Configuration for Ponzo
# ----------------------------------------------------------------------
PONZO_REPO_IDS = [
    "openneuro/ponzo",
    "OpenNeuro/ponzo",
    "openneuro/ponzo_illusion",
    "OpenNeuro/ponzo_illusion",
]

PONZO_PARQUET_FILENAME = "ponzo.parquet"

PONZO_REQUIRED_COLUMNS = [
    "subject_id",
    "response",
    "arrow_angle",
    "depth_cue",
]

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Helper functions (generic)
# ----------------------------------------------------------------------
def _ensure_output_paths(
    raw_dir: Path | None = None,
    clean_dir: Path | None = None,
    dataset: str = "muller",
) -> tuple[Path, Path]:
    """Return paths for raw parquet and cleaned CSV, creating dirs if needed."""
    if dataset == "muller":
        raw_filename = MULLER_PARQUET_FILENAME
        clean_filename = "clean_muller_lyer.csv"
    elif dataset == "ponzo":
        raw_filename = PONZO_PARQUET_FILENAME
        clean_filename = "clean_ponzo.csv"
    else:
        raise ValueError(f"Unsupported dataset: {dataset}")

    raw_path = (raw_dir / raw_filename) if raw_dir else paths.data("raw", raw_filename)
    clean_path = (clean_dir / clean_filename) if clean_dir else paths.data("clean", clean_filename)

    raw_path.parent.mkdir(parents=True, exist_ok=True)
    clean_path.parent.mkdir(parents=True, exist_ok=True)

    return raw_path, clean_path

def _download_parquet(
    raw_path: Path,
    repo_ids: list[str],
    filename: str,
) -> None:
    """
    Download a parquet file using multiple strategies:
    1. Direct file download via ``hf_hub_download`` (repo_type="dataset").
    2. ``datasets.load_dataset`` for dataset objects.
    """
    log.info("Attempting to download parquet file %s", filename)

    # Strategy 1: Direct file download via hf_hub_download
    for repo_id in repo_ids:
        try:
            downloaded_file = hf_hub_download(
                repo_id=repo_id,
                filename=filename,
                repo_type="dataset",
            )
            log.info("Successfully downloaded via hf_hub_download from %s", repo_id)
            shutil.copyfile(downloaded_file, raw_path)
            return
        except Exception as exc:
            log.debug("hf_hub_download failed for %s: %s", repo_id, exc)

    # Strategy 2: Use datasets.load_dataset (handles dataset objects)
    for repo_id in repo_ids:
        try:
            ds = load_dataset(repo_id, split="train", streaming=False)
            df = ds.to_pandas()
            df.to_parquet(raw_path, index=False)
            log.info("Successfully loaded dataset via datasets.load_dataset from %s", repo_id)
            return
        except Exception as exc:
            log.debug("load_dataset failed for %s: %s", repo_id, exc)

    raise RuntimeError(
        f"Failed to download parquet from any known sources: {repo_ids}. "
        "Please verify dataset availability or provide a direct URL."
    )

def _clean_dataframe(df: pd.DataFrame, required_columns: list[str]) -> pd.DataFrame:
    """Enforce column presence, drop NaNs in critical fields, and warn on duplicates."""
    missing_cols = [c for c in required_columns if c not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Drop rows with missing values in critical columns (FR‑001)
    before_rows = len(df)
    df_clean = df.dropna(subset=required_columns)
    dropped = before_rows - len(df_clean)
    if dropped > 0:
        log.warning("Dropped %d rows with missing values in required columns.", dropped)

    # Warn about duplicate subject IDs (FR‑001: warn, not error)
    if "subject_id" in df_clean.columns:
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
# High‑level download & clean for each dataset
# ----------------------------------------------------------------------
def download_and_clean_muller(seed: int = 42) -> None:
    """Download and clean the Müller‑Lyer dataset."""
    set_global_seed(seed)
    raw_path, clean_path = _ensure_output_paths(dataset="muller")

    if not raw_path.is_file():
        _download_parquet(raw_path, MULLER_REPO_IDS, MULLER_PARQUET_FILENAME)
    else:
        log.info("Raw parquet already exists at %s – skipping download.", raw_path)

    df_raw = pd.read_parquet(raw_path)
    df_clean = _clean_dataframe(df_raw, MULLER_REQUIRED_COLUMNS)
    _write_clean_csv(df_clean, clean_path)

def download_and_clean_ponzo(seed: int = 42) -> None:
    """Download and clean the Ponzo dataset."""
    set_global_seed(seed)
    raw_path, clean_path = _ensure_output_paths(dataset="ponzo")

    if not raw_path.is_file():
        _download_parquet(raw_path, PONZO_REPO_IDS, PONZO_PARQUET_FILENAME)
    else:
        log.info("Raw parquet already exists at %s – skipping download.", raw_path)

    df_raw = pd.read_parquet(raw_path)
    df_clean = _clean_dataframe(df_raw, PONZO_REQUIRED_COLUMNS)
    _write_clean_csv(df_clean, clean_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for both sub‑command and flag‑based styles."""
    if argv is None:
        argv = sys.argv[1:]

    # Detect flag‑style usage
    if any(arg.startswith("--download") or arg.startswith("--clean") for arg in argv):
        parser = argparse.ArgumentParser(description="Download/clean illusion datasets.")
        parser.add_argument("--download", action="store_true")
        parser.add_argument("--clean", action="store_true")
        parser.add_argument("--output-dir", type=str, default="data/raw")
        parser.add_argument("--raw-dir", type=str, default="data/raw")
        parser.add_argument("--clean-dir", type=str, default="data/clean")
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument("--dataset", choices=["muller", "ponzo"], default="muller",
                            help="Select which dataset to operate on (flag style only).")
        return parser.parse_args(argv)

    # Sub‑command style
    parser = argparse.ArgumentParser(description="Download/clean illusion datasets.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dl_muller = subparsers.add_parser("download_muller")
    dl_muller.add_argument("--seed", type=int, default=42)

    dl_ponzo = subparsers.add_parser("download_ponzo")
    dl_ponzo.add_argument("--seed", type=int, default=42)

    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    # Flag‑style handling (currently only supports Müller‑Lyer, but dataset can be chosen)
    if getattr(args, "download", False) or getattr(args, "clean", False):
        set_global_seed(args.seed)
        raw_dir = Path(args.output_dir) if getattr(args, "output_dir", None) else None
        clean_dir = Path(args.clean_dir) if getattr(args, "clean_dir", None) else None
        dataset = getattr(args, "dataset", "muller")

        raw_path, clean_path = _ensure_output_paths(raw_dir, clean_dir, dataset=dataset)

        if args.download:
            if not raw_path.is_file():
                if dataset == "muller":
                    _download_parquet(raw_path, MULLER_REPO_IDS, MULLER_PARQUET_FILENAME)
                else:  # ponzo
                    _download_parquet(raw_path, PONZO_REPO_IDS, PONZO_PARQUET_FILENAME)
            else:
                log.info("Raw parquet already exists at %s – skipping download.", raw_path)

        if args.clean:
            if not raw_path.is_file():
                raise RuntimeError(f"Raw parquet not found at {raw_path}. Run --download first.")
            df_raw = pd.read_parquet(raw_path)
            required = MULLER_REQUIRED_COLUMNS if dataset == "muller" else PONZO_REQUIRED_COLUMNS
            df_clean = _clean_dataframe(df_raw, required)
            _write_clean_csv(df_clean, clean_path)
        return

    # Sub‑command handling
    if args.command == "download_muller":
        log.info("Running download_muller with seed=%s", args.seed)
        download_and_clean_muller(seed=args.seed)
    elif args.command == "download_ponzo":
        log.info("Running download_ponzo with seed=%s", args.seed)
        download_and_clean_ponzo(seed=args.seed)

if __name__ == "__main__":
    main(sys.argv[1:])
