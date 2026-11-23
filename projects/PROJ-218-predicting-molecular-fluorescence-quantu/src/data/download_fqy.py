"""
Download the raw Fluorescence Quantum Yield (FQY) JSON file.

Mirrors the behaviour of ``download_smiles.py``: streams the file,
writes it to the requested location, and validates its SHA‑256 checksum
against the entry in ``data/raw/checksums.txt``.
"""

import argparse
import sys
from pathlib import Path

from code.data.download_raw import download_file, read_checksums, verify_checksums

def _parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Download FQY JSON")
    parser.add_argument(
        "--url",
        required=True,
        help="URL of the FQY JSON file to download",
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Destination path under the project (e.g., data/raw/fqy.json)",
    )
    return parser.parse_args(argv)

def main(argv=None) -> int:
    args = _parse_args(argv)

    # Ensure destination directory exists
    args.output.parent.mkdir(parents=True, exist_ok=True)

    # Download and compute checksum
    try:
        computed_digest = download_file(args.url, args.output)
    except Exception as e:
        print(f"Download failed: {e}", file=sys.stderr)
        return 1

    # Load expected checksums
    expected = read_checksums()
    filename = args.output.name
    if filename not in expected:
        print(
            f"Checksum for '{filename}' not found in data/raw/checksums.txt",
            file=sys.stderr,
        )
        return 1

    # Verify checksum
    try:
        verify_checksums({filename: computed_digest})
    except ValueError as ve:
        print(f"Checksum mismatch: {ve}", file=sys.stderr)
        return 1

    print(f"Successfully downloaded and verified '{filename}'.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
