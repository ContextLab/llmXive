import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, error, info

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except FileNotFoundError:
        error(f"File not found: {file_path}")
        raise
    except Exception as e:
        error(f"Error calculating hash for {file_path}: {e}")
        raise

def scan_directory_for_hashes(directory: Path, exclude_patterns: Optional[List[str]] = None) -> Dict[str, str]:
    """Scan a directory recursively and calculate SHA-256 hashes for all files."""
    if exclude_patterns is None:
        exclude_patterns = []
    
    hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            # Skip hidden files and common non-artifact files
            if file.startswith('.'):
                continue
            if any(file.endswith(ext) for ext in exclude_patterns):
                continue
            
            file_path = Path(root) / file
            try:
                relative_path = file_path.relative_to(directory)
                file_hash = calculate_sha256(file_path)
                hashes[str(relative_path)] = file_hash
            except Exception as e:
                error(f"Skipping {file_path}: {e}")
                continue
    return hashes

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load an existing state YAML file."""
    if not state_path.exists():
        return {"project": state_path.parent.name, "last_updated": None, "artifacts": {}}
    
    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        error(f"Error loading state file {state_path}: {e}")
        return {"project": state_path.parent.name, "last_updated": None, "artifacts": {}}

def save_state_file(state_path: Path, state_data: Dict[str, Any]) -> None:
    """Save state data to a YAML file."""
    try:
        state_path.parent.mkdir(parents=True, exist_ok=True)
        with open(state_path, "w") as f:
            yaml.safe_dump(state_data, f, default_flow_style=False, sort_keys=False)
        info(f"State file saved: {state_path}")
    except Exception as e:
        error(f"Error saving state file {state_path}: {e}")
        raise

def get_artifact_hash(file_path: Path) -> str:
    """Get the SHA-256 hash of a single artifact file."""
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")
    return calculate_sha256(file_path)

def update_project_state(project_root: Path, state_file_name: str = "state.yaml") -> Dict[str, Any]:
    """
    Update the project state file with SHA-256 hashes of all artifacts.
    
    Args:
        project_root: The root path of the project.
        state_file_name: The name of the state file (default: 'state.yaml').
    
    Returns:
        The updated state dictionary.
    """
    state_path = project_root / "state" / state_file_name
    
    # Load existing state or initialize new one
    state_data = load_state_file(state_path)
    state_data["project"] = project_root.name
    
    # Define directories to scan for artifacts
    # Typically: data/processed, data/artifacts, figures, etc.
    # Exclude code/, tests/, and temporary files
    directories_to_scan = [
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "figures",
    ]
    
    exclude_patterns = [".pyc", ".pyo", "__pycache__", ".git", ".DS_Store", ".tmp"]
    
    all_hashes = {}
    for directory in directories_to_scan:
        if directory.exists():
            info(f"Scanning directory: {directory}")
            dir_hashes = scan_directory_for_hashes(directory, exclude_patterns)
            all_hashes.update(dir_hashes)
        else:
            info(f"Directory not found, skipping: {directory}")
    
    # Update state with new hashes
    state_data["artifacts"] = all_hashes
    from datetime import datetime
    state_data["last_updated"] = datetime.utcnow().isoformat()
    
    # Save updated state
    save_state_file(state_path, state_data)
    
    return state_data

def main():
    """Main entry point for state management."""
    import argparse
    from utils.config import get_project_root

    parser = argparse.ArgumentParser(description="Update project state file with artifact hashes.")
    parser.add_argument("--project-root", type=str, help="Path to project root (default: auto-detect)")
    parser.add_argument("--state-file", type=str, default="state.yaml", help="Name of state file")
    args = parser.parse_args()

    project_root = Path(args.project_root) if args.project_root else get_project_root()
    
    info(f"Updating state for project: {project_root}")
    try:
        state = update_project_state(project_root, args.state_file)
        info(f"State update complete. Total artifacts tracked: {len(state['artifacts'])}")
    except Exception as e:
        error(f"Failed to update state: {e}")
        raise

if __name__ == "__main__":
    main()
