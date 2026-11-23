"""
Script to generate provenance metadata for all files in the raw data directory.

This script scans `data/raw/` for data files (csv, json, parquet, etc.) and
generates corresponding `_meta.json` files using the `write_meta` function
from `utils.provenance`.
"""
import os
import sys
import glob
import argparse
from pathlib import Path
import json

# Add project root to path if running as script
if __name__ == "__main__":
    project_root = Path(__file__).resolve().parent.parent
    sys.path.insert(0, str(project_root))

from utils.provenance import generate_provenance_for_dataset, hash_file

def main():
    parser = argparse.ArgumentParser(
        description="Generate provenance metadata for raw data files."
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw",
        help="Path to the raw data directory."
    )
    parser.add_argument(
        "--source-id",
        type=str,
        default="verified_dataset",
        help="Source identifier to include in metadata."
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory {data_dir} does not exist.")
        sys.exit(1)

    # Supported extensions
    extensions = ["*.csv", "*.json", "*.parquet", "*.tsv", "*.npy"]
    files = []
    for ext in extensions:
        files.extend(data_dir.glob(ext))
    
    if not files:
        print(f"No data files found in {data_dir}.")
        sys.exit(0)

    print(f"Found {len(files)} data files. Generating provenance...")
    
    generated_count = 0
    for file_path in files:
        try:
            meta_path = generate_provenance_for_dataset(
                str(file_path), 
                args.source_id
            )
            print(f"  Generated: {meta_path}")
            generated_count += 1
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")
    
    print(f"Successfully generated {generated_count} provenance files.")

if __name__ == "__main__":
    main()
