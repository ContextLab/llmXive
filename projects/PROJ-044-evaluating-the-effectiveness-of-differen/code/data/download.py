"""
FEMNIST Data Downloader.

This module downloads the FEMNIST dataset from the Hugging Face Hub
using streaming mode and materializes it into two parquet files
(train and test). It also computes a SHA‑256 checksum over the
concatenated bytes of both parquet files and writes it to
`data/raw/femnist.sha256`.

Behaviour:
* Only the 'femnist' dataset is supported.
* Attempts to download 'shakespeare' raise a ValueError with the mandated
  message.
* No synthetic fallback – any failure raises a DataFetchError.
* Files are written under the project’s `data/raw/` directory.
"""

import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional, Tuple

import pandas as pd
from datasets import load_dataset

from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

# ----------------------------------------------------------------------
# Constants & configuration
# ----------------------------------------------------------------------
SUPPORTED_DATASETS = {"femnist"}
EXCLUDED_DATASETS = {"shakespeare"}
EXCLUSION_MESSAGE = "Shakespeare excluded per plan.md Gap Analysis"

# Limit records to avoid OOM during materialization while maintaining a
# representative real sample. 200k records per split (train / test) fits in memory.
MAX_RECORDS = 200_000

class DataFetchError(Exception):
    """Raised when the dataset cannot be fetched or written."""


def _compute_sha256(file_path: Path) -> str:
    """Compute the SHA‑256 checksum of a single file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def _write_checksum(checksum_path: Path, checksum: str) -> None:
    """Write a checksum file in the format ``<hash>  <filename>``."""
    checksum_path.write_text(f"{checksum}  {checksum_path.stem}.parquet\n")
    log.info(f"Checksum written to {checksum_path}")


def _stream_and_write(split: str, output_path: Path) -> Path:
    """
    Stream a FEMNIST split and write it to a parquet file.

    Args:
        split: Either ``"train"`` or ``"test"``.
        output_path: Full path (including filename) where the parquet file will be saved.

    Returns:
        Path to the written parquet file.
    """
    log.info(f"Streaming FEMNIST {split} split...")
    try:
        ds = load_dataset(
            "federated/femnist",
            split=split,
            streaming=True,
            trust_remote_code=True,
        )
    except Exception as e:
        log.exception(f"Failed to load FEMNIST {split} split: {e}")
        raise DataFetchError(f"Failed to load FEMNIST {split} split: {e}")

    records = []
    for i, example in enumerate(ds):
        client_id = example.get("user_id")
        label = example.get("label")
        if client_id is None or label is None:
            continue
        records.append({"client_id": client_id, "label": label})

        if (i + 1) % 50_000 == 0:
            log.info(f"Fetched {i + 1} records from {split} split...")

        if len(records) >= MAX_RECORDS:
            log.info(f"Reached MAX_RECORDS ({MAX_RECORDS}) for {split} – stopping.")
            break

    if not records:
        raise DataFetchError(f"No records retrieved from FEMNIST {split} split.")

    df = pd.DataFrame(records)
    log.info(f"Writing {len(df)} records to {output_path}")
    df.to_parquet(output_path, index=False)
    return output_path


def download_femnist(output_dir: Optional[Path] = None) -> Tuple[Path, Path]:
    """
    Download both train and test splits of FEMNIST, materialize them as parquet,
    and write a combined SHA‑256 checksum.

    Returns:
        Tuple containing paths to the train and test parquet files.
    """
    if output_dir is None:
        output_dir = paths.data("raw")
    output_dir.mkdir(parents=True, exist_ok=True)

    train_path = output_dir / "femnist_train.parquet"
    test_path = output_dir / "femnist_test.parquet"
    checksum_path = output_dir / "femnist.sha256"

    # If files already exist and checksum matches, skip re‑download.
    if train_path.is_file() and test_path.is_file() and checksum_path.is_file():
        stored = checksum_path.read_text().split()[0]
        combined = train_path.read_bytes() + test_path.read_bytes()
        current = hashlib.sha256(combined).hexdigest()
        if stored == current:
            log.info("Existing parquet files and checksum verified – skipping download.")
            return train_path, test_path
        else:
            log.warning("Checksum mismatch – re‑downloading dataset.")

    # Stream and write each split.
    _stream_and_write("train", train_path)
    _stream_and_write("test", test_path)

    # Compute combined checksum.
    combined_bytes = train_path.read_bytes() + test_path.read_bytes()
    combined_hash = hashlib.sha256(combined_bytes).hexdigest()
    _write_checksum(checksum_path, combined_hash)

    return train_path, test_path


def download_dataset(dataset_name: str, output_dir: Optional[Path] = None) -> Tuple[Path, ...]:
    """
    Public entry point for dataset download.

    Args:
        dataset_name: Name of the dataset (case‑insensitive).
        output_dir: Optional custom output directory.

    Returns:
        Tuple of paths to the generated files.
    """
    name = dataset_name.lower()
    if name in EXCLUDED_DATASETS:
        raise ValueError(EXCLUSION_MESSAGE)

    if name not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    if name == "femnist":
        return download_femnist(output_dir)

    raise ValueError(f"No handler for dataset: {dataset_name}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Download FEMNIST dataset.")
    parser.add_argument(
        "--dataset",
        type=str,
        default="femnist",
        help="Dataset name (only 'femnist' is supported).",
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Output directory (defaults to data/raw).",
    )
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else paths.data("raw")

    try:
        log.info(f"Initiating download for dataset: {args.dataset}")
        train_path, test_path = download_dataset(args.dataset, out_dir)
        log.info(f"Dataset successfully stored at {train_path} and {test_path}")
        sys.exit(0)
    except ValueError as ve:
        log.error(f"Configuration error: {ve}")
        sys.exit(1)
    except DataFetchError as dfe:
        log.error(f"Data fetch error: {dfe}")
        sys.exit(1)
    except Exception as e:
        log.exception(f"Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()