"""
State Manager Module: Handles artifact checksum computation, registration,
and verification for the Constitution Principle III (Versioning & Integrity).

This module provides utilities to track artifact versions and ensure
data integrity via SHA-256 checksums.
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime

# Import project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_DIR = PROJECT_ROOT / "state"
CHECKSUMS_DIR = STATE_DIR / "checksums"
MANIFEST_PATH = STATE_DIR / "manifest.json"


def compute_sha256(file_path: Path) -> str:
    """
    Computes the SHA-256 checksum of a file.

    Args:
        file_path (Path): Path to the file.

    Returns:
        str: Hexadecimal string of the SHA-256 hash.

    Raises:
        FileNotFoundError: If the file does not exist.
        IOError: If the file cannot be read.
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    sha256_hash = hashlib.sha256()
    try:
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    except IOError as e:
        raise IOError(f"Error reading file {file_path}: {e}")


def initialize_state_structure() -> bool:
    """
    Ensures the state directory structure exists.
    This is a convenience wrapper that can be called before other operations.

    Returns:
        bool: True if successful, False otherwise.
    """
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        CHECKSUMS_DIR.mkdir(parents=True, exist_ok=True)
        if not MANIFEST_PATH.exists():
            initial_manifest = {
                "version": "1.0.0",
                "created_at": datetime.now().isoformat(),
                "artifacts": {}
            }
            with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
                json.dump(initial_manifest, f, indent=2)
        return True
    except Exception as e:
        print(f"Error initializing state structure: {e}", file=sys.stderr)
        return False


def _load_manifest() -> Dict[str, Any]:
    """
    Loads the manifest file.

    Returns:
        Dict[str, Any]: The manifest dictionary.
    """
    if not MANIFEST_PATH.exists():
        initialize_state_structure()
    
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def _save_manifest(manifest: Dict[str, Any]) -> None:
    """
    Saves the manifest file.

    Args:
        manifest (Dict[str, Any]): The manifest dictionary to save.
    """
    with open(MANIFEST_PATH, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)


def register_artifact(artifact_path: Path, task_id: str, description: str = "") -> bool:
    """
    Registers an artifact in the state manifest with its checksum and metadata.

    Args:
        artifact_path (Path): Path to the artifact file.
        task_id (str): The ID of the task that produced this artifact.
        description (str): Optional description of the artifact.

    Returns:
        bool: True if registration was successful, False otherwise.
    """
    if not artifact_path.exists():
        print(f"[ERROR] Cannot register non-existent artifact: {artifact_path}", file=sys.stderr)
        return False

    try:
        # Initialize state if needed
        initialize_state_structure()

        checksum = compute_sha256(artifact_path)
        manifest = _load_manifest()

        # Ensure artifacts key exists
        if "artifacts" not in manifest:
            manifest["artifacts"] = {}

        # Create artifact entry
        artifact_key = f"{task_id}_{artifact_path.name}"
        artifact_entry = {
            "path": str(artifact_path.relative_to(PROJECT_ROOT)),
            "checksum": checksum,
            "task_id": task_id,
            "description": description,
            "registered_at": datetime.now().isoformat(),
            "size_bytes": artifact_path.stat().st_size
        }

        manifest["artifacts"][artifact_key] = artifact_entry

        # Save updated manifest
        _save_manifest(manifest)

        # Also save a standalone checksum file for quick verification
        checksum_file = CHECKSUMS_DIR / f"{artifact_key}.sha256"
        with open(checksum_file, "w", encoding="utf-8") as f:
            f.write(f"{checksum}  {artifact_path.name}\n")

        print(f"[INFO] Artifact registered: {artifact_key} (SHA-256: {checksum[:16]}...)")
        return True

    except Exception as e:
        print(f"[ERROR] Failed to register artifact: {e}", file=sys.stderr)
        return False


