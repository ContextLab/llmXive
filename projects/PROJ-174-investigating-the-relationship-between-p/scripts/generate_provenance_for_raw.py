"""
Script to generate metadata JSON files for all raw data files.

This script scans the data/raw directory for data files (csv, txt, json)
and generates corresponding *_meta.json files using the provenance utilities.

Usage:
    python scripts/generate_provenance_for_raw.py
"""
import os
import glob
import sys

# Add project root to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "code"))

from utils.provenance import write_meta

def main():
    raw_dir = os.path.join(os.path.dirname(__file__), "..", "data", "raw")
    
    if not os.path.isdir(raw_dir):
        print(f"Error: Directory not found: {raw_dir}")
        sys.exit(1)

    # Find data files (csv, txt, json)
    patterns = ["*.csv", "*.txt", "*.json", "*.tsv"]
    data_files = []
    for pattern in patterns:
        data_files.extend(glob.glob(os.path.join(raw_dir, pattern)))

    if not data_files:
        print(f"No data files found in {raw_dir}. Skipping metadata generation.")
        return

    print(f"Found {len(data_files)} data files. Generating metadata...")

    generated_count = 0
    for file_path in data_files:
        filename = os.path.basename(file_path)
        # Extract source identifier from filename (e.g., ds004287 from ds004287.csv)
        source_id = os.path.splitext(filename)[0]
        
        try:
            write_meta(file_path, {}, source=source_id)
            print(f"  Generated: {file_path.replace('.csv', '_meta.json')}")
            generated_count += 1
        except Exception as e:
            print(f"  Error processing {file_path}: {e}")

    print(f"Completed. Generated {generated_count} metadata files.")

if __name__ == "__main__":
    main()