"""
Download FluorDB v1.0 dataset using the HuggingFace `datasets` library,
write it as a parquet file to ``data/raw/fluordb/fluordb.parquet``,
compute and record its SHA‑256 checksum, and emit a simple log file.
The script aborts if fewer than 500 valid rows are present.
"""

import argparse
import sys
import hashlib
from pathlib import Path

from datasets import load_dataset
from llmxive_toolkit import paths, get_logger

log = get_logger(__name__)

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
    log_path = paths.data("raw", "fluordb", LOG_FILENAME)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w") as f:
        f.write(message + "\n")
    log.info(f"Wrote log to {log_path}")

def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Download FluorDB v1.0 and verify its integrity."
    )
    # The URL argument is kept for backward compatibility but is ignored;
    # the dataset is fetched via the HuggingFace `datasets` library.
    parser.add_argument(
        "--url",
        help="(ignored) URL of the dataset – the script uses the HF identifier.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=paths.data("raw", "fluordb", "fluordb.parquet"),
        help="Path where the parquet file will be written.",
    )
    args = parser.parse_args(argv)

    # Load the dataset via the official HF identifier.
    try:
        ds = load_dataset("fluordb/v1", split="train", streaming=False)
    except Exception as e:
        log.error(f"Failed to load FluorDB via datasets: {e}")
        return 1

    # Ensure output directory exists.
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Write parquet file.
    try:
        ds.to_parquet(str(args.output))
    except Exception as e:
        log.error(f"Failed to write parquet file: {e}")
        return 1

    # Verify row count.
    row_count = ds.num_rows if hasattr(ds, "num_rows") else len(ds)
    if row_count < MIN_ROWS:
        log.error(
            f"Dataset contains only {row_count} rows (< {MIN_ROWS}); aborting."
        )
        return 1

    # Compute checksum and write checksums file.
    checksum = compute_sha256(args.output)
    checksums_path = paths.data("raw", "fluordb", CHECKSUMS_FILENAME)
    with open(checksums_path, "w") as f:
        f.write(f"{args.output.name} {checksum}\n")
    log.info(f"Wrote checksum to {checksums_path}")

    # Write success log.
    write_log(f"SUCCESS: {row_count} molecules downloaded.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
