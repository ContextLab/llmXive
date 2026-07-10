"""
Generate SHA-256 checksums for all files in data/raw/ and write to a local log file.

This implements Constitution Principle III: Raw data integrity verification.
The output is a local log file, NOT the shared state YAML.
"""
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime

# Constants
RAW_DATA_DIR = Path("data/raw")
CHECKSUM_LOG_FILE = Path("data/raw_checksums.log")
CHUNK_SIZE = 8192  # 8KB chunks for reading large files


def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(CHUNK_SIZE), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def get_raw_data_files() -> list[Path]:
    """Get all files in the raw data directory recursively."""
    if not RAW_DATA_DIR.exists():
        print(f"Warning: Raw data directory '{RAW_DATA_DIR}' does not exist.", file=sys.stderr)
        return []
    
    files = []
    for root, _, filenames in os.walk(RAW_DATA_DIR):
        for filename in filenames:
            # Skip hidden files and common temporary files
            if filename.startswith('.') or filename.endswith(('.tmp', '.part', '.lock')):
                continue
            files.append(Path(root) / filename)
    
    return sorted(files)


def generate_checksums() -> dict[str, str]:
    """Generate checksums for all raw data files."""
    files = get_raw_data_files()
    checksums = {}
    
    for file_path in files:
        try:
            checksum = calculate_sha256(file_path)
            relative_path = file_path.relative_to(Path.cwd())
            checksums[str(relative_path)] = checksum
            print(f"  {relative_path}: {checksum}")
        except Exception as e:
            print(f"Error processing {file_path}: {e}", file=sys.stderr)
    
    return checksums


def write_checksum_log(checksums: dict[str, str]) -> None:
    """Write checksums to a local log file."""
    timestamp = datetime.now().isoformat()
    
    with open(CHECKSUM_LOG_FILE, "w") as f:
        f.write(f"# Raw Data Checksum Log\n")
        f.write(f"# Generated: {timestamp}\n")
        f.write(f"# Directory: {RAW_DATA_DIR}\n")
        f.write(f"# Format: <sha256_hash>  <relative_path>\n")
        f.write("#\n")
        
        if not checksums:
            f.write("# No files found in raw data directory.\n")
        else:
            for path, checksum in sorted(checksums.items()):
                f.write(f"{checksum}  {path}\n")
    
    print(f"\nChecksum log written to: {CHECKSUM_LOG_FILE}")


def main():
    """Main entry point."""
    print(f"Scanning raw data directory: {RAW_DATA_DIR}")
    files = get_raw_data_files()
    
    if not files:
        print("No files found to checksum.")
        write_checksum_log({})
        return
    
    print(f"Found {len(files)} file(s). Generating checksums...")
    checksums = generate_checksums()
    write_checksum_log(checksums)
    
    print(f"Completed. Processed {len(checksums)} file(s).")


if __name__ == "__main__":
    main()