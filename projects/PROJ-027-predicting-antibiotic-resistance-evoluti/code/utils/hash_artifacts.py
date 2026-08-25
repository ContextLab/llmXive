import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

# Import the fixed logger
from utils.logging import get_logger

logger = get_logger(__name__)

def compute_file_hash(file_path: Path) -> str:
    """
    Compute SHA256 hash of a file.
    
    Args:
        file_path: Path to the file
    
    Returns:
        Hex digest of the SHA256 hash
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def collect_files(directory: Path, extensions: Optional[List[str]] = None) -> List[Path]:
    """
    Collect all files in a directory recursively.
    
    Args:
        directory: Root directory to scan
        extensions: Optional list of file extensions to include (e.g., ['.py', '.csv'])
    
    Returns:
        List of file paths
    """
    files = []
    for root, _, filenames in os.walk(directory):
        for filename in filenames:
            file_path = Path(root) / filename
            if extensions is None or file_path.suffix in extensions:
                files.append(file_path)
    return sorted(files)

def hash_directory(directory: Path, extensions: Optional[List[str]] = None) -> Dict[str, str]:
    """
    Compute hashes for all files in a directory.
    
    Args:
        directory: Root directory to hash
        extensions: Optional list of file extensions to include
    
    Returns:
        Dictionary mapping relative file paths to their SHA256 hashes
    """
    hashes = {}
    files = collect_files(directory, extensions)
    
    for file_path in files:
        relative_path = file_path.relative_to(directory.parent)
        file_hash = compute_file_hash(file_path)
        hashes[str(relative_path)] = file_hash
        logger.debug(f"Hashed: {relative_path}")
    
    return hashes

def load_state(state_file: Path) -> Dict[str, Any]:
    """
    Load the state file if it exists, otherwise return an empty state structure.
    
    Args:
        state_file: Path to the state YAML/JSON file
    
    Returns:
        State dictionary
    """
    if state_file.exists():
        # Try to load as JSON first, then YAML
        try:
            with open(state_file, 'r') as f:
                return json.load(f)
        except json.JSONDecodeError:
            # Fallback for YAML if json fails (simple parser for basic YAML)
            logger.warning(f"State file {state_file} is not valid JSON, attempting basic YAML parse")
            return load_yaml_fallback(state_file)
    else:
        logger.info(f"State file {state_file} does not exist. Creating new state.")
        return {
            "projects": {}
        }

def load_yaml_fallback(state_file: Path) -> Dict[str, Any]:
    """
    Simple YAML parser fallback for basic key-value structures.
    Only handles the specific format expected for state files.
    """
    result = {"projects": {}}
    current_project = None
    current_section = None
    
    with open(state_file, 'r') as f:
        for line in f:
            line = line.rstrip()
            if not line or line.startswith('#'):
                continue
            
            # Check for project key
            if line.startswith('projects:'):
                continue
            
            # Check for project ID (indented with 2 spaces)
            if line.startswith('  PROJ-') and ':' in line:
                project_id = line.split(':')[0].strip()
                result["projects"][project_id] = {}
                current_project = project_id
                continue
            
            # Check for section within project (indented with 4 spaces)
            if current_project and line.startswith('    ') and ':' in line and not line.startswith('      '):
                key = line.strip().split(':')[0]
                value = line.strip().split(':', 1)[1].strip() if ':' in line else ""
                
                if value.startswith('[') and value.endswith(']'):
                    # List value
                    value = [x.strip().strip('"').strip("'") for x in value[1:-1].split(',')]
                elif value.isdigit():
                    value = int(value)
                elif value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                
                result["projects"][current_project][key] = value
                current_section = key
                continue
            
            # Check for nested value (indented with 6 spaces)
            if current_project and current_section and line.startswith('      ') and ':' in line:
                key = line.strip().split(':')[0]
                value = line.strip().split(':', 1)[1].strip()
                if key == 'artifact_hashes':
                    if key not in result["projects"][current_project]:
                        result["projects"][current_project][key] = {}
                    result["projects"][current_project][key][key.split('.')[0]] = value
    
    return result

def save_state(state: Dict[str, Any], state_file: Path) -> None:
    """
    Save the state dictionary to a JSON file.
    
    Args:
        state: State dictionary to save
        state_file: Path to the state file
    """
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, 'w') as f:
        json.dump(state, f, indent=2)
    logger.info(f"State saved to {state_file}")

def update_state_with_hashes(
    project_id: str,
    data_dir: Path,
    code_dir: Path,
    state_file: Path,
    current_stage: str = "research_accepted"
) -> None:
    """
    Update the state file with artifact hashes for a project.
    
    Args:
        project_id: Project identifier (e.g., PROJ-027-...)
        data_dir: Path to data directory
        code_dir: Path to code directory
        state_file: Path to the state file
        current_stage: Current stage of the project
    """
    logger.info(f"Updating state for project: {project_id}")
    
    # Load existing state
    state = load_state(state_file)
    
    # Initialize project entry if it doesn't exist
    if project_id not in state["projects"]:
        state["projects"][project_id] = {}
    
    project_state = state["projects"][project_id]
    
    # Compute hashes for data directory
    logger.info(f"Hashing data directory: {data_dir}")
    if data_dir.exists():
        data_hashes = hash_directory(data_dir, ['.csv', '.json', '.nwk', '.pkl', '.png', '.txt', '.log'])
        project_state["data_hashes"] = data_hashes
    else:
        logger.warning(f"Data directory {data_dir} does not exist")
        project_state["data_hashes"] = {}
    
    # Compute hashes for code directory
    logger.info(f"Hashing code directory: {code_dir}")
    if code_dir.exists():
        code_hashes = hash_directory(code_dir, ['.py', '.sh', '.yaml', '.yml', '.toml'])
        project_state["code_hashes"] = code_hashes
    else:
        logger.warning(f"Code directory {code_dir} does not exist")
        project_state["code_hashes"] = {}
    
    # Aggregate all hashes
    all_hashes = {}
    all_hashes.update(data_hashes)
    all_hashes.update(code_hashes)
    project_state["artifact_hashes"] = all_hashes
    
    # Update metadata
    import datetime
    project_state["updated_at"] = datetime.datetime.now().isoformat()
    project_state["current_stage"] = current_stage
    project_state["research_complete"] = True
    
    # Save updated state
    save_state(state, state_file)
    
    logger.info(f"Successfully updated state for {project_id} with {len(all_hashes)} artifacts")

def main() -> int:
    """
    Main entry point for the hash_artifacts script.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    # Define paths relative to project root
    project_root = Path(__file__).resolve().parent.parent.parent
    data_dir = project_root / "data"
    code_dir = project_root / "code"
    state_dir = project_root / "state" / "projects"
    
    # Project ID for this specific project
    project_id = "PROJ-027-predicting-antibiotic-resistance-evoluti"
    state_file = state_dir / f"{project_id}.yaml"
    
    logger.info(f"Starting artifact hashing for {project_id}")
    
    try:
        # Update state with hashes
        update_state_with_hashes(
            project_id=project_id,
            data_dir=data_dir,
            code_dir=code_dir,
            state_file=state_file,
            current_stage="research_accepted"
        )
        
        logger.info("Artifact hashing completed successfully")
        return 0
        
    except Exception as e:
        logger.error(f"Error during artifact hashing: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
