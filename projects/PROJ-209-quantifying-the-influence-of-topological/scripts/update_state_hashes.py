#!/usr/bin/env python3
"""
Update state file with SHA-256 checksums for raw/processed data and feature matrices.

This script computes SHA-256 hashes for all relevant data files in the project
(raw data, processed features/targets, and model artifacts) and records them
in a state file under state/projects/.

It also records the git hash of the current code version to ensure reproducibility.
"""

import os
import sys
import hashlib
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Project root is assumed to be the parent of the 'scripts' directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"
DATA_RAW_DIR = PROJECT_ROOT / "data" / "raw"
DATA_PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"
DATA_VALIDATION_DIR = PROJECT_ROOT / "data" / "validation"

# Ensure state directory exists
STATE_DIR.mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        return "FILE_NOT_FOUND"
    except Exception as e:
        return f"ERROR: {str(e)}"

def get_git_hash() -> Optional[str]:
    """Get the current git commit hash."""
    try:
        import subprocess
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=PROJECT_ROOT,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None

def find_data_files(directory: Path, extensions: List[str] = None) -> List[Path]:
    """Find all files with specified extensions in a directory (non-recursive)."""
    if not directory.exists():
        return []
    
    files = []
    for item in directory.iterdir():
        if item.is_file():
            if extensions is None or any(item.suffix == ext for ext in extensions):
                files.append(item)
    return sorted(files)

def collect_checksums() -> Dict[str, Any]:
    """Collect checksums for all relevant data files."""
    checksums = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "git_hash": get_git_hash(),
        "files": {}
    }

    # Process raw data files
    if DATA_RAW_DIR.exists():
        raw_files = find_data_files(DATA_RAW_DIR, [".csv", ".json", ".txt", ".parquet"])
        for file_path in raw_files:
            checksums["files"][f"raw/{file_path.name}"] = {
                "path": str(file_path.relative_to(PROJECT_ROOT)),
                "sha256": compute_sha256(file_path),
                "size_bytes": file_path.stat().st_size
            }

    # Process processed data files
    if DATA_PROCESSED_DIR.exists():
        processed_files = find_data_files(DATA_PROCESSED_DIR, [".csv", ".json", ".parquet"])
        for file_path in processed_files:
            checksums["files"][f"processed/{file_path.name}"] = {
                "path": str(file_path.relative_to(PROJECT_ROOT)),
                "sha256": compute_sha256(file_path),
                "size_bytes": file_path.stat().st_size
            }

    # Process validation data if exists
    if DATA_VALIDATION_DIR.exists():
        validation_files = find_data_files(DATA_VALIDATION_DIR, [".csv", ".json", ".parquet"])
        for file_path in validation_files:
            checksums["files"][f"validation/{file_path.name}"] = {
                "path": str(file_path.relative_to(PROJECT_ROOT)),
                "sha256": compute_sha256(file_path),
                "size_bytes": file_path.stat().st_size
            }

    return checksums

def save_state_file(checksums: Dict[str, Any], project_id: str = "PROJ-209-quantifying-the-influence-of-topological") -> Path:
    """Save checksums to the state file."""
    state_file_path = STATE_DIR / f"{project_id}.yaml"
    
    # Convert to YAML-like format (simple key-value)
    # Since we don't want to depend on PyYAML, we'll use a simple text format
    lines = [
        f"# State file for {project_id}",
        f"# Generated: {checksums['timestamp']}",
        f"# Git Hash: {checksums['git_hash'] or 'N/A'}",
        "",
        "metadata:",
        f"  timestamp: {checksums['timestamp']}",
        f"  git_hash: {checksums['git_hash'] or 'N/A'}",
        "",
        "files:"
    ]
    
    for file_key, file_info in checksums["files"].items():
        lines.append(f"  - key: {file_key}")
        lines.append(f"    path: {file_info['path']}")
        lines.append(f"    sha256: {file_info['sha256']}")
        lines.append(f"    size_bytes: {file_info['size_bytes']}")
        lines.append("")
    
    content = "\n".join(lines)
    
    with open(state_file_path, "w", encoding="utf-8") as f:
        f.write(content)
    
    return state_file_path

def main():
    """Main entry point."""
    print("Collecting checksums for data files...")
    checksums = collect_checksums()
    
    if not checksums["files"]:
        print("Warning: No data files found to checksum.")
        print("Ensure that data files exist in data/raw/, data/processed/, or data/validation/")
    
    project_id = "PROJ-209-quantifying-the-influence-of-topological"
    state_file_path = save_state_file(checksums, project_id)
    
    print(f"State file updated: {state_file_path}")
    print(f"Total files processed: {len(checksums['files'])}")
    
    # Print summary
    for file_key, file_info in checksums["files"].items():
        status = "OK" if file_info["sha256"] != "FILE_NOT_FOUND" and not file_info["sha256"].startswith("ERROR") else "FAILED"
        print(f"  [{status}] {file_key}: {file_info['sha256'][:16]}...")

if __name__ == "__main__":
    main()