"""
Checksum generation and state file update for data integrity.

This module implements checksum generation for all files under data/
and updates the state file with artifact hashes per Constitution Principle III.
"""

import os
import sys
import hashlib
import csv
import yaml
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List, Optional

# Constants
DATA_DIR = Path("data")
STATE_DIR = Path("state/projects")
PROJECT_ID = "PROJ-141-evaluating-the-impact-of-code-generation"
CHECKSUMS_FILE = DATA_DIR / "checksums.csv"
STATE_FILE = STATE_DIR / f"{PROJECT_ID}.yaml"


def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file.

    Args:
        file_path: Path to the file

    Returns:
        Hexadecimal hash string
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error computing hash for {file_path}: {e}", file=sys.stderr)
        return None


def scan_data_directory(data_dir: Path = DATA_DIR) -> List[Dict[str, str]]:
    """
    Scan data directory and compute hashes for all files.

    Args:
        data_dir: Path to data directory

    Returns:
        List of dictionaries with file paths and hashes
    """
    checksums = []
    
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return checksums

    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            # Skip checksums.csv itself to avoid circular dependency
            if file_path.name == "checksums.csv":
                continue
            
            file_hash = compute_file_hash(file_path)
            if file_hash:
                relative_path = file_path.relative_to(data_dir)
                checksums.append({
                    "file_path": str(relative_path),
                    "hash": file_hash,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

    return checksums


def write_checksums_csv(checksums: List[Dict[str, str]], output_path: Path = CHECKSUMS_FILE) -> None:
    """
    Write checksums to CSV file.

    Args:
        checksums: List of checksum dictionaries
        output_path: Path to output CSV file
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["file_path", "hash", "timestamp"])
        writer.writeheader()
        writer.writerows(checksums)
    
    print(f"Checksums written to {output_path}")


def update_state_file(checksums: List[Dict[str, str]], state_path: Path = STATE_FILE) -> None:
    """
    Update state file with artifact hashes.

    Args:
        checksums: List of checksum dictionaries
        state_path: Path to state file
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Load existing state or create new
    state_data = {}
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load state file: {e}", file=sys.stderr)
            state_data = {}

    # Update artifact_hashes
    artifact_hashes = {}
    for entry in checksums:
        artifact_hashes[entry["file_path"]] = entry["hash"]

    state_data["artifact_hashes"] = artifact_hashes
    state_data["last_updated"] = datetime.now(timezone.utc).isoformat()
    state_data["checksum_version"] = "1.0"

    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)
    
    print(f"State file updated: {state_path}")


def main():
    """Main entry point for checksum generation."""
    print("Starting checksum generation...")
    
    # Scan data directory
    checksums = scan_data_directory()
    
    if not checksums:
        print("No files found to checksum or data directory does not exist.")
        # Create empty checksums file
        write_checksums_csv([])
        # Update state file with empty hashes
        update_state_file([])
        return

    print(f"Found {len(checksums)} files to checksum.")
    
    # Write checksums to CSV
    write_checksums_csv(checksums)
    
    # Update state file
    update_state_file(checksums)
    
    print("Checksum generation complete.")


if __name__ == "__main__":
    main()
