"""
State Management Utility for llmXive Pipeline.

Implements Constitution Principle III: YAML-based Single Source of Truth.
Handles artifact versioning, hash tracking, and pipeline state management
using YAML files instead of SQLite.

This module replaces the previous SQLite-based approach to ensure:
1. Human-readable state files
2. Git-friendly diffing
3. No database dependencies
4. Transparent artifact tracking
"""

import hashlib
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

# Import from local config module
try:
    from utils.config import get_project_root, get_state_dir
except ImportError:
    # Fallback for direct execution
    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from utils.config import get_project_root, get_state_dir


def calculate_file_hash(file_path: Path, algorithm: str = "sha256") -> str:
    """
    Calculate the hash of a file for integrity verification.

    Args:
        file_path: Path to the file to hash
        algorithm: Hash algorithm to use (default: sha256)

    Returns:
        Hexadecimal hash string
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found for hashing: {file_path}")

    hash_obj = hashlib.new(algorithm)
    with open(file_path, "rb") as f:
        # Read in chunks to handle large files
        for chunk in iter(lambda: f.read(8192), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest()


def get_file_metadata(file_path: Path) -> Dict[str, Any]:
    """
    Extract metadata from a file for state tracking.

    Args:
        file_path: Path to the file

    Returns:
        Dictionary containing file metadata
    """
    if not file_path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    stat = file_path.stat()
    return {
        "path": str(file_path.relative_to(get_project_root())),
        "size_bytes": stat.st_size,
        "modified_at": datetime.fromtimestamp(stat.st_mtime).isoformat(),
        "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat(),
        "hash_sha256": calculate_file_hash(file_path),
    }


def load_yaml_state(state_file: Path) -> Dict[str, Any]:
    """
    Load state from a YAML file.

    Args:
        state_file: Path to the YAML state file

    Returns:
        Dictionary containing the state
    """
    # Lazy import yaml to avoid hard dependency if not needed
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for state management. "
            "Install with: pip install pyyaml"
        )

    if not state_file.exists():
        return {
            "version": "1.0",
            "project_id": "PROJ-361-investigating-the-relationship-between-b",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "pipeline_state": {
                "current_phase": "foundational",
                "completed_tasks": [],
                "failed_tasks": [],
                "pending_tasks": [],
            },
        }

    with open(state_file, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def save_yaml_state(state_file: Path, state: Dict[str, Any]) -> None:
    """
    Save state to a YAML file.

    Args:
        state_file: Path to the YAML state file
        state: State dictionary to save
    """
    try:
        import yaml
    except ImportError:
        raise ImportError(
            "PyYAML is required for state management. "
            "Install with: pip install pyyaml"
        )

    # Update timestamp
    state["updated_at"] = datetime.now().isoformat()

    # Ensure directory exists
    state_file.parent.mkdir(parents=True, exist_ok=True)

    with open(state_file, "w", encoding="utf-8") as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False, allow_unicode=True)


def get_state_file_path() -> Path:
    """
    Get the path to the project state YAML file.

    Returns:
        Path to the state file
    """
    state_dir = get_state_dir()
    project_root = get_project_root()
    project_id = project_root.name.replace(" ", "-").lower()
    return state_dir / f"{project_id}.yaml"


def register_artifact(
    file_path: Path,
    artifact_type: str,
    task_id: str,
    status: str = "completed",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Register a new artifact in the state file.

    Args:
        file_path: Path to the artifact file
        artifact_type: Type of artifact (e.g., 'code', 'data', 'figure', 'report')
        task_id: ID of the task that produced this artifact
        status: Status of the artifact ('pending', 'completed', 'failed')
        metadata: Optional additional metadata

    Returns:
        The updated artifact record
    """
    state_file = get_state_file_path()
    state = load_yaml_state(state_file)

    file_path = Path(file_path).resolve()
    relative_path = str(file_path.relative_to(get_project_root()))

    artifact_key = f"{task_id}:{artifact_type}:{relative_path}"

    # Calculate hash and metadata
    file_metadata = get_file_metadata(file_path)

    artifact_record = {
        "type": artifact_type,
        "task_id": task_id,
        "path": relative_path,
        "status": status,
        "hash_sha256": file_metadata["hash_sha256"],
        "size_bytes": file_metadata["size_bytes"],
        "created_at": datetime.now().isoformat(),
        "metadata": metadata or {},
    }

    state["artifacts"][artifact_key] = artifact_record
    save_yaml_state(state_file, state)

    return artifact_record


