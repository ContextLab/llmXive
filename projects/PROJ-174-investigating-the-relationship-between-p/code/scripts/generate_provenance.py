"""
Script to generate provenance metadata for all raw data files.

This script scans `data/raw/` for data files (csv, json, tsv) and
generates corresponding `_meta.json` files using `utils.provenance`.
"""
import os
import sys
import glob
import argparse
from pathlib import Path
import json

# Add project root to path to import utils
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.provenance import generate_provenance_for_dataset, write_meta

def main():
    parser = argparse.ArgumentParser(description="Generate provenance metadata for raw data.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw data files."
    )
    parser.add_argument(
        "--source-id",
        type=str,
        default="openneuro_verified",
        help="Source identifier to embed in metadata."
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"Error: Data directory '{data_dir}' does not exist.")
        sys.exit(1)

    # Find all data files (csv, tsv, json, parquet)
    extensions = ["*.csv", "*.tsv", "*.json", "*.parquet"]
    files = []
    for ext in extensions:
        files.extend(data_dir.glob(ext))
    
    if not files:
        print(f"No data files found in {data_dir}. Skipping provenance generation.")
        return

    print(f"Found {len(files)} data files.")
    processed_count = 0

    for file_path in files:
        # Skip if already has a meta file (optional, but good practice)
        meta_path = str(file_path).rsplit(".", 1)[0] + "_meta.json"
        if os.path.exists(meta_path):
            print(f"Skipping {file_path.name} (meta already exists).")
            continue

        try:
            result_path = generate_provenance_for_dataset(str(file_path), args.source_id)
            print(f"Generated: {result_path}")
            processed_count += 1
        except FileNotFoundError as e:
            print(f"Error processing {file_path}: {e}")
        except Exception as e:
            print(f"Unexpected error processing {file_path}: {e}")

    print(f"Provenance generation complete. Processed {processed_count} files.")

if __name__ == "__main__":
    main()
