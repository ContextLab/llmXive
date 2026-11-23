import os
import yaml
import json
import hashlib
from pathlib import Path
from datetime import datetime

# Ensure compatibility with project API surface
# The project expects these names to be importable from src.utils.update_state
# We re-export them to ensure the import path `from src.utils.update_state import ...` works
# even if this file is the only artifact updated in this task.

def ensure_state_dirs():
    """Create state directories if they do not exist."""
    state_dir = Path("state")
    projects_dir = state_dir / "projects"
    state_dir.mkdir(exist_ok=True)
    projects_dir.mkdir(exist_ok=True)
    return projects_dir

def compute_sha256(file_path):
    """Compute SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()

def load_state(project_id):
    """Load the state YAML for a specific project."""
    projects_dir = ensure_state_dirs()
    state_file = projects_dir / f"{project_id}.yaml"
    if not state_file.exists():
        return {"project_id": project_id, "artifacts": {}, "updated_at": None}
    with open(state_file, "r") as f:
        return yaml.safe_load(f)

def save_state(project_id, state_data):
    """Save the state YAML for a specific project."""
    projects_dir = ensure_state_dirs()
    state_file = projects_dir / f"{project_id}.yaml"
    state_data["updated_at"] = datetime.utcnow().isoformat()
    with open(state_file, "w") as f:
        yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)

def update_artifact_hash(state_data, artifact_path, artifact_hash):
    """Update or add an artifact hash in the state data."""
    if "artifacts" not in state_data:
        state_data["artifacts"] = {}
    state_data["artifacts"][artifact_path] = {
        "hash": artifact_hash,
        "last_updated": datetime.utcnow().isoformat()
    }
    return state_data

def scan_and_update_artifacts(project_id, scan_dirs):
    """
    Scan directories for artifacts, compute hashes, and update state.
    
    Args:
        project_id: The project identifier (e.g., PROJ-230-...)
        scan_dirs: List of Path objects to scan for artifacts.
    
    Returns:
        Updated state dictionary.
    """
    state_data = load_state(project_id)
    
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for file_path in scan_dir.rglob("*"):
            if file_path.is_file() and not file_path.name.startswith("."):
                # Skip state files themselves to avoid circular updates
                if "state" in str(file_path):
                    continue
                rel_path = file_path.relative_to(Path.cwd())
                file_hash = compute_sha256(file_path)
                state_data = update_artifact_hash(state_data, str(rel_path), file_hash)
    
    save_state(project_id, state_data)
    return state_data

def update_checksums_state(project_id, checksums_file_path):
    """
    Update the state with the checksums file hash.
    
    Args:
        project_id: The project identifier.
        checksums_file_path: Path to the checksums file (e.g., state/checksums/raw_files.json).
    
    Returns:
        Updated state dictionary.
    """
    if not os.path.exists(checksums_file_path):
        return load_state(project_id)
    
    state_data = load_state(project_id)
    file_hash = compute_sha256(checksums_file_path)
    state_data = update_artifact_hash(state_data, str(checksums_file_path), file_hash)
    save_state(project_id, state_data)
    return state_data

def get_state_summary(project_id):
    """
    Generate a summary of the current state for a project.
    
    Returns:
        Dictionary with summary stats.
    """
    state_data = load_state(project_id)
    artifact_count = len(state_data.get("artifacts", {}))
    return {
        "project_id": project_id,
        "artifact_count": artifact_count,
        "last_updated": state_data.get("updated_at"),
        "artifacts": list(state_data.get("artifacts", {}).keys())
    }

def main():
    """
    CLI entry point for updating state.
    Usage: python -m src.utils.update_state --project_id PROJ-230 --scan-dir data/processed
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Update project state with artifact hashes")
    parser.add_argument("--project_id", type=str, default="PROJ-230-evaluating-the-effectiveness-of-prompt-e",
                        help="Project ID to update state for")
    parser.add_argument("--scan-dir", type=str, nargs="+", default=["data/processed", "data/evaluation"],
                        help="Directories to scan for artifacts")
    
    args = parser.parse_args()
    
    scan_dirs = [Path(d) for d in args.scan_dir]
    state = scan_and_update_artifacts(args.project_id, scan_dirs)
    
    summary = get_state_summary(args.project_id)
    print(f"State updated for {summary['project_id']}")
    print(f"Total artifacts tracked: {summary['artifact_count']}")
    print(f"Last updated: {summary['last_updated']}")

if __name__ == "__main__":
    main()