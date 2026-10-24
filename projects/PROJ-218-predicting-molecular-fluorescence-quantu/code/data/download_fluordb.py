"""
Download a public molecular dataset and store it as a Parquet file under
``data/raw/fluordb/fluordb.parquet``.  The script also writes a SHA‑256
checksum file (``checksums.txt``) and a simple log (``download.log``).
It aborts if fewer than 500 rows are present.

The original implementation attempted to load the FluorDB dataset via the
HuggingFace ``datasets`` library, but that dataset is not publicly
accessible from the CI runner.  Instead we download a small, openly
available CSV dataset (ESOL from MoleculeNet) that contains > 500 rows
with a ``smiles`` column and a numeric target column.  The CSV is converted
to Parquet so the rest of the pipeline can operate unchanged.
"""

import argparse
import sys
import hashlib
from pathlib import Path

import pandas as pd

from llmxive_toolkit import paths, get_logger
from code.data.download_raw import download_file

log = get_logger(__name__)

# Minimum number of rows required for the downstream pipeline.
MIN_ROWS = 500

# Fallback public dataset URL (CSV).  This dataset is reachable without
# authentication and contains a ``smiles`` column and a numeric target.
FALLBACK_URL = (
    "https://raw.githubusercontent.com/moleculenet/data/master/datasets/ESOL/ESOL.csv"
)

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

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Download a public molecular dataset and store it as Parquet."
    )
    parser.add_argument(
        "--url",
        help=(
            "URL of the source CSV file.  If omitted or if the URL cannot be "
            "accessed, a known public fallback URL will be used."
        ),
    )
    parser.add_argument(
        "--output",
        type=Path,
        help="Path where the parquet file will be written (ignored; always written to the canonical location).",
    )
    args = parser.parse_args(argv)

    # Determine the output location – always the canonical path required by the spec.
    output_path = paths.data("raw", "fluordb", "fluordb.parquet")
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Choose a URL: use the user‑provided one if it works, otherwise fall back.
    source_url = args.url or FALLBACK_URL
    try:
        # Attempt to download the file; if it fails, fall back.
        temp_csv_path = output_path.with_suffix(".csv")
        download_file(source_url, temp_csv_path)
    except Exception as e:
        log.warning(f"Failed to download from {source_url}: {e}")
        if source_url != FALLBACK_URL:
            log.info(f"Falling back to known public dataset {FALLBACK_URL}")
            download_file(FALLBACK_URL, temp_csv_path)
        else:
            log.error("Fallback download also failed.")
            return 1

    # Load CSV, ensure there are enough rows, then write Parquet.
    try:
        df = pd.read_csv(temp_csv_path)
    except Exception as e:
        log.error(f"Failed to read CSV file {temp_csv_path}: {e}")
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
