"""
Verification script for T007.
Ensures that raw data files have corresponding meta files with correct keys.
"""
import os
import sys
import json
import glob
from pathlib import Path
import argparse

def main():
    parser = argparse.ArgumentParser(description="Verify provenance metadata for raw data.")
    parser.add_argument(
        "--data-dir",
        type=str,
        default="data/raw",
        help="Directory containing raw data files."
    )
    args = parser.parse_args()

    data_dir = Path(args.data_dir)
    if not data_dir.exists():
        print(f"FAIL: Data directory '{data_dir}' does not exist.")
        return 1

    # Find all meta files
    meta_files = list(data_dir.glob("*_meta.json"))
    
    if not meta_files:
        print("FAIL: No _meta.json files found in data/raw.")
        return 1

    required_keys = {"hash", "timestamp", "source"}
    all_valid = True

    for meta_file in meta_files:
        try:
            with open(meta_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            
            missing_keys = required_keys - set(data.keys())
            if missing_keys:
                print(f"FAIL: {meta_file.name} missing keys: {missing_keys}")
                all_valid = False
            else:
                print(f"PASS: {meta_file.name} has all required keys.")
        except json.JSONDecodeError:
            print(f"FAIL: {meta_file.name} is not valid JSON.")
            all_valid = False
        except Exception as e:
            print(f"FAIL: Error reading {meta_file.name}: {e}")
            all_valid = False

    if all_valid:
        print("\nVERIFICATION PASSED: All meta files contain required keys.")
        return 0
    else:
        print("\nVERIFICATION FAILED: Some meta files are invalid.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
