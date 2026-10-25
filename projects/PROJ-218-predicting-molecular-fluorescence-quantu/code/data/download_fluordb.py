"""
Download the FluorDB v1.0 dataset (or a verified fallback) and store it as a Parquet
file under ``data/raw/fluordb/fluordb.parquet``. The script also writes a SHA‑256
checksum file (``checksums.txt``) and a simple log (``download.log``). It aborts if
fewer than 500 rows are present.

The implementation uses the HuggingFace ``datasets`` library to fetch the
joint SMILES + FQY parquet file directly from the ``fluordb/v1`` repository.
This avoids heavyweight optional dependencies such as ``deepchem`` and ensures
deterministic behaviour on the CI runner.
"""

import argparse
import sys
import hashlib
from pathlib import Path

import pandas as pd
from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

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


def _load_fluordb_via_hf() -> pd.DataFrame:
    """
    Load the FluorDB v1.0 dataset using the ``datasets`` library.
    The HF dataset contains a ``smiles`` column and a target column.
    The target column may be named ``fqy`` or already ``fqy_raw``.
    """
    try:
        # The dataset is small enough to load without streaming.
        ds = load_dataset("fluordb/v1", split="train", streaming=False)
    except Exception as e:
        log.error(f"Failed to load FluorDB from HuggingFace: {e}")
        raise

    # Convert to pandas for easier manipulation.
    df = ds.to_pandas()

    # Ensure required column names.
    if "smiles" not in df.columns:
        raise RuntimeError("FluorDB dataset does not contain a 'smiles' column.")
    # Target column may be named 'fqy' or already 'fqy_raw'.
    if "fqy_raw" not in df.columns:
        if "fqy" in df.columns:
            df = df.rename(columns={"fqy": "fqy_raw"})
        else:
            # If no recognised target column, raise.
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
        help=(
            "URL of the source file (unused). The script always downloads "
            "the verified FluorDB v1.0 dataset via HuggingFace."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Path where the parquet file will be written (unused). The file is "
            "always written to ``data/raw/fluordb/fluordb.parquet`` as required by the spec."
        ),
    )
    args = parser.parse_args(argv)

    # Canonical output location.
    output_path = paths.data("raw", "fluordb", "fluordb.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        df = _load_fluordb_via_hf()
    except Exception as e:
        log.error(f"Data loading error: {e}")
        return 1

    row_count = len(df)
    if row_count < MIN_ROWS:
        log.error(
            f"Dataset contains only {row_count} rows (< {MIN_ROWS}); aborting."
        )
        return 1

    try:
        df.to_parquet(output_path, index=False)
    except Exception as e:
        log.error(f"Failed to write Parquet file {output_path}: {e}")
        return 1

    # Compute checksum of the Parquet file.
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
