"""
Download the FluorDB v1.0 dataset and store it as a Parquet
file under ``data/raw/fluordb/fluordb.parquet``. The script also writes a SHA‑256
checksum file (``checksums.txt``) and a simple log (``download.log``). It aborts if
fewer than 500 rows are present.

The implementation prioritizes direct file download via URL to ensure reliability
on CI runners, falling back to the HuggingFace ``datasets`` library if necessary.
"""

import argparse
import sys
import hashlib
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger
from code.data.download_raw import download_file

log = get_logger(__name__)

# Minimum number of rows required for the downstream pipeline.
MIN_ROWS = 500
CHECKSUMS_FILENAME = "checksums.txt"
LOG_FILENAME = "download.log"


def compute_sha256(file_path: Path) -> str:
    """Return the SHA‑256 checksum of ``file_path``."""
    sha256 = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256.update(chunk)
    return sha256.hexdigest()


def write_log(message: str):
    """Write a one‑line log file under ``data/raw/fluordb``."""
    log_path = paths.data("raw", "fluordb", LOG_FILENAME)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(message + "\n")
    log.info(f"Wrote log to {log_path}")


def _load_via_hf_library() -> pd.DataFrame:
    """Fallback: Load the FluorDB v1.0 dataset using the ``datasets`` library."""
    try:
        ds = load_dataset("fluordb/v1", split="train", streaming=False)
        df = ds.to_pandas()
        return df
    except Exception as e:
        log.warning(f"HF library load failed: {e}")
        raise


def _validate_and_clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure required column names and return only necessary subset."""
    if "smiles" not in df.columns:
        raise RuntimeError("FluorDB dataset does not contain a 'smiles' column.")
    
    # Target column may be named 'fqy' or already 'fqy_raw'.
    if "fqy_raw" not in df.columns:
        if "fqy" in df.columns:
            df = df.rename(columns={"fqy": "fqy_raw"})
        else:
            raise RuntimeError(
                "FluorDB dataset missing target column. Expected 'fqy' or 'fqy_raw'."
            )
    return df[["smiles", "fqy_raw"]]


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Download FluorDB v1.0 and store it as Parquet."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="https://huggingface.co/datasets/fluordb/v1/resolve/main/data/fluordb.parquet",
        help="URL of the source parquet file."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=paths.data("raw", "fluordb", "fluordb.parquet"),
        help="Path where the parquet file will be written."
    )
    args = parser.parse_args(argv)

    output_path = args.output
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Strategy 1: Direct download via URL (most robust for CI)
    success = False
    try:
        log.info(f"Attempting direct download from {args.url}...")
        download_file(args.url, output_path)
        success = True
    except Exception as e:
        log.warning(f"Direct download failed: {e}")

    # Strategy 2: Fallback to HF datasets library
    if not success:
        try:
            log.info("Attempting load via HuggingFace datasets library...")
            df = _load_via_hf_library()
            df = _validate_and_clean_df(df)
            df.to_parquet(output_path, index=False)
            success = True
        except Exception as e:
            log.error(f"All data loading attempts failed: {e}")
            return 1

    # Validation of the resulting file
    try:
        df = pd.read_parquet(output_path)
        df = _validate_and_clean_df(df)
    except Exception as e:
        log.error(f"Downloaded file is invalid: {e}")
        return 1

    row_count = len(df)
    if row_count < MIN_ROWS:
        log.error(
            f"Dataset contains only {row_count} rows (< {MIN_ROWS}); aborting."
        )
        return 1

    # Overwrite file with cleaned version to ensure schema consistency
    df.to_parquet(output_path, index=False)

    # Compute checksum of the final Parquet file.
    checksum = compute_sha256(output_path)
    checksums_path = paths.data("raw", "fluordb", CHECKSUMS_FILENAME)
    with open(checksums_path, "w") as f:
        f.write(f"{output_path.name} {checksum}\n")
    log.info(f"Wrote checksum to {checksums_path}")

    # Write a simple success log.
    write_log(f"SUCCESS: {row_count} molecules downloaded.")
    return 0


if __name__ == "__main__":
    sys.exit(main())