def update_artifact_status(
    file_path: Path,
    task_id: str,
    new_status: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Update the status of an existing artifact.

    Args:
        file_path: Path to the artifact file
        task_id: ID of the task associated with this artifact
        new_status: New status ('pending', 'completed', 'failed')
        notes: Optional notes about the status change

    Returns:
        Updated artifact record
    """
    state_file = get_state_file_path()
    state = load_yaml_state(state_file)

    # Find the artifact
    relative_path = str(Path(file_path).resolve().relative_to(get_project_root()))
    artifact_key = f"{task_id}:*:{relative_path}"

    found_key = None
    for key in state["artifacts"]:
        if key.startswith(f"{task_id}:") and relative_path in key:
            found_key = key
            break

    if not found_key:
        raise ValueError(f"Artifact not found: {task_id} -> {relative_path}")

    # Update the record
    artifact = state["artifacts"][found_key]
    artifact["status"] = new_status
    artifact["updated_at"] = datetime.now().isoformat()

    if notes:
        if "notes" not in artifact:
            artifact["notes"] = []
        artifact["notes"].append({
            "timestamp": datetime.now().isoformat(),
            "note": notes,
        })

    # Re-calculate hash if file still exists
    if Path(file_path).exists():
        artifact["hash_sha256"] = calculate_file_hash(Path(file_path))
        artifact["size_bytes"] = Path(file_path).stat().st_size

    save_yaml_state(state_file, state)

    return artifact


def verify_artifact_integrity(file_path: Path, task_id: str) -> bool:
    """
    Verify that an artifact's current hash matches the stored hash.

    Args:
        file_path: Path to the artifact file
        task_id: ID of the task associated with this artifact

    Returns:
        True if integrity check passes, False otherwise
    """
    state_file = get_state_file_path()
    state = load_yaml_state(state_file)

    relative_path = str(Path(file_path).resolve().relative_to(get_project_root()))

    # Find the artifact
    found_key = None
    for key in state["artifacts"]:
        if key.startswith(f"{task_id}:") and relative_path in key:
            found_key = key
            break

    if not found_key:
        raise ValueError(f"Artifact not found in state: {task_id} -> {relative_path}")

    stored_hash = state["artifacts"][found_key]["hash_sha256"]
    current_hash = calculate_file_hash(Path(file_path))

    if stored_hash != current_hash:
        print(
            f"⚠️  Integrity check failed for {relative_path}: "
            f"stored={stored_hash[:16]}..., current={current_hash[:16]}..."
        )
        return False

    return True


def get_pipeline_state() -> Dict[str, Any]:
    """
    Get the current pipeline state from the state file.

    Returns:
        Dictionary containing pipeline state information
    """
    state_file = get_state_file_path()
    state = load_yaml_state(state_file)
    return state.get("pipeline_state", {})


def update_pipeline_state(
    phase: Optional[str] = None,
    completed_tasks: Optional[List[str]] = None,
    failed_tasks: Optional[List[str]] = None,
    pending_tasks: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """
    Update the pipeline state in the state file.

    Args:
        phase: Current phase name
        completed_tasks: List of completed task IDs
        failed_tasks: List of failed task IDs
        pending_tasks: List of pending task IDs

    Returns:
        Updated pipeline state
    """
    state_file = get_state_file_path()
    state = load_yaml_state(state_file)

    if "pipeline_state" not in state:
        state["pipeline_state"] = {
            "current_phase": "initializing",
            "completed_tasks": [],
            "failed_tasks": [],
            "pending_tasks": [],
        }

    if phase is not None:
        state["pipeline_state"]["current_phase"] = phase
    if completed_tasks is not None:
        state["pipeline_state"]["completed_tasks"] = completed_tasks
    if failed_tasks is not None:
        state["pipeline_state"]["failed_tasks"] = failed_tasks
    if pending_tasks is not None:
        state["pipeline_state"]["pending_tasks"] = pending_tasks

    save_yaml_state(state_file, state)

    return state["pipeline_state"]


def initialize_project_state() -> Dict[str, Any]:
    """
    Initialize a new project state file if it doesn't exist.

    Returns:
        The initialized state dictionary
    """
    state_file = get_state_file_path()

    if not state_file.exists():
        state = {
            "version": "1.0",
            "project_id": "PROJ-361-investigating-the-relationship-between-b",
            "title": "Investigating the Relationship Between Brain Network Topology and Susceptibility to Visual Illusions",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "artifacts": {},
            "pipeline_state": {
                "current_phase": "setup",
                "completed_tasks": ["T001a", "T001b", "T001c", "T002", "T003", "T005"],
                "failed_tasks": [],
                "pending_tasks": [
                    "T006", "T007", "T008", "T009",
                    "T010", "T011", "T012", "T013", "T014", "T015", "T016", "T017",
                    "T018", "T019", "T020", "T021", "T022", "T023", "T024", "T026",
                    "T044", "T045", "T046",
                    "T052", "T053", "T054", "T055", "T056", "T057", "T058", "T059",
                    "T060", "T061", "T062", "T063", "T064", "T065", "T066", "T067", "T068", "T069"
                ],
            },
        }
        save_yaml_state(state_file, state)
        print(f"Initialized project state at: {state_file}")
    else:
        state = load_yaml_state(state_file)
        print(f"Loaded existing project state from: {state_file}")

    return state


def main():
    """
    Main entry point for command-line usage.

    Usage:
        python -m utils.update_state init          # Initialize state file
        python -m utils.update_state register <file_path> <type> <task_id>  # Register artifact
        python -m utils.update_state verify <file_path> <task_id>           # Verify integrity
        python -m utils.update_state status                               # Show pipeline status
    """
    if len(sys.argv) < 2:
        print("Usage: python -m utils.update_state <command> [args...]")
        print("Commands:")
        print("  init                                    - Initialize project state")
        print("  register <file> <type> <task_id>        - Register an artifact")
        print("  verify <file> <task_id>                 - Verify artifact integrity")
        print("  status                                  - Show pipeline status")
        print("  update-phase <phase>                    - Update current phase")
        sys.exit(1)

    command = sys.argv[1]

    if command == "init":
        state = initialize_project_state()
        print(f"State initialized. Phase: {state['pipeline_state']['current_phase']}")

    elif command == "register":
        if len(sys.argv) < 5:
            print("Usage: register <file_path> <artifact_type> <task_id>")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        artifact_type = sys.argv[3]
        task_id = sys.argv[4]

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        try:
            artifact = register_artifact(file_path, artifact_type, task_id)
            print(f"Registered artifact: {artifact['path']} (hash: {artifact['hash_sha256'][:16]}...)")
        except Exception as e:
            print(f"Error registering artifact: {e}")
            sys.exit(1)

    elif command == "verify":
        if len(sys.argv) < 4:
            print("Usage: verify <file_path> <task_id>")
            sys.exit(1)
        file_path = Path(sys.argv[2])
        task_id = sys.argv[3]

        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            sys.exit(1)

        try:
            if verify_artifact_integrity(file_path, task_id):
                print(f"✓ Integrity verified for: {file_path}")
            else:
                print(f"✗ Integrity check FAILED for: {file_path}")
                sys.exit(1)
        except Exception as e:
            print(f"Error verifying artifact: {e}")
            sys.exit(1)

    elif command == "status":
        state = get_pipeline_state()
        print(f"Current Phase: {state.get('current_phase', 'unknown')}")
        print(f"Completed Tasks: {len(state.get('completed_tasks', []))}")
        print(f"Failed Tasks: {len(state.get('failed_tasks', []))}")
        print(f"Pending Tasks: {len(state.get('pending_tasks', []))}")

    elif command == "update-phase":
        if len(sys.argv) < 3:
            print("Usage: update-phase <phase_name>")
            sys.exit(1)
        phase = sys.argv[2]
        update_pipeline_state(phase=phase)
        print(f"Updated phase to: {phase}")

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()