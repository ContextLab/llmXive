"""
Script to generate provenance metadata for datasets in data/raw/.

This script verifies that real data files exist in data/raw/ and generates
corresponding _meta.json files with hash, timestamp, and source keys.
"""
import os
import sys
import glob
import argparse
from pathlib import Path
import json

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.provenance import write_meta, hash_file

def main():
    parser = argparse.ArgumentParser(
        description="Generate provenance metadata for datasets in data/raw/"
    )
    parser.add_argument(
        "--source",
        type=str,
        default="verified_dataset",
        help="Source identifier for the metadata"
    )
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw",
        help="Directory containing dataset files"
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"ERROR: Data directory not found: {data_dir}")
        sys.exit(1)

    # Find all non-meta files in the data directory
    # Exclude .json files (metadata files) and common non-data extensions
    extensions_to_process = {".csv", ".tsv", ".edf", ".asc", ".txt"}
    files_processed = 0
    
    for file_path in data_dir.iterdir():
        if file_path.is_file() and file_path.suffix.lower() in extensions_to_process:
            # Skip if it's already a meta file
            if file_path.name.endswith("_meta.json"):
                continue
            
            print(f"Processing: {file_path.name}")
            
            # Create metadata dictionary
            meta_dict = {
                "dataset_id": file_path.name,
                "file_size_bytes": file_path.stat().st_size
            }
            
            # Generate metadata file
            try:
                write_meta(str(file_path), meta_dict, source=args.source)
                meta_file = str(file_path).replace(file_path.suffix, "") + "_meta.json"
                print(f"  -> Generated: {os.path.basename(meta_file)}")
                files_processed += 1
            except Exception as e:
                print(f"  -> ERROR: {e}")
    
    print(f"\nCompleted: {files_processed} provenance files generated.")
    
    if files_processed == 0:
        print("WARNING: No data files found to process.")
        print("Ensure real data files exist in data/raw/ (e.g., .csv, .tsv, .edf)")
        sys.exit(1)

if __name__ == "__main__":
    main()
