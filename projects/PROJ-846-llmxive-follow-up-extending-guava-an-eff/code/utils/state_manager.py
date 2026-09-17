import hashlib
import os
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculate SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        Hexadecimal string of the SHA-256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def get_all_files(directory: Path, exclude_patterns: Optional[List[str]] = None) -> List[Path]:
    """
    Get all files in a directory recursively.
    
    Args:
        directory: Directory to scan
        exclude_patterns: List of glob patterns to exclude
        
    Returns:
        List of file paths
    """
    if exclude_patterns is None:
        exclude_patterns = ["*.pyc", "__pycache__", ".git", "*.egg-info"]
    
    files = []
    for root, dirs, filenames in os.walk(directory):
        # Filter out excluded directories
        dirs[:] = [d for d in dirs if not any(pattern in d for pattern in exclude_patterns)]
        
        for filename in filenames:
            # Skip excluded files
            if any(filename.endswith(pattern.replace("*", "")) for pattern in exclude_patterns if pattern.startswith("*")):
                continue
            if any(pattern in filename for pattern in exclude_patterns if not pattern.startswith("*")):
                continue
                
            file_path = Path(root) / filename
            files.append(file_path)
    
    return files

def generate_state_hash(files: Dict[str, str]) -> str:
    """
    Generate a hash representing the state of multiple files.
    
    Args:
        files: Dictionary mapping file paths to their hashes
        
    Returns:
        Combined hash string
    """
    combined = "".join(f"{path}:{hash}" for path, hash in sorted(files.items()))
    return hashlib.sha256(combined.encode()).hexdigest()

def update_state_file(state_path: Path, project_id: str, files: Dict[str, str]) -> None:
    """
    Update the state YAML file with file hashes and timestamps.
    
    Args:
        state_path: Path to the state YAML file
        project_id: Project identifier
        files: Dictionary mapping relative file paths to their SHA-256 hashes
    """
    state_path.parent.mkdir(parents=True, exist_ok=True)
    
    state_data = {
        "project_id": project_id,
        "last_updated": datetime.now().isoformat(),
        "file_hashes": files,
        "state_hash": generate_state_hash(files)
    }
    
    with open(state_path, "w") as f:
        yaml.dump(state_data, f, default_flow_style=False, sort_keys=False)

def verify_state_integrity(state_path: Path, project_id: str) -> bool:
    """
    Verify the integrity of the state file against current file hashes.
    
    Args:
        state_path: Path to the state YAML file
        project_id: Project identifier
        
    Returns:
        True if state is valid, False otherwise
    """
    if not state_path.exists():
        return False
    
    with open(state_path, "r") as f:
        state_data = yaml.safe_load(f)
    
    if state_data.get("project_id") != project_id:
        return False
    
    stored_hashes = state_data.get("file_hashes", {})
    current_hashes = {}
    
    # Recalculate hashes for tracked files
    for rel_path in stored_hashes.keys():
        full_path = state_path.parent / rel_path
        if full_path.exists():
            current_hashes[rel_path] = calculate_file_hash(full_path)
        else:
            current_hashes[rel_path] = "MISSING"
    
    return stored_hashes == current_hashes

def get_state_summary(state_path: Path) -> Dict[str, Any]:
    """
    Get a summary of the current state.
    
    Args:
        state_path: Path to the state YAML file
        
    Returns:
        Dictionary with state summary
    """
    if not state_path.exists():
        return {"exists": False}
    
    with open(state_path, "r") as f:
        state_data = yaml.safe_load(f)
    
    return {
        "exists": True,
        "project_id": state_data.get("project_id"),
        "last_updated": state_data.get("last_updated"),
        "file_count": len(state_data.get("file_hashes", {})),
        "state_hash": state_data.get("state_hash")
    }

def main():
    """Main entry point for state management demonstration.
    
    This function scans the project root for relevant source files,
    calculates their SHA-256 hashes, and updates the state YAML file
    located at state/PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml.
    """
    project_root = Path.cwd()
    project_id = "PROJ-846-llmxive-follow-up-extending-guava-an-eff"
    state_path = project_root / "state" / f"{project_id}.yaml"
    
    # Define directories to track for project state
    # We track code, data/processed, data/artifacts, and tests
    directories_to_track = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts"
    ]
    
    all_files = []
    for directory in directories_to_track:
        if directory.exists():
            all_files.extend(get_all_files(directory))
    
    if not all_files:
        print("No files found to track in specified directories.")
        return
    
    # Calculate hashes for all files, relative to project root
    file_hashes = {}
    for f in all_files:
        try:
            rel_path = str(f.relative_to(project_root))
            file_hashes[rel_path] = calculate_file_hash(f)
        except ValueError:
            # Skip files not under project root
            continue
    
    if not file_hashes:
        print("No valid files found to hash.")
        return
    
    update_state_file(state_path, project_id, file_hashes)
    print(f"State updated successfully: {state_path}")
    summary = get_state_summary(state_path)
    print(f"State summary: {summary}")

if __name__ == "__main__":
    main()