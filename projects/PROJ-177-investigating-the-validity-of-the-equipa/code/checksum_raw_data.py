"""
Checksum Raw Data Module.

Generates SHA-256 hashes for files in the `data/raw/` directory
and writes them to a local log file.
"""

import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.

    Args:
        file_path: Path to the file to hash.

    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Failed to read file {file_path} for hashing: {e}")


def get_raw_data_files(raw_dir: Path) -> list[Path]:
    """
    Recursively retrieve all files in the raw data directory.

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        List of Path objects for files found.
    """
    if not raw_dir.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(raw_dir):
        for filename in filenames:
            files.append(Path(root) / filename)
    return sorted(files)


def generate_checksums(raw_dir: Path) -> dict[str, str]:
    """
    Generate checksums for all files in the raw data directory.

    Args:
        raw_dir: Path to the raw data directory.

    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes.
    """
    checksums = {}
    files = get_raw_data_files(raw_dir)
    
    for file_path in files:
        try:
            rel_path = str(file_path.relative_to(raw_dir))
            checksums[rel_path] = calculate_sha256(file_path)
        except ValueError:
            # Should not happen if relative_to works, but safe fallback
            pass
    
    return checksums


def write_checksum_log(checksums: dict[str, str], log_path: Path) -> None:
    """
    Write checksums to a log file.

    Args:
        checksums: Dictionary of file paths to hashes.
        log_path: Path to the output log file.
    """
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(log_path, "w") as f:
        f.write(f"# Raw Data Checksum Log\n")
        f.write(f"# Generated: {datetime.utcnow().isoformat()}Z\n")
        f.write(f"# Format: <relative_path> <sha256_hash>\n\n")
        
        for rel_path, hash_val in sorted(checksums.items()):
            f.write(f"{rel_path} {hash_val}\n")


def main() -> int:
    """
    Main entry point for the checksum_raw_data script.

    Generates checksums for `data/raw/` and writes to `data/checksums.log`.
    """
    project_root = Path.cwd()
    raw_dir = project_root / "data" / "raw"
    log_file = project_root / "data" / "checksums.log"

    if not raw_dir.exists():
        print(f"Warning: Raw data directory '{raw_dir}' does not exist.")
        # Create empty log to indicate directory was checked
        write_checksum_log({}, log_file)
        print(f"Created empty checksum log: {log_file}")
        return 0

    try:
        checksums = generate_checksums(raw_dir)
        print(f"Generated checksums for {len(checksums)} files.")
    except Exception as e:
        print(f"Error generating checksums: {e}", file=sys.stderr)
        return 1

    try:
        write_checksum_log(checksums, log_file)
        print(f"Checksum log written to: {log_file}")
    except Exception as e:
        print(f"Error writing checksum log: {e}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
