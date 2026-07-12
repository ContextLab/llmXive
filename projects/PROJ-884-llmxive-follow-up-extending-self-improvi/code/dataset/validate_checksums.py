import json
import hashlib
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import existing types from generator
from code.dataset.generator import PuzzleInstance

# Constants
RAW_DATA_DIR = Path("data/raw")
CHECKSUM_FILE = RAW_DATA_DIR / "checksums.json"
MANIFEST_FILE = RAW_DATA_DIR / "manifest.json"

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes SHA-256 checksum of a file.
    Reads in chunks to handle large files efficiently.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except Exception as e:
        raise RuntimeError(f"Failed to compute checksum for {file_path}: {e}")

def generate_checksums_for_directory(directory: Path) -> Dict[str, str]:
    """
    Iterates over all JSON files in the directory and generates checksums.
    Returns a dict mapping relative filename to checksum.
    """
    checksums = {}
    if not directory.exists():
        raise FileNotFoundError(f"Data directory not found: {directory}")

    json_files = list(directory.glob("*.json"))
    if not json_files:
        print(f"Warning: No JSON files found in {directory}")

    for file_path in json_files:
        if file_path.name in ["checksums.json", "manifest.json"]:
            continue  # Skip metadata files themselves
        checksums[file_path.name] = compute_file_checksum(file_path)

    return checksums

def save_checksums(checksums: Dict[str, str], output_path: Path) -> None:
    """
    Saves the checksums dictionary to a JSON file.
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(checksums, f, indent=2)
    print(f"Checksums saved to {output_path}")

def load_checksums(checksum_path: Path) -> Dict[str, str]:
    """
    Loads existing checksums from a JSON file.
    """
    if not checksum_path.exists():
        return {}
    with open(checksum_path, "r", encoding="utf-8") as f:
        return json.load(f)

def validate_data_integrity(directory: Path, checksum_file: Path) -> bool:
    """
    Validates all JSON files in the directory against stored checksums.
    Returns True if all match, False otherwise.
    """
    if not checksum_file.exists():
        print(f"Error: Checksum file not found at {checksum_file}")
        print("Run this script first to generate checksums.")
        return False

    stored_checksums = load_checksums(checksum_file)
    current_checksums = generate_checksums_for_directory(directory)

    if not stored_checksums:
        print("Warning: Stored checksums file is empty.")
        return False

    all_valid = True
    errors = []

    # Check for missing files
    for filename in stored_checksums:
        if filename not in current_checksums:
            errors.append(f"Missing file: {filename}")
            all_valid = False

    # Check for new files not in manifest
    for filename in current_checksums:
        if filename not in stored_checksums:
            errors.append(f"New file detected (not in manifest): {filename}")
            # Depending on strictness, this might be a warning or error.
            # For data integrity, we flag it.
            all_valid = False

    # Check content integrity
    for filename, stored_hash in stored_checksums.items():
        if filename in current_checksums:
            current_hash = current_checksums[filename]
            if stored_hash != current_hash:
                errors.append(f"Checksum mismatch for {filename}")
                errors.append(f"  Expected: {stored_hash}")
                errors.append(f"  Found:    {current_hash}")
                all_valid = False

    if errors:
        print("\nData Integrity Validation FAILED:")
        for err in errors:
            print(f"  - {err}")
        return False
    else:
        print("Data Integrity Validation PASSED: All files match stored checksums.")
        return True

def update_manifest(directory: Path, manifest_path: Path) -> None:
    """
    Creates or updates a manifest file listing all valid data files.
    """
    json_files = [f.name for f in directory.glob("*.json") 
                  if f.name not in ["checksums.json", "manifest.json"]]
    
    manifest_data = {
        "generated_at": "current_timestamp", # In real impl, use datetime
        "file_count": len(json_files),
        "files": json_files
    }
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2)
    print(f"Manifest updated at {manifest_path}")

def main():
    """
    Entry point for checksum validation.
    Usage:
      - First run: Generates checksums for all files in data/raw/
      - Subsequent runs: Validates files against stored checksums.
    """
    import argparse
    parser = argparse.ArgumentParser(description="Validate or generate checksums for dataset integrity.")
    parser.add_argument("--generate", action="store_true", help="Force regeneration of checksums.")
    parser.add_argument("--validate", action="store_true", help="Force validation against existing checksums.")
    args = parser.parse_args()

    # Determine mode
    should_generate = args.generate
    should_validate = args.validate or not args.generate

    if not should_generate and not should_validate:
        # Default behavior: if checksums exist, validate; otherwise generate
        if CHECKSUM_FILE.exists():
            should_validate = True
        else:
            should_generate = True

    if should_generate:
        print(f"Generating checksums for all files in {RAW_DATA_DIR}...")
        try:
            checksums = generate_checksums_for_directory(RAW_DATA_DIR)
            if checksums:
                save_checksums(checksums, CHECKSUM_FILE)
                update_manifest(RAW_DATA_DIR, MANIFEST_FILE)
                print("Generation complete.")
            else:
                print("No data files found to checksum.")
        except Exception as e:
            print(f"Error generating checksums: {e}")
            sys.exit(1)

    if should_validate:
        print(f"Validating data integrity in {RAW_DATA_DIR}...")
        is_valid = validate_data_integrity(RAW_DATA_DIR, CHECKSUM_FILE)
        sys.exit(0 if is_valid else 1)

if __name__ == "__main__":
    main()