def verify_artifact(artifact_path: Path, task_id: str) -> bool:
    """
    Verifies an artifact's checksum against the registered value.

    Args:
        artifact_path (Path): Path to the artifact file.
        task_id (str): The ID of the task that produced this artifact.

    Returns:
        bool: True if verification passes, False otherwise.
    """
    if not artifact_path.exists():
        print(f"[ERROR] Artifact not found for verification: {artifact_path}", file=sys.stderr)
        return False

    try:
        manifest = _load_manifest()
        artifact_key = f"{task_id}_{artifact_path.name}"

        if artifact_key not in manifest.get("artifacts", {}):
            print(f"[WARNING] Artifact not found in manifest: {artifact_key}", file=sys.stderr)
            return False

        registered_checksum = manifest["artifacts"][artifact_key]["checksum"]
        current_checksum = compute_sha256(artifact_path)

        if registered_checksum == current_checksum:
            print(f"[INFO] Verification PASSED for: {artifact_key}")
            return True
        else:
            print(f"[ERROR] Verification FAILED for: {artifact_key}", file=sys.stderr)
            print(f"  Expected: {registered_checksum}")
            print(f"  Actual:   {current_checksum}")
            return False

    except Exception as e:
        print(f"[ERROR] Error during verification: {e}", file=sys.stderr)
        return False


def list_artifacts_by_task(task_id: str) -> List[Dict[str, Any]]:
    """
    Lists all artifacts registered for a specific task.

    Args:
        task_id (str): The task ID.

    Returns:
        List[Dict[str, Any]]: List of artifact metadata dictionaries.
    """
    try:
        manifest = _load_manifest()
        artifacts = manifest.get("artifacts", {})
        return [
            info for key, info in artifacts.items()
            if info.get("task_id") == task_id
        ]
    except Exception as e:
        print(f"[ERROR] Failed to list artifacts: {e}", file=sys.stderr)
        return []


def get_state_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current state.

    Returns:
        Dict[str, Any]: Summary containing version, total artifacts, and recent activity.
    """
    try:
        manifest = _load_manifest()
        artifacts = manifest.get("artifacts", {})
        
        return {
            "version": manifest.get("version", "unknown"),
            "total_artifacts": len(artifacts),
            "tasks": list(set(a.get("task_id") for a in artifacts.values())),
            "manifest_path": str(MANIFEST_PATH)
        }
    except Exception as e:
        print(f"[ERROR] Failed to get state summary: {e}", file=sys.stderr)
        return {"error": str(e)}


if __name__ == "__main__":
    # Simple CLI for testing
    import argparse
    
    parser = argparse.ArgumentParser(description="State Manager CLI")
    parser.add_argument("command", choices=["init", "register", "verify", "list", "summary"])
    parser.add_argument("--path", help="Path to artifact file")
    parser.add_argument("--task", help="Task ID")
    parser.add_argument("--desc", help="Description for registration")
    
    args = parser.parse_args()
    
    if args.command == "init":
        if initialize_state_structure():
            print("State initialized.")
        else:
            print("State initialization failed.")
            sys.exit(1)
    
    elif args.command == "register":
        if not args.path or not args.task:
            print("Error: --path and --task are required for registration.")
            sys.exit(1)
        path = Path(args.path)
        if register_artifact(path, args.task, args.desc or ""):
            print("Artifact registered.")
        else:
            sys.exit(1)
    
    elif args.command == "verify":
        if not args.path or not args.task:
            print("Error: --path and --task are required for verification.")
            sys.exit(1)
        path = Path(args.path)
        if verify_artifact(path, args.task):
            print("Verification passed.")
        else:
            sys.exit(1)
    
    elif args.command == "list":
        if not args.task:
            print("Error: --task is required.")
            sys.exit(1)
        artifacts = list_artifacts_by_task(args.task)
        print(json.dumps(artifacts, indent=2))
    
    elif args.command == "summary":
        summary = get_state_summary()
        print(json.dumps(summary, indent=2))
