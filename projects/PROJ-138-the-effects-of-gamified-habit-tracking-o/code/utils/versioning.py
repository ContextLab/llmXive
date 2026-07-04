"""
Versioning utilities for the llmXive automated science pipeline.

This module handles artifact hashing and state tracking to ensure
reproducibility and integrity of the research pipeline.
"""
import hashlib
import yaml
import os
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

# Ensure project root is in path for imports if running from submodules
_project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if _project_root not in os.environ.get('PYTHONPATH', '').split(os.pathsep):
    os.environ['PYTHONPATH'] = f"{_project_root}" + os.pathsep + os.environ.get('PYTHONPATH', '')

STATE_FILE = os.path.join(_project_root, "state.yaml")


def calculate_sha256(file_path: str) -> str:
    """
    Calculate the SHA-256 hash of a file.
    
    Args:
        file_path: Path to the file to hash
        
    Returns:
        str: Hexadecimal SHA-256 hash string
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def load_state() -> Dict:
    """
    Load the current state from the state.yaml file.
    
    Returns:
        dict: Current state dictionary, or empty dict if file doesn't exist.
    """
    if not os.path.exists(STATE_FILE):
        return {"artifacts": {}, "last_updated": None}
    
    with open(STATE_FILE, "r") as f:
        try:
            return yaml.safe_load(f) or {"artifacts": {}, "last_updated": None}
        except yaml.YAMLError:
            return {"artifacts": {}, "last_updated": None}


def save_state(state: Dict) -> None:
    """
    Save the state dictionary to the state.yaml file.
    
    Args:
        state: The state dictionary to save
    """
    with open(STATE_FILE, "w") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)


def update_artifact_state(artifact_path: str, state: Dict) -> None:
    """
    Update the state for a specific artifact.
    
    Args:
        artifact_path: Relative path to the artifact
        state: The full state dictionary to update
    """
    abs_path = os.path.abspath(artifact_path)
    if not os.path.exists(abs_path):
        raise FileNotFoundError(f"Artifact not found: {abs_path}")
    
    rel_path = os.path.relpath(abs_path, _project_root)
    hash_val = calculate_sha256(abs_path)
    
    state["artifacts"][rel_path] = {
        "hash": hash_val,
        "updated_at": datetime.now().isoformat()
    }
    state["last_updated"] = datetime.now().isoformat()
    
    save_state(state)


def verify_artifacts(artifact_paths: List[str]) -> bool:
    """
    Verify the integrity of a list of artifacts against the stored state.
    
    Args:
        artifact_paths: List of relative paths to verify
        
    Returns:
        bool: True if all artifacts match their stored hashes, False otherwise.
    """
    state = load_state()
    all_valid = True
    
    for rel_path in artifact_paths:
        abs_path = os.path.abspath(os.path.join(_project_root, rel_path))
        
        if not os.path.exists(abs_path):
            print(f"[WARN] Artifact missing: {rel_path}")
            all_valid = False
            continue
        
        current_hash = calculate_sha256(abs_path)
        stored_hash = state.get("artifacts", {}).get(rel_path, {}).get("hash")
        
        if stored_hash is None:
            print(f"[WARN] No stored hash for: {rel_path}")
            # We don't fail on missing hash, just warn
        elif current_hash != stored_hash:
            print(f"[ERROR] Hash mismatch for: {rel_path}")
            print(f"  Stored: {stored_hash}")
            print(f"  Current: {current_hash}")
            all_valid = False
        else:
            print(f"[OK] Verified: {rel_path}")
    
    return all_valid


def main():
    """
    CLI entry point for versioning operations.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage artifact versioning")
    subparsers = parser.add_subparsers(dest="command", help="Command to run")
    
    # Update command
    update_parser = subparsers.add_parser("update", help="Update state for specific artifacts")
    update_parser.add_argument("paths", nargs="+", help="Paths to artifacts to update")
    
    # Verify command
    verify_parser = subparsers.add_parser("verify", help="Verify artifact integrity")
    verify_parser.add_argument("paths", nargs="+", help="Paths to artifacts to verify")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List current state")
    
    args = parser.parse_args()
    
    if args.command == "update":
        state = load_state()
        for path in args.paths:
            try:
                update_artifact_state(path, state)
            except FileNotFoundError as e:
                print(f"[ERROR] {e}")
        print(f"State updated. File: {STATE_FILE}")
        
    elif args.command == "verify":
        if verify_artifacts(args.paths):
            print("All verified artifacts are valid.")
        else:
            print("Some artifacts failed verification.")
            
    elif args.command == "list":
        state = load_state()
        print(f"Last updated: {state.get('last_updated', 'Never')}")
        print(f"Artifacts ({len(state.get('artifacts', {}))}):")
        for path, info in state.get("artifacts", {}).items():
            print(f"  - {path}: {info.get('hash', 'N/A')[:16]}...")
            
    else:
        parser.print_help()


if __name__ == "__main__":
    main()