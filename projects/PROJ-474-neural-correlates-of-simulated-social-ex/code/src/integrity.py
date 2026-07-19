import os
import hashlib
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Set, Any
import json

from src.utils import get_logger

# Ensure paths are relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state" / "projects"

def get_state_path() -> Path:
    """Get the path to the state file."""
    state_file = STATE_DIR / "PROJ-474-neural-correlates-social-ex.yaml"
    if not state_file.exists():
        state_file.parent.mkdir(parents=True, exist_ok=True)
        # Create an empty state file if it doesn't exist
        with open(state_file, 'w') as f:
            yaml.dump({"artifact_hashes": {}}, f)
    return state_file

def compute_file_hash(file_path: Path) -> str:
    """Compute the SHA-256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_hashes(state_file: Path) -> Dict[str, Any]:
    """Load the state file."""
    with open(state_file, 'r') as f:
        return yaml.safe_load(f)

def save_hashes(state_file: Path, data: Dict[str, Any]) -> None:
    """Save the state file."""
    with open(state_file, 'w') as f:
        yaml.dump(data, f)

def update_hashes(state_file: Path, file_paths: List[Path]) -> None:
    """
    Update the artifact_hashes in the state file with the SHA-256 hashes of the given files.
    """
    state_data = load_hashes(state_file)
    if "artifact_hashes" not in state_data:
        state_data["artifact_hashes"] = {}
    
    for file_path in file_paths:
        if file_path.exists():
            file_hash = compute_file_hash(file_path)
            # Store the hash with a relative path
            relative_path = file_path.relative_to(PROJECT_ROOT)
            state_data["artifact_hashes"][str(relative_path)] = file_hash
        else:
            logger = get_logger("Integrity")
            logger.warning(f"File not found: {file_path}")
    
    save_hashes(state_file, state_data)

def scan_data_directory(data_dir: Path) -> List[Path]:
    """Scan a directory for data files."""
    files = []
    for root, _, filenames in os.walk(data_dir):
        for filename in filenames:
            files.append(Path(root) / filename)
    return files

def generate_hashes(data_dir: Path) -> Dict[str, str]:
    """Generate hashes for all files in a directory."""
    hashes = {}
    for file_path in scan_data_directory(data_dir):
        relative_path = file_path.relative_to(PROJECT_ROOT)
        hashes[str(relative_path)] = compute_file_hash(file_path)
    return hashes

def verify_integrity(state_file: Path, data_dir: Path) -> bool:
    """Verify the integrity of the data files."""
    state_data = load_hashes(state_file)
    if "artifact_hashes" not in state_data:
        return False
    
    for relative_path, expected_hash in state_data["artifact_hashes"].items():
        file_path = PROJECT_ROOT / relative_path
        if not file_path.exists():
            logger = get_logger("Integrity")
            logger.warning(f"File not found: {file_path}")
            return False
        
        actual_hash = compute_file_hash(file_path)
        if actual_hash != expected_hash:
            logger = get_logger("Integrity")
            logger.warning(f"Hash mismatch for {file_path}")
            return False
    
    return True

def main():
    """
    Main entry point for the integrity module.
    This is a placeholder for future functionality.
    """
    pass

if __name__ == "__main__":
    main()