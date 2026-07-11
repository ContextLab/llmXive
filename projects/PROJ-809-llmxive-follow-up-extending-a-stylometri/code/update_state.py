"""
State management for the llmXive project.
Implements Constitution Principle V (artifact hashing and state updates).
"""
import os
import hashlib
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional, List

import yaml

# Project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
STATE_FILE = PROJECT_ROOT / "state" / "PROJ-809-llmxive-followup.yaml"


def load_state() -> Dict[str, Any]:
    """
    Load the state file. Creates it if it doesn't exist.
    """
    if STATE_FILE.exists():
        with open(STATE_FILE, 'r') as f:
            return yaml.safe_load(f)
    else:
        # Initialize new state
        state = {
            "project_id": "PROJ-809-llmxive-follow-up-extending-a-stylometri",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "tasks_completed": [],
            "checksums": {}
        }
        save_state(state)
        return state


def save_state(state: Dict[str, Any]) -> None:
    """
    Save the state file.
    """
    state["updated_at"] = datetime.now().isoformat()
    os.makedirs(STATE_FILE.parent, exist_ok=True)
    with open(STATE_FILE, 'w') as f:
        yaml.dump(state, f, default_flow_style=False)


def hash_artifact(file_path: str) -> str:
    """
    Compute SHA-256 hash of a file.
    """
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()


def register_artifact(state: Dict[str, Any], category: str, name: str, metadata: Dict[str, Any]) -> None:
    """
    Register an artifact in the state.
    """
    if "artifacts" not in state:
        state["artifacts"] = {}

    if category not in state["artifacts"]:
        state["artifacts"][category] = {}

    state["artifacts"][category][name] = {
        "metadata": metadata,
        "registered_at": datetime.now().isoformat()
    }


def update_artifact_hash(state: Dict[str, Any], category: str, name: str, checksum: str) -> None:
    """
    Update the checksum for an existing artifact.
    """
    if category in state["artifacts"] and name in state["artifacts"][category]:
        state["artifacts"][category][name]["metadata"]["checksum"] = checksum


def verify_artifact_integrity(file_path: str, expected_checksum: str) -> bool:
    """
    Verify the integrity of an artifact by comparing checksums.
    """
    actual_checksum = hash_artifact(file_path)
    return actual_checksum == expected_checksum


def get_artifact_metadata(state: Dict[str, Any], category: str, name: str) -> Optional[Dict[str, Any]]:
    """
    Get metadata for a specific artifact.
    """
    if category in state["artifacts"] and name in state["artifacts"][category]:
        return state["artifacts"][category][name]["metadata"]
    return None


def list_artifacts(state: Dict[str, Any], category: Optional[str] = None) -> List[str]:
    """
    List all registered artifacts, optionally filtered by category.
    """
    if category:
        if category in state["artifacts"]:
            return list(state["artifacts"][category].keys())
        return []
    else:
        all_artifacts = []
        for cat, items in state["artifacts"].items():
            for name in items:
                all_artifacts.append(f"{cat}/{name}")
        return all_artifacts


def main():
    """
    Main entry point for state module.
    """
    state = load_state()
    print(f"Current state: {state}")


if __name__ == "__main__":
    main()