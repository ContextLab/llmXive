"""
Download the raw SMILES parquet file.

This script streams the file from the provided URL, writes it to the
destination path, and verifies its SHA‑256 checksum against the value
recorded in ``data/raw/checksums.txt``.  On success it exits with status 0;
on mismatch it raises a ``ValueError`` causing a non‑zero exit code.
"""

import argparse
import sys
from pathlib import Path

from code.data.download_raw import download_file, read_checksums, verify_checksums

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Download SMILES parquet")
    parser.add_argument(
        "--url",
        required=True,
        help="URL of the SMILES parquet file to download",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination path under the project (e.g., data/raw/smiles.parquet)",
    )
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = _parse_args(argv)

    # Ensure the parent directory exists (paths helper creates it)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Perform the download and compute its SHA‑256 digest
    try:
        computed_digest = download_file(args.url, args.output)
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return 1

    # Load the expected checksums from the canonical file
    expected = read_checksums()
    filename = args.output.name
    if filename not in expected:
        print(
            f"Checksum for '{filename}' not found in data/raw/checksums.txt",
            file=sys.stderr,
        )
        return 1

    # Verify the computed digest against the expected value
    try:
        verify_checksums({filename: computed_digest})
    except ValueError as ve:
        print(f"Checksum mismatch: {ve}", file=sys.stderr)
        return 1

    print(f"Successfully downloaded and verified '{filename}'.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
