import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.config import get_paths, ensure_directories
from utils.logging_config import get_logger

logger = get_logger(__name__)

def ensure_state_directory() -> Path:
    """Ensures the state directory exists and returns its path."""
    paths = get_paths()
    ensure_directories(paths)
    return paths["state"]

def get_provenance_state_file() -> Path:
    """Returns the path to the main provenance state YAML file."""
    state_dir = ensure_state_directory()
    return state_dir / "provenance.yaml"

def compute_file_checksum(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def load_existing_state() -> Dict[str, Any]:
    """
    Loads the existing provenance state if it exists, otherwise returns an empty structure.
    
    Returns:
        Dictionary containing the state data.
    """
    state_file = get_provenance_state_file()
    if state_file.exists():
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                return yaml.safe_load(f) or {"artifacts": []}
        except Exception as e:
            logger.warning(f"Could not load existing state file: {e}. Starting fresh.")
    return {"artifacts": []}

def save_state(state: Dict[str, Any]) -> None:
    """
    Saves the state dictionary to the provenance YAML file.
    
    Args:
        state: The state dictionary to save.
    """
    state_file = get_provenance_state_file()
    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)
    logger.info(f"Provenance state saved to {state_file}")

def record_artifact(file_path: Path, state_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Records an artifact in the provenance state.
    
    Args:
        file_path: Path to the artifact file.
        state_file: Optional path to the state file (uses default if None).
        
    Returns:
        The recorded artifact entry.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"Artifact file not found: {file_path}")

    if state_file is None:
        state_file = get_provenance_state_file()

    state = load_existing_state()
    
    checksum = compute_file_checksum(file_path)
    entry = {
        "path": str(file_path),
        "checksum": checksum,
        "timestamp": datetime.now().isoformat(),
        "type": "generated" # Default type, could be extended
    }

    # Check if already recorded to avoid duplicates
    found = False
    for i, existing in enumerate(state["artifacts"]):
        if existing["path"] == str(file_path):
            state["artifacts"][i] = entry
            found = True
            break
    
    if not found:
        state["artifacts"].append(entry)

    save_state(state)
    logger.info(f"Recorded artifact: {file_path} (SHA-256: {checksum})")
    return entry

def verify_artifact(file_path: Path) -> bool:
    """
    Verifies an artifact's checksum against the recorded state.
    
    Args:
        file_path: Path to the artifact file.
        
    Returns:
        True if checksum matches, False otherwise.
    """
    file_path = Path(file_path)
    state = load_existing_state()
    
    current_checksum = compute_file_checksum(file_path)
    
    for entry in state["artifacts"]:
        if entry["path"] == str(file_path):
            if entry["checksum"] == current_checksum:
                logger.info(f"Verification passed for {file_path}")
                return True
            else:
                logger.warning(f"Verification FAILED for {file_path}. Checksum mismatch.")
                return False
    
    logger.warning(f"No record found for {file_path} in provenance state.")
    return False

def list_artifacts() -> List[Dict[str, Any]]:
    """
    Lists all recorded artifacts.
    
    Returns:
        List of artifact entries.
    """
    state = load_existing_state()
    return state.get("artifacts", [])

def main():
    """CLI entry point for provenance utilities."""
    import argparse
    parser = argparse.ArgumentParser(description="Provenance Management")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Record command
    record_parser = subparsers.add_parser("record", help="Record an artifact")
    record_parser.add_argument("file", type=Path, help="Path to the file to record")

    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify an artifact")
    verify_parser.add_argument("file", type=Path, help="Path to the file to verify")

    # List command
    subparsers.add_parser("list", help="List all artifacts")

    args = parser.parse_args()

    if args.command == "record":
        try:
            record_artifact(args.file)
        except FileNotFoundError as e:
            print(f"Error: {e}")
    elif args.command == "verify":
        result = verify_artifact(args.file)
        print(f"Verification result: {'PASS' if result else 'FAIL'}")
    elif args.command == "list":
        artifacts = list_artifacts()
        for art in artifacts:
            print(f"{art['path']}: {art['checksum']}")
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
