import json
import hashlib
import os
import sys
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, Any, List

import yaml

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory(directory: Path, extensions: List[str]) -> List[Dict[str, Any]]:
    """
    Recursively scan a directory for files with specific extensions.
    Returns a list of dicts with 'relative_path' and 'hash'.
    The relative_path is relative to the project root (parent of the scan directory's parent context).
    """
    artifacts = []
    if not directory.exists():
        return artifacts

    project_root = directory.parent.parent  # Assuming directory is data/derived or results/ at root level
    
    for root, _, files in os.walk(directory):
        for file in files:
            if any(file.endswith(ext) for ext in extensions):
                file_path = Path(root) / file
                # Calculate relative path from project root
                relative_path = file_path.relative_to(project_root)
                file_hash = calculate_sha256(file_path)
                artifacts.append({
                    "relative_path": str(relative_path),
                    "hash": file_hash
                })
    return artifacts

def load_existing_state(state_path: Path) -> Dict[str, Any]:
    """Load existing state.yaml if it exists."""
    if state_path.exists():
        with open(state_path, "r") as f:
            return yaml.safe_load(f) or {}
    return {}

def save_state(state_path: Path, state: Dict[str, Any]) -> None:
    """Save state to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def main():
    project_root = Path(__file__).resolve().parent.parent.parent
    state_file_path = project_root / "state" / "projects" / "PROJ-865-llmxive-followup-extending-autoresearch.yaml"
    
    # Define directories to scan
    scan_dirs = [
        project_root / "data" / "derived",
        project_root / "results"
    ]
    
    # Define file extensions to include
    extensions = [".json", ".csv", ".yaml", ".yml"]
    
    # Scan for artifacts
    all_artifacts = []
    for scan_dir in scan_dirs:
        artifacts = scan_directory(scan_dir, extensions)
        all_artifacts.extend(artifacts)
    
    # Sort artifacts by relative path for reproducibility
    all_artifacts.sort(key=lambda x: x["relative_path"])
    
    # Load existing state to preserve metadata if needed
    existing_state = load_existing_state(state_file_path)
    
    # Build new state
    current_time = datetime.now(timezone.utc).isoformat()
    new_state = {
        "project_id": "PROJ-865-llmxive-followup-extending-autoresearch",
        "updated_at": current_time,
        "artifacts": all_artifacts,
        "total_artifacts": len(all_artifacts)
    }
    
    # Save state
    save_state(state_file_path, new_state)
    
    print(f"State updated successfully at {state_file_path}")
    print(f"Total artifacts scanned: {len(all_artifacts)}")
    print(f"Timestamp: {current_time}")

if __name__ == "__main__":
    main()
