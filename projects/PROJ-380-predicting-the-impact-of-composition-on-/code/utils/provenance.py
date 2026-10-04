"""
Provenance tracking module for llmXive pipeline.

Implements Constitution Principle V: Full checksum generation and state recording.
Provides functions to compute SHA-256 hashes of artifacts and record them
in a state YAML file for reproducibility and auditability.
"""
import hashlib
import os
import yaml
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from utils.config import get_paths


def ensure_state_directory() -> Path:
    """
    Ensure the state directory exists.
    
    Returns:
        Path to the state directory.
    """
    paths = get_paths()
    state_dir = paths.get("state_dir", Path("state"))
    state_dir.mkdir(parents=True, exist_ok=True)
    return state_dir


def get_provenance_state_file() -> Path:
    """
    Get the path to the main provenance state file.
    
    Returns:
        Path to the state YAML file.
    """
    state_dir = ensure_state_directory()
    return state_dir / "provenance.yaml"


def compute_file_checksum(file_path: str | Path) -> str:
    """
    Compute SHA-256 checksum of a file.
    
    Args:
        file_path: Path to the file to hash.
        
    Returns:
        Hexadecimal string of the SHA-256 hash.
        
    Raises:
        FileNotFoundError: If the file does not exist.
        ValueError: If the path is not a file.
    """
    file_path = Path(file_path)
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")
    if not file_path.is_file():
        raise ValueError(f"Path is not a file: {file_path}")
    
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    
    return sha256_hash.hexdigest()


def load_existing_state(state_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load existing provenance state from YAML file.
    
    Args:
        state_file: Optional path to state file. If None, uses default.
        
    Returns:
        Dictionary containing the state, or empty structure if file doesn't exist.
    """
    if state_file is None:
        state_file = get_provenance_state_file()
    
    if not state_file.exists():
        return {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": []
        }
    
    with open(state_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "artifacts": []
        }


def save_state(state: Dict[str, Any], state_file: Optional[Path] = None) -> None:
    """
    Save provenance state to YAML file.
    
    Args:
        state: Dictionary containing the state to save.
        state_file: Optional path to state file. If None, uses default.
    """
    if state_file is None:
        state_file = get_provenance_state_file()
    
    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def record_artifact(file_path: str | Path, state_file: Optional[Path] = None) -> Dict[str, Any]:
    """
    Record an artifact in the provenance state.
    
    Computes SHA-256 checksum and adds an entry to the state YAML file.
    
    Args:
        file_path: Path to the artifact file to record.
        state_file: Optional path to state file. If None, uses default.
        
    Returns:
        The artifact entry that was added to the state.
        
    Raises:
        FileNotFoundError: If the file does not exist.
    """
    file_path = Path(file_path)
    if state_file is None:
        state_file = get_provenance_state_file()
    
    # Load existing state
    state = load_existing_state(state_file)
    
    # Compute checksum
    checksum = compute_file_checksum(file_path)
    
    # Create artifact entry
    artifact_entry = {
        "path": str(file_path),
        "checksum": checksum,
        "algorithm": "sha256",
        "recorded_at": datetime.utcnow().isoformat(),
        "size_bytes": file_path.stat().st_size
    }
    
    # Add to artifacts list
    if "artifacts" not in state:
        state["artifacts"] = []
    
    # Check for duplicates and update if exists
    existing_idx = None
    for idx, art in enumerate(state["artifacts"]):
        if art.get("path") == str(file_path):
            existing_idx = idx
            break
    
    if existing_idx is not None:
        state["artifacts"][existing_idx] = artifact_entry
    else:
        state["artifacts"].append(artifact_entry)
    
    # Update creation timestamp if this is the first entry
    if len(state["artifacts"]) == 1 and "created_at" not in state:
        state["created_at"] = artifact_entry["recorded_at"]
    
    # Save updated state
    save_state(state, state_file)
    
    return artifact_entry


def verify_artifact(file_path: str | Path, state_file: Optional[Path] = None) -> bool:
    """
    Verify an artifact's checksum against the recorded state.
    
    Args:
        file_path: Path to the artifact file to verify.
        state_file: Optional path to state file. If None, uses default.
        
    Returns:
        True if checksum matches, False otherwise.
        
    Raises:
        FileNotFoundError: If the file or state file does not exist.
    """
    file_path = Path(file_path)
    if state_file is None:
        state_file = get_provenance_state_file()
    
    if not state_file.exists():
        raise FileNotFoundError(f"State file not found: {state_file}")
    
    state = load_existing_state(state_file)
    current_checksum = compute_file_checksum(file_path)
    
    for artifact in state.get("artifacts", []):
        if artifact.get("path") == str(file_path):
            recorded_checksum = artifact.get("checksum")
            return current_checksum == recorded_checksum
    
    # File not found in state
    return False


def list_artifacts(state_file: Optional[Path] = None) -> List[Dict[str, Any]]:
    """
    List all recorded artifacts from the state file.
    
    Args:
        state_file: Optional path to state file. If None, uses default.
        
    Returns:
        List of artifact entries.
    """
    if state_file is None:
        state_file = get_provenance_state_file()
    
    if not state_file.exists():
        return []
    
    state = load_existing_state(state_file)
    return state.get("artifacts", [])


def main() -> None:
    """
    Command-line interface for provenance operations.
    
    Usage examples:
        python -m utils.provenance record path/to/file.txt
        python -m utils.provenance verify path/to/file.txt
        python -m utils.provenance list
    """
    import sys
    import argparse
    
    parser = argparse.ArgumentParser(description="Provenance tracking CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Record command
    record_parser = subparsers.add_parser("record", help="Record an artifact")
    record_parser.add_argument("file_path", help="Path to the file to record")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify an artifact")
    verify_parser.add_argument("file_path", help="Path to the file to verify")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all recorded artifacts")
    
    args = parser.parse_args()
    
    if args.command == "record":
        try:
            entry = record_artifact(args.file_path)
            print(f"Recorded: {entry['path']}")
            print(f"Checksum: {entry['checksum']}")
            print(f"Size: {entry['size_bytes']} bytes")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "verify":
        try:
            is_valid = verify_artifact(args.file_path)
            if is_valid:
                print(f"Verification PASSED: {args.file_path}")
            else:
                print(f"Verification FAILED: {args.file_path}")
                sys.exit(1)
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            sys.exit(1)
    
    elif args.command == "list":
        artifacts = list_artifacts()
        if not artifacts:
            print("No artifacts recorded.")
        else:
            print(f"Recorded artifacts ({len(artifacts)}):")
            for art in artifacts:
                print(f"  - {art['path']} ({art['checksum'][:16]}...)")
    
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()