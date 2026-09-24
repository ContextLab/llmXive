"""
State Manager for llmXive Project.

Handles atomic updates of the project state YAML file, calculating content hashes
for artifacts and recording timestamps.
"""
import hashlib
import os
import tempfile
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Optional

# Project root relative to this file (utils/state_manager.py is in code/utils/)
# We assume the project root is 4 levels up: code/utils/ -> code/ -> projects/.../ -> root
# However, to be robust, we will calculate the project root based on the existence
# of the 'state' directory or by traversing up until we find a known marker.
# For this implementation, we assume the standard structure:
# Root/
#   state/
#   projects/PROJ-846-.../code/utils/state_manager.py

def get_project_root() -> Path:
    """
    Traverses up from the current file location to find the project root.
    The project root is defined as the directory containing the 'state' folder.
    """
    current = Path(__file__).resolve()
    # Traverse up
    for _ in range(10): # Limit traversal to avoid infinite loops
        parent = current.parent
        if (parent / "state").is_dir():
            return parent
        current = parent
    # Fallback: if not found, assume current working directory or a standard relative path
    # Given the task context, we assume the root is the parent of the 'projects' directory
    # which is likely 3 levels up from code/utils
    return Path(__file__).resolve().parent.parent.parent.parent

def calculate_file_hash(file_path: Path) -> str:
    """
    Calculates the SHA-256 hash of a file's contents.
    
    Args:
        file_path: Path to the file.
        
    Returns:
        Hex digest string of the file hash.
    """
    if not file_path.exists():
        return ""
    
    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    except (IOError, OSError):
        return ""

def get_all_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Recursively gets all files in a directory.
    
    Args:
        directory: Path to the directory.
        extensions: Optional list of extensions to filter by (e.g., ['.json', '.csv']).
                    
    Returns:
        List of Path objects.
    """
    if not directory.exists():
        return []
    
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions:
                if any(file_path.suffix == ext for ext in extensions):
                    files.append(file_path)
            else:
                # Skip hidden files and .gitkeep
                if not filename.startswith('.') and filename != '.gitkeep':
                    files.append(file_path)
    return files

def generate_state_hash(artifacts: Dict[str, str]) -> str:
    """
    Generates a hash of the entire state dictionary to verify integrity.
    
    Args:
        artifacts: The dictionary of artifact hashes.
                    
    Returns:
        Hex digest string of the state hash.
    """
    # Sort keys to ensure deterministic hashing
    sorted_items = sorted(artifacts.items())
    content = yaml.dump(sorted_items, sort_keys=True)
    return hashlib.sha256(content.encode('utf-8')).hexdigest()

def update_state_file(state_path: Path, artifact_dirs: Optional[List[Path]] = None) -> Dict[str, Any]:
    """
    Updates the state YAML file with current artifact hashes and timestamp.
    Uses atomic write (temp file + rename) to prevent corruption.
    
    Args:
        state_path: Path to the state YAML file.
        artifact_dirs: List of directories to scan for artifacts. If None, defaults to standard data/artifacts.
                    
    Returns:
        The updated state dictionary.
    """
    if artifact_dirs is None:
        # Default to data/artifacts relative to project root
        project_root = get_project_root()
        artifact_dirs = [project_root / "data" / "artifacts"]
    
    artifact_hashes = {}
    
    # Scan provided directories
    for dir_path in artifact_dirs:
        if not dir_path.exists():
            continue
        
        # Get relative path for the key
        try:
            rel_base = dir_path.relative_to(get_project_root())
        except ValueError:
            rel_base = dir_path.name
        
        files = get_all_files(dir_path)
        for file_path in files:
            try:
                # Key is relative path from project root
                rel_path = file_path.relative_to(get_project_root())
                file_hash = calculate_file_hash(file_path)
                if file_hash:
                    artifact_hashes[str(rel_path)] = file_hash
            except ValueError:
                # File is outside project root, skip or handle differently
                continue
    
    # Prepare state content
    current_time = datetime.utcnow().isoformat()
    state_content = {
        "artifact_hashes": artifact_hashes,
        "updated_at": current_time
    }
    
    # Atomic write
    # Create temp file in the same directory to ensure same filesystem for rename
    if not state_path.parent.exists():
        state_path.parent.mkdir(parents=True, exist_ok=True)
    
    fd, temp_path = tempfile.mkstemp(dir=state_path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'w') as f:
            yaml.dump(state_content, f, default_flow_style=False, sort_keys=False)
        
        # Atomic rename
        os.replace(temp_path, state_path)
        
    except Exception:
        # Clean up temp file if something goes wrong
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise
    
    return state_content

def verify_state_integrity(state_path: Path) -> bool:
    """
    Verifies the integrity of the state file by recalculating hashes.
    
    Args:
        state_path: Path to the state YAML file.
                    
    Returns:
        True if state is valid, False otherwise.
    """
    if not state_path.exists():
        return False
    
    try:
        with open(state_path, 'r') as f:
            state_data = yaml.safe_load(f)
        
        if not isinstance(state_data, dict) or 'artifact_hashes' not in state_data:
            return False
        
        # Recalculate hashes for the recorded artifacts
        project_root = get_project_root()
        for rel_path_str, recorded_hash in state_data['artifact_hashes'].items():
            file_path = project_root / rel_path_str
            if not file_path.exists():
                # Artifact missing
                return False
            
            current_hash = calculate_file_hash(file_path)
            if current_hash != recorded_hash:
                # Artifact modified
                return False
        
        return True
    except Exception:
        return False

def get_state_summary(state_path: Path) -> Optional[Dict[str, Any]]:
    """
    Retrieves a summary of the state file.
    
    Args:
        state_path: Path to the state YAML file.
                    
    Returns:
        Dictionary with summary info or None if file invalid.
    """
    if not state_path.exists():
        return None
    
    try:
        with open(state_path, 'r') as f:
            return yaml.safe_load(f)
    except Exception:
        return None

def main():
    """
    Main entry point for state management CLI.
    Updates the state file for the current project.
    """
    project_root = get_project_root()
    state_dir = project_root / "state"
    state_file = state_dir / "PROJ-846-llmxive-follow-up-extending-guava-an-eff.yaml"
    
    print(f"Updating state file: {state_file}")
    
    # Define directories to scan (standard data artifacts)
    artifact_dirs = [project_root / "data" / "artifacts"]
    
    try:
        state = update_state_file(state_file, artifact_dirs)
        print(f"State updated successfully.")
        print(f"  Timestamp: {state['updated_at']}")
        print(f"  Artifacts tracked: {len(state['artifact_hashes'])}")
        
        # Verify integrity immediately after write
        if verify_state_integrity(state_file):
            print("  Integrity check: PASSED")
        else:
            print("  Integrity check: FAILED")
            
    except Exception as e:
        print(f"Error updating state: {e}")
        raise

if __name__ == "__main__":
    main()