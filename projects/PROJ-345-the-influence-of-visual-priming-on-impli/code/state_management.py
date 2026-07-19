"""
State management module for Principle V (Versioning).
Handles initialization and management of state.yaml and project directory structures.
"""
import os
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

# Import config utilities
try:
    from config import get_path
except ImportError:
    # Fallback for direct execution or missing config
    def get_path(key: str) -> Path:
        base = Path.cwd()
        if key == "state":
            return base / "state"
        return base / key

logger = logging.getLogger(__name__)


def get_state_root() -> Path:
    """Get the root state directory."""
    return get_path("state")


def get_project_state_dir(project_id: str) -> Path:
    """Get the state directory for a specific project."""
    state_root = get_state_root()
    return state_root / "projects" / project_id


def init_state_file(project_id: str) -> Dict[str, Any]:
    """
    Initialize or load the state.yaml file for a project.
    Creates the directory structure and a default state file if it doesn't exist.

    Args:
        project_id: The project identifier (e.g., 'PROJ-345-the-influence-of-visual-priming-on-impli')

    Returns:
        The loaded state dictionary.
    """
    project_dir = get_project_state_dir(project_id)
    project_dir.mkdir(parents=True, exist_ok=True)

    state_file = project_dir / "state.yaml"

    if state_file.exists():
        logger.info(f"Loading existing state file: {state_file}")
        with open(state_file, 'r', encoding='utf-8') as f:
            state = yaml.safe_load(f) or {}
    else:
        logger.info(f"Creating new state file: {state_file}")
        state = {
            "project_id": project_id,
            "initialized_at": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "principle_v": {
                "status": "initialized",
                "description": "Versioning and state tracking for project lifecycle",
                "created_by": "T007_state_init"
            },
            "artifacts": [],
            "checksums": {},
            "execution_log": []
        }
        with open(state_file, 'w', encoding='utf-8') as f:
            yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    return state


def save_state_file(project_id: str, state: Dict[str, Any]) -> None:
    """
    Save the state dictionary to the state.yaml file.

    Args:
        project_id: The project identifier.
        state: The state dictionary to save.
    """
    project_dir = get_project_state_dir(project_id)
    state_file = project_dir / "state.yaml"

    with open(state_file, 'w', encoding='utf-8') as f:
        yaml.dump(state, f, default_flow_style=False, sort_keys=False)

    logger.info(f"State file saved: {state_file}")


def add_artifact_record(project_id: str, artifact_name: str, artifact_type: str, details: Optional[Dict[str, Any]] = None) -> None:
    """
    Add a record of a new artifact to the state file.

    Args:
        project_id: The project identifier.
        artifact_name: Name/Path of the artifact.
        artifact_type: Type of artifact (e.g., 'script', 'data', 'model', 'report').
        details: Optional additional metadata.
    """
    state = init_state_file(project_id)

    if "artifacts" not in state:
        state["artifacts"] = []

    record = {
        "name": artifact_name,
        "type": artifact_type,
        "timestamp": datetime.utcnow().isoformat(),
        "details": details or {}
    }
    state["artifacts"].append(record)

    save_state_file(project_id, state)
    logger.info(f"Artifact recorded: {artifact_name}")


def log_execution(project_id: str, task_id: str, status: str, message: str) -> None:
    """
    Log an execution event to the state file.

    Args:
        project_id: The project identifier.
        task_id: The task identifier that triggered the log.
        status: Execution status (e.g., 'success', 'failed', 'started').
        message: Log message.
    """
    state = init_state_file(project_id)

    if "execution_log" not in state:
        state["execution_log"] = []

    entry = {
        "task_id": task_id,
        "status": status,
        "timestamp": datetime.utcnow().isoformat(),
        "message": message
    }
    state["execution_log"].append(entry)

    save_state_file(project_id, state)


def main():
    """Main entry point for state initialization."""
    import sys

    # Default project ID from the task description
    project_id = "PROJ-345-the-influence-of-visual-priming-on-impli"

    if len(sys.argv) > 1:
        project_id = sys.argv[1]

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info(f"Initializing state for project: {project_id}")

    try:
        state = init_state_file(project_id)
        log_execution(project_id, "T007", "success", "State initialization completed")
        print(f"State initialized successfully at: {get_project_state_dir(project_id) / 'state.yaml'}")
        return 0
    except Exception as e:
        log_execution(project_id, "T007", "failed", str(e))
        logger.error(f"State initialization failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
