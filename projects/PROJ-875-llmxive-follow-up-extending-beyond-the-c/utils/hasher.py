"""
utils/hasher.py

Implements Constitution Principle V: Artifact Versioning.
Generates deterministic version hashes (SHA-256) for all artifacts in the project's
data, code, and results directories to ensure reproducibility and integrity tracking.

Usage:
    python utils/hasher.py
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List

# Project root relative to this file (utils/hasher.py is in 'utils/')
PROJECT_ROOT = Path(__file__).parent.parent
ARTIFACT_DIRS = [
    "data/processed",
    "data/raw",
    "code",
    "results",
    "config",
    "specs/contracts"
]
OUTPUT_FILE = PROJECT_ROOT / "results" / "artifact_hashes.json"

# Extensions to include (exclude pycache, logs, etc.)
INCLUDE_EXTENSIONS = {".py", ".yaml", ".yml", ".json", ".txt", ".csv", ".md", ".png", ".jpg", ".txt"}
EXCLUDE_DIRS = {"__pycache__", ".git", "venv", ".venv", "node_modules", ".pytest_cache"}

def compute_file_hash(file_path: Path) -> str:
    """
    Computes the SHA-256 hash of a file by reading it in chunks.
    Returns a hex string.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError) as e:
        raise RuntimeError(f"Failed to read file {file_path}: {e}")

def collect_artifacts(base_dir: Path) -> List[Path]:
    """
    Recursively collects all relevant artifact files in a directory.
    Skips excluded directories and non-matching extensions.
    """
    artifacts = []
    if not base_dir.exists():
        return artifacts

    for root, dirs, files in os.walk(base_dir):
        # Modify dirs in-place to skip excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix in INCLUDE_EXTENSIONS:
                artifacts.append(file_path)

    return artifacts

def generate_version_manifest() -> Dict[str, Any]:
    """
    Generates a manifest containing hashes for all tracked artifacts.
    """
    manifest = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "project_root": str(PROJECT_ROOT),
        "hash_algorithm": "sha256",
        "artifacts": {}
    }

    total_files = 0
    for dir_name in ARTIFACT_DIRS:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            print(f"Warning: Directory {dir_path} does not exist. Skipping.")
            continue

        files = collect_artifacts(dir_path)
        for file_path in files:
            relative_path = file_path.relative_to(PROJECT_ROOT)
            try:
                file_hash = compute_file_hash(file_path)
                manifest["artifacts"][str(relative_path)] = file_hash
                total_files += 1
            except RuntimeError as e:
                print(f"Error hashing {file_path}: {e}", file=sys.stderr)

    manifest["summary"] = {
        "total_files_hashed": total_files,
        "directories_scanned": ARTIFACT_DIRS
    }

    return manifest

def main():
    """
    Entry point for the hasher utility.
    Ensures the results directory exists, generates the manifest,
    and writes it to artifact_hashes.json.
    """
    # Ensure output directory exists
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

    print(f"Starting artifact hashing for project: {PROJECT_ROOT}")
    print(f"Scanning directories: {ARTIFACT_DIRS}")

    try:
        manifest = generate_version_manifest()
        
        # Write manifest to file
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, sort_keys=True)

        print(f"Successfully hashed {manifest['summary']['total_files_hashed']} artifacts.")
        print(f"Manifest written to: {OUTPUT_FILE}")
        
        return 0
    except Exception as e:
        print(f"Fatal error during hashing: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())