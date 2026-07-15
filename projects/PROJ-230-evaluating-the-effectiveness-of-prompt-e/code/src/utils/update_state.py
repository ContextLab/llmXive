"""
State management utility for tracking artifact hashes and project state.
Implements Constitution Principle V: State tracking and versioning.
"""
import os
import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

# Project ID from tasks.md context
PROJECT_ID = "PROJ-230-evaluating-the-effectiveness-of-prompt-e"

def ensure_state_dirs(state_root: Path) -> None:
    """Ensure state directories exist."""
    state_root.mkdir(parents=True, exist_ok=True)
    (state_root / "projects").mkdir(parents=True, exist_ok=True)
    (state_root / "checksums").mkdir(parents=True, exist_ok=True)

def compute_sha256(file_path: Path) -> str:
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_state(state_root: Path, project_id: str) -> Dict[str, Any]:
    """Load project state from YAML file."""
    state_file = state_root / "projects" / f"{project_id}.yaml"
    if not state_file.exists():
        return {
            "project_id": project_id,
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
            "artifacts": {},
            "checksums": {},
            "summary": {}
        }
    
    with open(state_file, "r") as f:
        return yaml.safe_load(f)

def save_state(state_root: Path, project_id: str, state: Dict[str, Any]) -> None:
    """Save project state to YAML file."""
    state_file = state_root / "projects" / f"{project_id}.yaml"
    state["updated_at"] = datetime.utcnow().isoformat()
    with open(state_file, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

def update_artifact_hash(state: Dict[str, Any], artifact_path: str, file_path: Path) -> Dict[str, Any]:
    """Update hash for a specific artifact."""
    if not file_path.exists():
        return state
    
    file_hash = compute_sha256(file_path)
    if "artifacts" not in state:
        state["artifacts"] = {}
    
    state["artifacts"][artifact_path] = {
        "hash": file_hash,
        "updated_at": datetime.utcnow().isoformat(),
        "size_bytes": file_path.stat().st_size
    }
    return state

def scan_and_update_artifacts(state_root: Path, project_id: str, scan_dirs: List[Path]) -> Dict[str, Any]:
    """Scan directories and update artifact hashes in state."""
    state = load_state(state_root, project_id)
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        
        for file_path in scan_dir.rglob("*"):
            if file_path.is_file():
                rel_path = file_path.relative_to(state_root.parent)
                state = update_artifact_hash(state, str(rel_path), file_path)
    
    return state

def update_checksums_state(state_root: Path, project_id: str, checksum_file: Path) -> Dict[str, Any]:
    """Update checksums state from a checksum file."""
    state = load_state(state_root, project_id)
    
    if checksum_file.exists():
        checksums = {}
        with open(checksum_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and "  " in line:
                    hash_val, file_path = line.split("  ", 1)
                    checksums[file_path] = hash_val
        
        state["checksums"] = checksums
    
    return state

def get_state_summary(state: Dict[str, Any]) -> Dict[str, Any]:
    """Generate a summary of the current state."""
    return {
        "total_artifacts": len(state.get("artifacts", {})),
        "total_checksums": len(state.get("checksums", {})),
        "created_at": state.get("created_at"),
        "updated_at": state.get("updated_at"),
        "artifact_paths": list(state.get("artifacts", {}).keys())
    }

def main():
    """Main entry point for updating state."""
    project_root = Path(__file__).parent.parent.parent.parent
    state_root = project_root / "state"
    
    ensure_state_dirs(state_root)
    
    # Define directories to scan
    scan_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "prompts",
        project_root / "data" / "evaluation",
        project_root / "state" / "checksums"
    ]
    
    # Load and update state
    state = load_state(state_root, PROJECT_ID)
    state = scan_and_update_artifacts(state_root, PROJECT_ID, scan_dirs)
    
    # Update checksums if they exist
    checksum_file = state_root / "checksums" / "checksums.txt"
    if checksum_file.exists():
        state = update_checksums_state(state_root, PROJECT_ID, checksum_file)
    
    # Save updated state
    save_state(state_root, PROJECT_ID, state)
    
    # Print summary
    summary = get_state_summary(state)
    print(f"State updated for project: {PROJECT_ID}")
    print(f"Total artifacts tracked: {summary['total_artifacts']}")
    print(f"Total checksums tracked: {summary['total_checksums']}")
    print(f"Last updated: {summary['updated_at']}")

if __name__ == "__main__":
    main()
