"""
FEMNIST Data Downloader.

This module downloads the FEMNIST dataset from the Hugging Face Hub
using streaming mode and materializes it into a parquet file.
The implementation respects the project constraints:
* Only the 'femnist' dataset is supported.
* Attempts to download 'shakespeare' raise a ValueError with the mandated message.
* No synthetic fallback - any failure raises a DataFetchError.
* Materializes real data into data/raw/femnist.parquet and data/raw/femnist.sha256.
"""

import argparse
import hashlib
import logging
import sys
from pathlib import Path
from typing import Optional

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
# representative real sample. 200k records of 28x28 images fits in memory.
MAX_RECORDS = 200_000

class DataFetchError(Exception):
    """Raised when the dataset cannot be fetched or written."""

def compute_sha256(file_path: Path) -> str:
    """Compute the SHA-256 checksum of a file."""
    sha256_hash = hashlib.sha256()
    with file_path.open("rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def write_checksum(file_path: Path, checksum: str) -> Path:
    """Write a .sha256 file next to the target file."""
    # Task specifies data/raw/femnist.sha256 (not femnist.parquet.sha256)
    checksum_path = file_path.parent / f"{file_path.stem.replace('.parquet', '')}.sha256"
    checksum_path.write_text(f"{checksum}  {file_path.name}\n")
    log.info(f"Checksum written to {checksum_path}")
    return checksum_path

def download_femnist_streaming(output_dir: Path) -> Path:
    """
    Stream the FEMNIST training split and materialize a parquet file.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    parquet_path = output_dir / "femnist.parquet"
    checksum_path = output_dir / "femnist.sha256"

    # Verify existing file
    if parquet_path.is_file() and checksum_path.is_file():
        stored = checksum_path.read_text().split()[0]
        current = compute_sha256(parquet_path)
        if stored == current:
            log.info("Existing parquet file and checksum verified - skipping download.")
            return parquet_path
        else:
            log.warning("Checksum mismatch - re-downloading dataset.")

    log.info("Streaming FEMNIST from Hugging Face...")
    try:
        # Load streaming dataset
        ds = load_dataset(
            "leaf/femnist",
            split="train",
            streaming=True,
            trust_remote_code=True,
        )

        records = []
        for i, example in enumerate(ds):
            client_id = example.get("user_id")
            label = example.get("label")
            if client_id is None or label is None:
                continue
            
            # Store as minimal representation to save memory
            records.append({"client_id": client_id, "label": label})
            
            if (i + 1) % 50_000 == 0:
                log.info(f"Fetched {i + 1} records...")
            
            if len(records) >= MAX_RECORDS:
                log.info(f"Reached MAX_RECORDS ({MAX_RECORDS}) - stopping materialization.")
                break

        if not records:
            raise DataFetchError("No records retrieved from the streaming endpoint.")

        df = pd.DataFrame(records)
        log.info(f"Writing {len(df)} records to {parquet_path}")
        df.to_parquet(parquet_path, index=False)

        checksum = compute_sha256(parquet_path)
        write_checksum(parquet_path, checksum)

        return parquet_path

    except Exception as e:
        log.exception(f"Fetch failed: {e}")
        raise DataFetchError(f"Failed to download FEMNIST: {e}")

def download_dataset(dataset_name: str, output_dir: Optional[Path] = None) -> Path:
    """Public entry point for dataset download."""
    if output_dir is None:
        output_dir = paths.data("raw")

    name = dataset_name.lower()
    if name in EXCLUDED_DATASETS:
        raise ValueError(EXCLUSION_MESSAGE)

    if name not in SUPPORTED_DATASETS:
        raise ValueError(f"Unsupported dataset: {dataset_name}")

    if name == "femnist":
        return download_femnist_streaming(output_dir)

    raise ValueError(f"No handler for dataset: {dataset_name}")

def main() -> None:
    parser = argparse.ArgumentParser(description="Download FEMNIST dataset.")
    parser.add_argument("--dataset", type=str, default="femnist", help="Dataset name.")
    parser.add_argument("--output-dir", type=str, default=None, help="Output directory.")
    args = parser.parse_args()

    out_dir = Path(args.output_dir) if args.output_dir else paths.data("raw")

    try:
        log.info(f"Initiating download for dataset: {args.dataset}")
        parquet_path = download_dataset(args.dataset, out_dir)
        log.info(f"Dataset successfully stored at {parquet_path}")
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