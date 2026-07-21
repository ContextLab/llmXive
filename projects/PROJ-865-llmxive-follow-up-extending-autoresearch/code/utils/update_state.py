import hashlib
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional
import yaml

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_artifacts(base_dir: Path) -> Dict[str, str]:
    """
    Recursively scan a directory for files and calculate their SHA-256 hashes.
    Returns a dictionary mapping relative path to hash.
    """
    artifacts = {}
    if not base_dir.exists():
        return artifacts
    
    for root, _, files in os.walk(base_dir):
        for file in files:
            # Skip hidden files
            if file.startswith('.'):
                continue
            
            file_path = Path(root) / file
            try:
                rel_path = str(file_path.relative_to(base_dir))
                hash_val = calculate_sha256(file_path)
                artifacts[rel_path] = hash_val
            except Exception as e:
                print(f"Warning: Could not hash {file_path}: {e}", file=sys.stderr)
    
    return artifacts

def load_current_state(state_path: Path) -> Dict[str, Any]:
    """Load the current state file if it exists."""
    if not state_path.exists():
        return {
            "project_id": "PROJ-865-llmxive-follow-up-extending-autoresearch",
            "artifact_hashes": {},
            "updated_at": None,
            "tasks_completed": []
        }
    
    with open(state_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def update_state_file(state_path: Path, artifact_hashes: Dict[str, str], tasks_completed: List[str]) -> None:
    """
    Update the state file with new artifact hashes and timestamp.
    Specifically updates:
    - artifact_hashes: map of file paths to hashes
    - updated_at: ISO8601 timestamp
    """
    current_state = load_current_state(state_path)
    
    # Update specific keys as required by T007 and T034
    current_state["artifact_hashes"] = artifact_hashes
    current_state["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    # Merge tasks completed if provided (append unique)
    if tasks_completed:
        existing = set(current_state.get("tasks_completed", []))
        for t in tasks_completed:
            existing.add(t)
        current_state["tasks_completed"] = sorted(list(existing))
    
    # Ensure project_id is set correctly
    current_state["project_id"] = "PROJ-865-llmxive-follow-up-extending-autoresearch"
    
    # Write back
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with open(state_path, 'w', encoding='utf-8') as f:
        yaml.dump(current_state, f, default_flow_style=False, sort_keys=False)

def main():
    """
    Main entry point for T034: Finalize state.yaml with all artifact hashes.
    Scans data/derived/, data/artifacts/, and results/ (if exists) and updates state.yaml.
    This task runs after all pipeline stages are complete to capture the final state.
    """
    project_root = Path(__file__).resolve().parent.parent
    state_path = project_root / "state" / "projects" / "PROJ-865-llmxive-follow-up-extending-autoresearch.yaml"
    
    # Directories to scan: data/derived, data/artifacts, and results (if it exists)
    dirs_to_scan = [
        project_root / "data" / "derived",
        project_root / "data" / "artifacts"
    ]
    
    # Check for a 'results' directory at project root as mentioned in task description
    results_dir = project_root / "results"
    if results_dir.exists():
        dirs_to_scan.append(results_dir)
    
    all_hashes = {}
    for d in dirs_to_scan:
        if d.exists():
            hashes = scan_artifacts(d)
            # Prefix with directory name to avoid collisions across roots
            for k, v in hashes.items():
                prefixed_key = f"{d.name}/{k}"
                all_hashes[prefixed_key] = v
        else:
            print(f"Warning: Directory does not exist, skipping: {d}", file=sys.stderr)
    
    # Determine tasks to add (T034 is the finalization step)
    tasks_completed = ["T034"]
    
    update_state_file(state_path, all_hashes, tasks_completed)
    print(f"State updated: {state_path}")
    print(f"Total artifacts scanned: {len(all_hashes)}")
    if len(all_hashes) == 0:
        print("Note: No artifacts found in scanned directories. Ensure pipeline has produced output files.")

if __name__ == "__main__":
    main()