import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from utils.logging import get_logger, error, info

logger = get_logger(__name__)

def calculate_sha256(file_path: Path) -> str:
    """Calculate SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def scan_directory_for_hashes(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Scan a directory recursively and calculate SHA-256 hashes for files.
    
    Args:
        directory: Root directory to scan
        extensions: Optional list of file extensions to include (e.g., ['.py', '.yaml'])
        
    Returns:
        Dictionary mapping relative file paths to their SHA-256 hashes
    """
    hashes = {}
    for root, _, files in os.walk(directory):
        for file in files:
            if extensions:
                if not any(file.endswith(ext) for ext in extensions):
                    continue
            
            file_path = Path(root) / file
            relative_path = file_path.relative_to(directory)
            
            try:
                file_hash = calculate_sha256(file_path)
                hashes[str(relative_path)] = file_hash
                info(f"Hashed: {relative_path}")
            except Exception as e:
                error(f"Failed to hash {file_path}: {e}")
    
    return hashes

def load_state_file(state_path: Path) -> Dict[str, Any]:
    """Load existing state file or return empty structure if not found."""
    if not state_path.exists():
        return {
            "project": state_path.parent.name,
            "last_updated": None,
            "artifacts": {}
        }
    
    try:
        with open(state_path, "r") as f:
            return yaml.safe_load(f)
    except Exception as e:
        error(f"Failed to load state file: {e}")
        return {
            "project": state_path.parent.name,
            "last_updated": None,
            "artifacts": {}
        }

def save_state_file(state_path: Path, state: Dict[str, Any]) -> None:
    """Save state dictionary to YAML file."""
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_path, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    
    info(f"State file saved: {state_path}")

def get_artifact_hash(artifact_path: Path) -> str:
    """Get SHA-256 hash of a specific artifact."""
    if not artifact_path.exists():
        raise FileNotFoundError(f"Artifact not found: {artifact_path}")
    
    return calculate_sha256(artifact_path)

def update_project_state(
    project_root: Path, 
    state_file_path: Path,
    target_directories: Optional[List[Path]] = None,
    extensions: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Update the project state file with SHA-256 hashes of all artifacts.
    
    Args:
        project_root: Root directory of the project
        state_file_path: Path to the state YAML file
        target_directories: List of directories to scan (defaults to code/, data/, tests/)
        extensions: Optional list of file extensions to include
        
    Returns:
        Updated state dictionary
    """
    from datetime import datetime
    
    if target_directories is None:
        target_directories = [
            project_root / "code",
            project_root / "data",
            project_root / "tests"
        ]
    
    # Load existing state
    state = load_state_file(state_file_path)
    
    # Update project name
    state["project"] = state_file_path.parent.name
    
    # Scan all target directories
    all_hashes = {}
    for directory in target_directories:
        if directory.exists():
            dir_hashes = scan_directory_for_hashes(directory, extensions)
            all_hashes.update(dir_hashes)
    
    # Update state with new hashes
    state["artifacts"] = all_hashes
    state["last_updated"] = datetime.utcnow().isoformat()
    
    # Save updated state
    save_state_file(state_file_path, state)
    
    return state

def main():
    """Main entry point for state management CLI."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage project state with SHA-256 hashes")
    parser.add_argument(
        "--project-root",
        type=str,
        default=".",
        help="Path to project root directory"
    )
    parser.add_argument(
        "--state-file",
        type=str,
        default=None,
        help="Path to state file (defaults to state/<project>.yaml)"
    )
    parser.add_argument(
        "--extensions",
        nargs="+",
        default=[".py", ".yaml", ".json", ".csv", ".jsonl", ".txt", ".md"],
        help="File extensions to include in scanning"
    )
    
    args = parser.parse_args()
    
    project_root = Path(args.project_root).resolve()
    
    if args.state_file:
        state_file_path = Path(args.state_file).resolve()
    else:
        state_file_path = project_root / "state" / f"{project_root.name}.yaml"
    
    info(f"Scanning project: {project_root}")
    info(f"State file: {state_file_path}")
    
    try:
        state = update_project_state(
            project_root, 
            state_file_path,
            extensions=args.extensions
        )
        
        info(f"Updated state file with {len(state['artifacts'])} artifacts")
        info(f"Last updated: {state['last_updated']}")
        
        return 0
    except Exception as e:
        error(f"Failed to update project state: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
