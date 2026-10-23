"""
agp_loader.py
----------------
This module implements Task T001: download the American Gut Project (AGP)
raw 16S count table and associated metadata using the HuggingFace
`datasets` library (or, more directly, the `huggingface_hub` utility).
The script writes two TSV files to ``data/raw/agp/``:

* ``agp_counts.tsv``   – taxon abundance matrix (samples × taxa)
* ``agp_metadata.tsv`` – sample‑level metadata

It also creates a SHA‑256 checksum manifest at
``data/state/agp_checksums.json`` containing an entry for each file.

The script is executable via:

``python -m code.src.ingestion.agp_loader``

It can also be imported and called programmatically via the
``download_agp_dataset`` function.
"""

import argparse
import hashlib
import json
import logging
import sys
from pathlib import Path
from typing import Dict, Tuple

import pandas as pd
from datasets import load_dataset
from huggingface_hub import hf_hub_download

# Project‑wide logger utility (already part of the repo)
from src.utils.logger import get_logger

# ----------------------------------------------------------------------
# Helper utilities – these were already present in the original file.
# They are retained for backwards compatibility but are not used by the
# new download implementation.
# ----------------------------------------------------------------------
def get_project_root() -> Path:
    """Return the repository root (the folder that contains the top‑level ``.git``)."""
    current = Path(__file__).resolve()
    while current != current.parent:
        if (current / ".git").exists():
            return current
        current = current.parent
    # Fallback for environments without a ``.git`` folder.
    return Path(__file__).resolve().parents[3]

def verify_url(url: str) -> bool:
    """Very light‑weight URL sanity check – used only for defensive logging."""
    return url.startswith("http")

def ensure_qiita_token() -> str:
    """Legacy helper – retained for API compatibility."""
    token = os.getenv("QIITA_API_TOKEN")
    if not token:
        raise RuntimeError(
            "QIITA_API_TOKEN environment variable is not set. "
            "Please set it to access the Qiita API."
        )
    return token

def calculate_file_checksum(file_path: Path) -> str:
    """Calculate a SHA‑256 checksum for ``file_path``."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def record_checksum(file_path: Path, checksum: str, state_file: Path) -> None:
    """
    Record the checksum of ``file_path`` in ``state_file`` (a JSON mapping).
    The JSON is created if it does not already exist.
    """
    state_file.parent.mkdir(parents=True, exist_ok=True)
    if state_file.exists():
        with open(state_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    else:
        data = {}

    data[file_path.name] = checksum

    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, sort_keys=True)

# ----------------------------------------------------------------------
# New implementation – download the AGP dataset.
# ----------------------------------------------------------------------
def _download_file_from_hub(repo_id: str, filename: str, dest: Path) -> Path:
    """
    Download a single file from a HuggingFace hub repository and place it at ``dest``.
    Returns the path to the downloaded file.
    """
    # ``hf_hub_download`` returns the local cache path; we then copy it.
    cache_path = hf_hub_download(repo_id=repo_id, filename=filename)
    dest.parent.mkdir(parents=True, exist_ok=True)
    # Overwrite if the file already exists (ensures reproducibility).
    dest.write_bytes(Path(cache_path).read_bytes())
    return dest

def download_agp_dataset(
    raw_dir: Path,
    state_file: Path,
    logger: logging.Logger,
) -> Tuple[Path, Path]:
    """
    Download the American Gut Project (AGP) count and metadata TSV files.

    Parameters
    ----------
    raw_dir: Path
        Directory where the raw TSV files will be written
        (e.g. ``data/raw/agp``).
    state_file: Path
        JSON file that will store the SHA‑256 checksums.
    logger: logging.Logger
        Logger for progress reporting.

    Returns
    -------
    Tuple[Path, Path]
        Paths to the written ``agp_counts.tsv`` and ``agp_metadata.tsv`` files.
    """
    repo_id = "american_gut/agp_diet"
    counts_filename = "agp_counts.tsv"
    meta_filename = "agp_metadata.tsv"

    logger.info(f"Starting download of AGP dataset from repository '{repo_id}'.")
    counts_path = raw_dir / counts_filename
    meta_path = raw_dir / meta_filename

    # Download both files via the Hub API.
    _download_file_from_hub(repo_id, counts_filename, counts_path)
    logger.info(f"Downloaded counts to {counts_path}")

    _download_file_from_hub(repo_id, meta_filename, meta_path)
    logger.info(f"Downloaded metadata to {meta_path}")

    # Verify that both files are non‑empty.
    if counts_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded counts file {counts_path} is empty.")
    if meta_path.stat().st_size == 0:
        raise RuntimeError(f"Downloaded metadata file {meta_path} is empty.")

    # Compute checksums and record them.
    counts_checksum = calculate_file_checksum(counts_path)
    meta_checksum = calculate_file_checksum(meta_path)

    record_checksum(counts_path, counts_checksum, state_file)
    record_checksum(meta_path, meta_checksum, state_file)

    logger.info(f"Checksums recorded in {state_file}")
    logger.info(f"  {counts_path.name}: {counts_checksum}")
    logger.info(f"  {meta_path.name}: {meta_checksum}")

    return counts_path, meta_path

# ----------------------------------------------------------------------
# CLI entry point
# ----------------------------------------------------------------------
def build_arg_parser() -> argparse.ArgumentParser:
    """Construct ``argparse`` parser for the module."""
    parser = argparse.ArgumentParser(
        description="Download the American Gut Project (AGP) raw 16S count table and metadata."
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=None,
        help="Directory to store the raw TSV files. "
             "If omitted, defaults to ``data/raw/agp`` via the llmxive toolkit.",
    )
    parser.add_argument(
        "--state-file",
        type=Path,
        default=None,
        help="Path to the JSON checksum manifest. "
             "If omitted, defaults to ``data/state/agp_checksums.json``.",
    )
    parser.add_argument(
        "--log-level",
        default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity.",
    )
    return parser

def main() -> None:
    """CLI driver – downloads the dataset and writes checksums."""
    parser = build_arg_parser()
    args = parser.parse_args()

    # Resolve default locations using the llmxive toolkit helpers.
    from llmxive_toolkit import paths

    raw_dir = args.raw_dir or paths.data("raw", "agp")
    state_file = args.state_file or paths.data("state", "agp_checksums.json")

    # Configure logger
    logger = get_logger("agp_loader")
    logger.setLevel(getattr(logging, args.log_level))
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    )
    logger.addHandler(handler)

    try:
        download_agp_dataset(raw_dir=raw_dir, state_file=state_file, logger=logger)
        logger.info("AGP dataset download completed successfully.")
    except Exception as exc:
        logger.error(f"Failed to download AGP dataset: {exc}")
        sys.exit(1)

if __name__ == "__main__":
    main()
