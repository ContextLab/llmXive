"""
src.ingest.load_illusions
=========================

This module provides a command-line interface for downloading the
Müller‑Lyer and Ponzo illusion datasets from verified public sources.
It supports both sub‑command style (e.g. ``python -m src.ingest.load_illusions download_muller``)
and a limited flag‑style interface.

The implementation avoids the ``datasets`` library (which pulls in ``pyarrow``
that is incompatible with the default NumPy version) and instead uses
``huggingface_hub`` to fetch the raw parquet files directly.  After download
the raw file is validated for required columns and for uniqueness of the
``subject_id`` field; any duplicate ``subject_id`` values cause a hard error
(FR‑001).  A SHA‑256 checksum of the downloaded file is recorded in
``data/manifest.yaml`` for provenance.

The module also offers optional cleaning of the raw parquet into a tidy CSV
for downstream steps, but the primary task (T001) only requires the raw
parquet and its checksum.
"""

import argparse
import hashlib
import logging
import sys
from pathlib import Path
import shutil

import pandas as pd
import yaml
from huggingface_hub import hf_hub_download

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
    "trial_id",
    "stimulus_length",
    "response_length",
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
    "trial_id",
    "arrow_angle",
    "depth_cue",
    "perceived_length",
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
    Download a parquet file using ``hf_hub_download`` from the first repository
    that succeeds.  If none succeed, raise a clear ``RuntimeError``.
    """
    log.info("Attempting to download parquet file %s", filename)

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
        except Exception as exc:  # pragma: no cover – only logs on failure
            log.debug("hf_hub_download failed for %s: %s", repo_id, exc)

    raise RuntimeError(
        f"Failed to download parquet from any known sources: {repo_ids}. "
        "Please verify dataset availability or provide a direct URL."
    )

def _compute_sha256(path: Path) -> str:
    """Compute the SHA‑256 checksum of a file."""
    hasher = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            hasher.update(chunk)
    return hasher.hexdigest()

def _update_manifest(dataset: str, checksum: str, relative_path: str) -> None:
    """
    Record the checksum of a downloaded artifact in ``data/manifest.yaml``.
    The manifest is a simple mapping:
    ```yaml
    muller:
      path: data/raw/muller_lyer.parquet
      sha256: <hex>
    ponzo:
      path: data/raw/ponzo.parquet
      sha256: <hex>
    ```
    """
    manifest_path = paths.data("manifest.yaml")
    if manifest_path.is_file():
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f) or {}
    else:
        manifest = {}

    manifest[dataset] = {"path": relative_path, "sha256": checksum}

    with open(manifest_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(manifest, f, sort_keys=False)

def _validate_dataframe(df: pd.DataFrame, required_columns: list[str]) -> None:
    """Validate required columns exist and that ``subject_id`` is unique."""
    missing = [c for c in required_columns if c not in df.columns]
    if missing:
        raise ValueError(f"Dataset is missing required columns: {missing}")

    if "subject_id" in df.columns:
        dup_counts = df["subject_id"].value_counts()
        duplicates = dup_counts[dup_counts > 1]
        if not duplicates.empty:
            dup_list = duplicates.index.tolist()
            raise ValueError(
                f"Duplicate subject_id values found: {dup_list}. "
                "Each subject_id must be unique (FR‑001)."
            )

def _clean_dataframe(df: pd.DataFrame, required_columns: list[str]) -> pd.DataFrame:
    """Drop rows with missing values in required columns."""
    before = len(df)
    df_clean = df.dropna(subset=required_columns)
    dropped = before - len(df_clean)
    if dropped:
        log.warning("Dropped %d rows with missing required fields.", dropped)
    return df_clean

def _write_clean_csv(df_clean: pd.DataFrame, clean_path: Path) -> None:
    """Write the cleaned DataFrame to CSV."""
    log.info("Writing cleaned CSV to %s", clean_path)
    df_clean.to_csv(clean_path, index=False, encoding="utf-8")

# ----------------------------------------------------------------------
# High‑level download & optional clean for each dataset
# ----------------------------------------------------------------------
def download_and_clean_muller(seed: int = 42) -> None:
    """Download (and optionally clean) the Müller‑Lyer dataset."""
    set_global_seed(seed)
    raw_path, clean_path = _ensure_output_paths(dataset="muller")

    if not raw_path.is_file():
        _download_parquet(raw_path, MULLER_REPO_IDS, MULLER_PARQUET_FILENAME)
    else:
        log.info("Raw parquet already exists at %s – skipping download.", raw_path)

    # Compute checksum and record provenance
    checksum = _compute_sha256(raw_path)
    _update_manifest("muller", checksum, str(raw_path.relative_to(paths.root)))

    # Validate raw data
    df_raw = pd.read_parquet(raw_path)
    _validate_dataframe(df_raw, MULLER_REQUIRED_COLUMNS)

    # Optional cleaning step (used by later pipeline stages)
    df_clean = _clean_dataframe(df_raw, MULLER_REQUIRED_COLUMNS)
    _write_clean_csv(df_clean, clean_path)

def download_and_clean_ponzo(seed: int = 42) -> None:
    """Download (and optionally clean) the Ponzo dataset."""
    set_global_seed(seed)
    raw_path, clean_path = _ensure_output_paths(dataset="ponzo")

    if not raw_path.is_file():
        _download_parquet(raw_path, PONZO_REPO_IDS, PONZO_PARQUET_FILENAME)
    else:
        log.info("Raw parquet already exists at %s – skipping download.", raw_path)

    # Compute checksum and record provenance
    checksum = _compute_sha256(raw_path)
    _update_manifest("ponzo", checksum, str(raw_path.relative_to(paths.root)))

    # Validate raw data
    df_raw = pd.read_parquet(raw_path)
    _validate_dataframe(df_raw, PONZO_REQUIRED_COLUMNS)

    # Optional cleaning step
    df_clean = _clean_dataframe(df_raw, PONZO_REQUIRED_COLUMNS)
    _write_clean_csv(df_clean, clean_path)

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def _parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments for both sub‑command and flag‑style usage."""
    if argv is None:
        argv = sys.argv[1:]

    # Flag‑style detection
    if any(arg.startswith("--") for arg in argv):
        parser = argparse.ArgumentParser(description="Download/clean illusion datasets (flag style).")
        parser.add_argument("--download", action="store_true", help="Download the raw parquet file.")
        parser.add_argument("--clean", action="store_true", help="Clean the raw parquet into CSV.")
        parser.add_argument("--output-dir", type=str, default="data/raw", help="Directory for raw parquet.")
        parser.add_argument("--raw-dir", type=str, default="data/raw", help="Directory containing raw parquet.")
        parser.add_argument("--clean-dir", type=str, default="data/clean", help="Directory for cleaned CSV.")
        parser.add_argument("--seed", type=int, default=42)
        parser.add_argument(
            "--dataset",
            choices=["muller", "ponzo"],
            default="muller",
            help="Select dataset when using flag‑style interface.",
        )
        return parser.parse_args(argv)

    # Sub‑command style
    parser = argparse.ArgumentParser(description="Download/clean illusion datasets (sub‑command style).")
    subparsers = parser.add_subparsers(dest="command", required=True)

    dl_muller = subparsers.add_parser("download_muller", help="Download and clean Müller‑Lyer dataset.")
    dl_muller.add_argument("--seed", type=int, default=42)

    dl_ponzo = subparsers.add_parser("download_ponzo", help="Download and clean Ponzo dataset.")
    dl_ponzo.add_argument("--seed", type=int, default=42)

    return parser.parse_args(argv)

def main(argv: list[str] | None = None) -> None:
    args = _parse_args(argv)

    # Flag‑style handling
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
                else:
                    _download_parquet(raw_path, PONZO_REPO_IDS, PONZO_PARQUET_FILENAME)
            else:
                log.info("Raw parquet already exists at %s – skipping download.", raw_path)

            # Record checksum after download
            checksum = _compute_sha256(raw_path)
            _update_manifest(dataset, checksum, str(raw_path.relative_to(paths.root)))

            # Validate dataset immediately after download
            df_raw = pd.read_parquet(raw_path)
            required = MULLER_REQUIRED_COLUMNS if dataset == "muller" else PONZO_REQUIRED_COLUMNS
            _validate_dataframe(df_raw, required)

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
