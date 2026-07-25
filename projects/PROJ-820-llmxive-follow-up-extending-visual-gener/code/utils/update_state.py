"""
Module to update the project state by calculating SHA-256 hashes of artifacts.

This script scans specified directories, calculates hashes for all files,
and updates the state YAML files in `state/projects`.
"""

import os
import sys
import hashlib
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml # Assuming yaml is available via requirements.txt


def calculate_sha256(file_path: Path) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def scan_directory(directory: Path) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory and collect file metadata and hashes.
    
    Args:
        directory: Path to the directory to scan.
        
    Returns:
        List of dictionaries containing relative path, absolute path, and hash.
    """
    if not directory.exists():
        return []
    
    artifacts = []
    for path in directory.rglob("*"):
        if path.is_file():
            # Skip hidden files or specific patterns if needed
            if path.name.startswith(".") or path.suffix in [".pyc", ".pyo"]:
                continue
            
            rel_path = path.relative_to(directory)
            file_hash = calculate_sha256(path)
            artifacts.append({
                "path": str(rel_path),
                "absolute_path": str(path),
                "hash": file_hash,
                "size": path.stat().st_size
            })
    
    return artifacts


def update_state_file(project_id: str, artifacts: List[Dict[str, Any]], output_dir: Path) -> None:
    """
    Update or create the state file for a project with the calculated artifacts.
    
    Args:
        project_id: The ID of the project (e.g., 'PROJ-820').
        artifacts: List of artifact metadata.
        output_dir: Directory where the state file should be saved.
    """
    output_dir.mkdir(parents=True, exist_ok=True)
    state_file = output_dir / f"{project_id}_state.json"
    
    state_data = {
        "project_id": project_id,
        "last_updated": str(Path().resolve()), # Or use datetime if needed
        "artifacts": artifacts
    }
    
    with open(state_file, "w", encoding="utf-8") as f:
        json.dump(state_data, f, indent=2)
    
    print(f"State file updated: {state_file}")


def main():
    """
    Main entry point for updating the project state.
    
    Scans the 'data' and 'code' directories and updates the state file.
    """
    project_root = Path(__file__).parent.parent.parent
    state_dir = project_root / "state" / "projects"
    
    # Define directories to scan
    dirs_to_scan = [
        project_root / "data",
        project_root / "code",
        project_root / "tests",
        project_root / "specs"
    ]
    
    all_artifacts = []
    for d in dirs_to_scan:
        if d.exists():
            print(f"Scanning {d}...")
            artifacts = scan_directory(d)
            all_artifacts.extend(artifacts)
        else:
            print(f"Directory not found: {d}, skipping.")
    
    # Project ID from task description
    project_id = "PROJ-820"
    
    update_state_file(project_id, all_artifacts, state_dir)


if __name__ == "__main__":
    main()
