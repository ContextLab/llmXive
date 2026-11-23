"""
Wrapper script to reconcile the run-book with the implementation.
Invokes the QM9 download logic defined in data/download_qm9.py.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure code directory is in path for imports
code_dir = Path(__file__).parent
if str(code_dir) not in sys.path:
    sys.path.insert(0, str(code_dir))

from data.download_qm9 import download_qm9, calculate_sha256


def parse_args():
    parser = argparse.ArgumentParser(description="Download QM9 dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default="data/raw",
        help="Directory to save the downloaded data",
    )
    parser.add_argument(
        "--doi",
        type=str,
        default="10.1038/sdata.2014.22",
        help="DOI reference for the dataset",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    output_path = Path(args.output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    print(f"Downloading QM9 dataset (DOI: {args.doi}) to {output_path}...")
    success, file_path = download_qm9(output_dir=str(output_path))

    if not success:
        print("ERROR: Failed to download dataset. Exiting.")
        sys.exit(1)

    if file_path:
        sha = calculate_sha256(file_path)
        print(f"Download successful: {file_path}")
        print(f"SHA-256: {sha}")
    else:
        print("ERROR: Download reported success but no file path returned.")
        sys.exit(1)


if __name__ == "__main__":
    main()