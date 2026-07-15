"""
Artifact Hashing Utility for llmXive.

This module computes cryptographic hashes (SHA-256) for all artifacts
generated during the research pipeline to ensure reproducibility and
integrity verification.

It scans the `data/`, `data/models/`, `data/results/`, and `code/` directories
(excluding __pycache__ and .pyc files), computes hashes, and writes a
manifest to `state/artifact_manifest.json`.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Configuration relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
TARGET_DIRS = [
    PROJECT_ROOT / "data",
    PROJECT_ROOT / "code",
]
OUTPUT_FILE = PROJECT_ROOT / "state" / "artifact_manifest.json"
EXCLUDE_EXTENSIONS = {".pyc", ".pyo", ".pyd", ".so", ".dll", ".exe"}
EXCLUDE_DIRS = {"__pycache__", ".git", ".tox", "node_modules", ".pytest_cache"}

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA-256 hash of a file by reading it in chunks.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        PermissionError: If the file cannot be read.
    """
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        raise FileNotFoundError(f"Cannot hash missing file: {file_path}")
    except PermissionError:
        raise PermissionError(f"Permission denied reading file: {file_path}")

def scan_artifacts() -> List[Path]:
    """
    Recursively scan target directories for valid artifact files.
    
    Returns:
        List of Path objects for files to be hashed.
    """
    artifacts = []
    for target_dir in TARGET_DIRS:
        if not target_dir.exists():
            print(f"Warning: Target directory does not exist, skipping: {target_dir}", file=sys.stderr)
            continue
        
        for root, dirs, files in os.walk(target_dir):
            # Filter out excluded directories in-place
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
            
            for file in files:
                file_path = Path(root) / file
                if file_path.suffix in EXCLUDE_EXTENSIONS:
                    continue
                if file_path.is_file():
                    artifacts.append(file_path)
    return artifacts

def generate_manifest(artifacts: List[Path]) -> Dict[str, Any]:
    """
    Generate a manifest dictionary containing file paths and their hashes.
    
    Args:
        artifacts: List of file paths to hash.
        
    Returns:
        Dictionary containing metadata and a list of artifact records.
    """
    manifest = {
        "version": "1.0",
        "generated_at": "", # Will be set by caller if needed, or left empty for deterministic checks
        "total_files": len(artifacts),
        "artifacts": []
    }
    
    # Sort for deterministic output order
    sorted_artifacts = sorted(artifacts, key=lambda p: str(p))
    
    for file_path in sorted_artifacts:
        try:
            file_hash = compute_file_hash(file_path)
            relative_path = str(file_path.relative_to(PROJECT_ROOT))
            size_bytes = file_path.stat().st_size
            manifest["artifacts"].append({
                "path": relative_path,
                "hash": file_hash,
                "size_bytes": size_bytes
            })
        except (FileNotFoundError, PermissionError) as e:
            # Log error but continue processing other files
            print(f"Error hashing {file_path}: {e}", file=sys.stderr)
            continue
            
    return manifest

def save_manifest(manifest: Dict[str, Any]) -> None:
    """
    Save the manifest to the specified output file.
    
    Args:
        manifest: The manifest dictionary to save.
    """
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, sort_keys=True)
    print(f"Manifest saved to: {OUTPUT_FILE}")

def main():
    """
    Main entry point for the artifact hashing utility.
    
    Scans target directories, computes hashes, and saves the manifest.
    """
    print("Starting artifact hashing scan...")
    artifacts = scan_artifacts()
    
    if not artifacts:
        print("No artifacts found to hash.")
        # Still generate an empty manifest to indicate a successful run with no files
        manifest = generate_manifest([])
        save_manifest(manifest)
        return

    print(f"Found {len(artifacts)} files to hash.")
    manifest = generate_manifest(artifacts)
    save_manifest(manifest)
    print("Artifact hashing completed successfully.")

if __name__ == "__main__":
    main()