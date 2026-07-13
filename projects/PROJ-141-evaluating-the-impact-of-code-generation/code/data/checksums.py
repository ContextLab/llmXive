"""
Checksum generation and state file update for data integrity.
Implements Constitution Principle III: Write data checksums to data/checksums.csv
AND state file artifact_hashes map.
"""
import os
import sys
import hashlib
import csv
import yaml
import time
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Project root relative to this file
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
STATE_DIR = PROJECT_ROOT / "state" / "projects"
STATE_FILE = STATE_DIR / "PROJ-141-evaluating-the-impact-of-code-generation.yaml"
CHECKSUMS_CSV = DATA_DIR / "checksums.csv"


def compute_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """Compute SHA-256 hash of a file."""
    hasher = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                hasher.update(chunk)
        return hasher.hexdigest()
    except FileNotFoundError:
        return None
    except Exception as e:
        print(f"Error hashing {file_path}: {e}", file=sys.stderr)
        return None


def scan_data_directory(data_dir: Path) -> List[Dict[str, Any]]:
    """Scan data directory for all files and compute their checksums."""
    results = []
    if not data_dir.exists():
        print(f"Data directory not found: {data_dir}", file=sys.stderr)
        return results

    for file_path in data_dir.rglob("*"):
        if file_path.is_file():
            # Skip the checksums file itself to avoid circular dependency
            if file_path == CHECKSUMS_CSV:
                continue

            relative_path = file_path.relative_to(data_dir)
            file_hash = compute_file_hash(file_path)

            if file_hash:
                results.append({
                    "file_path": str(relative_path),
                    "algorithm": "sha256",
                    "hash": file_hash,
                    "size_bytes": file_path.stat().st_size,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })

    return results


def write_checksums_csv(checksums: List[Dict[str, Any]], output_path: Path) -> None:
    """Write checksums to CSV file."""
    if not checksums:
        print("No checksums to write.", file=sys.stderr)
        # Write header-only file if no data
        with open(output_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=["file_path", "algorithm", "hash", "size_bytes", "timestamp"])
            writer.writeheader()
        return

    with open(output_path, "w", newline="") as f:
        fieldnames = ["file_path", "algorithm", "hash", "size_bytes", "timestamp"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for row in checksums:
            writer.writerow(row)


def update_state_file(checksums: List[Dict[str, Any]], state_path: Path) -> None:
    """Update the project state file with artifact_hashes map."""
    # Ensure state directory exists
    state_path.parent.mkdir(parents=True, exist_ok=True)

    # Load existing state or create new
    state_data = {}
    if state_path.exists():
        try:
            with open(state_path, "r") as f:
                state_data = yaml.safe_load(f) or {}
        except Exception as e:
            print(f"Warning: Could not load existing state file: {e}", file=sys.stderr)

    # Build artifact_hashes map
    artifact_hashes = {}
    for checksum in checksums:
        artifact_hashes[checksum["file_path"]] = checksum["hash"]

    # Update state data
    state_data["artifact_hashes"] = artifact_hashes
    state_data["last_checksum_update"] = datetime.now(timezone.utc).isoformat()

    # Ensure updated_at is present (per T055a compliance)
    if "updated_at" not in state_data:
        state_data["updated_at"] = datetime.now(timezone.utc).isoformat()
    else:
        state_data["updated_at"] = datetime.now(timezone.utc).isoformat()

    # Write updated state
    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)


def main():
    """Main entry point for checksum generation and state update."""
    print(f"Scanning data directory: {DATA_DIR}")
    checksums = scan_data_directory(DATA_DIR)

    if not checksums:
        print("No files found to checksum (excluding checksums.csv itself).")
        # Still write empty CSV and update state with empty map
        write_checksums_csv([], CHECKSUMS_CSV)
        update_state_file([], STATE_FILE)
        print(f"Updated state file: {STATE_FILE}")
        return

    print(f"Computed {len(checksums)} checksums.")
    write_checksums_csv(checksums, CHECKSUMS_CSV)
    print(f"Wrote checksums to: {CHECKSUMS_CSV}")

    update_state_file(checksums, STATE_FILE)
    print(f"Updated state file: {STATE_FILE}")

    # Print summary
    print("\nChecksum Summary:")
    for cs in checksums:
        print(f"  {cs['file_path']}: {cs['hash'][:16]}...")


if __name__ == "__main__":
    main()
